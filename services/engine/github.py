"""GitHub reads for the engine — lifted with attribution.

Derived from MejorQueNada/bounty-agent `services/scout.py` (MIT, our own
lineage, battle-tested unattended since 2026-08). Adapted: user-agent,
contest detail includes PR age, and an issue-thread read for responder
signal. All reads are read-only; every response is disk-cached with TTLs so
runs stay inside rate limits.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CACHE_TTL = 3600
GITHUB_STATE_CACHE_TTL = 6 * 3600
PR_SEARCH_CACHE_TTL = 6 * 3600
UA = "satoshis-most-wanted/0.1 (+https://github.com/Bertofortheppl/satoshis-most-wanted)"


def http_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class GhCache:
    """Minimal disk cache for GitHub API responses with per-key TTL."""

    def __init__(self, cache_dir: Path, ttl=DEFAULT_CACHE_TTL, token="", fresh=False):
        self.path = cache_dir / "gh_cache.json"
        self.ttl = ttl
        self.token = token
        self.data = {}
        if fresh:
            try:
                self.path.unlink()
            except OSError:
                pass
        elif self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception:
                self.data = {}

    def get(self, key, ttl=None):
        ttl = ttl or self.ttl
        hit = self.data.get(key)
        if not hit:
            return None
        if time.time() - hit.get("ts", 0) > ttl:
            return None
        return hit["value"]

    def put(self, key, value):
        self.data[key] = {"ts": time.time(), "value": value}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data))
        tmp.replace(self.path)

    def gh(self, url, ttl=None):
        cached = self.get(url, ttl)
        if cached is not None:
            return cached
        headers = {"User-Agent": UA}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self.put(url, data)
        time.sleep(0.6)
        return data


def gh_repo_info(gh, full_name):
    return gh.gh(f"https://api.github.com/repos/{full_name}")


def gh_user_info(gh, username):
    return gh.gh(f"https://api.github.com/users/{username}")


def gh_repo_archived(gh, full_name):
    key = f"gh:repo-archived:{full_name}"
    cached = gh.get(key)
    if cached is not None:
        return cached
    try:
        r = gh_repo_info(gh, full_name)
        archived = bool(r.get("archived")) if isinstance(r, dict) else False
    except Exception:
        archived = False
    gh.put(key, archived)
    return archived


def repo_health(gh, full_name):
    """last push ISO date + archived flag, one cached read."""
    key = f"gh:repo-health:{full_name}"
    cached = gh.get(key)
    if cached is not None:
        return cached
    try:
        r = gh_repo_info(gh, full_name)
        out = {
            "archived": bool(r.get("archived")),
            "last_push": (r.get("pushed_at") or "")[:10] or None,
            "stars": r.get("stargazers_count") or 0,
        }
    except Exception:
        out = {"archived": False, "last_push": None, "stars": 0}
    gh.put(key, out)
    return out


def find_open_prs(gh, repo, issue_number):
    """Open PRs in `repo` referencing the issue (contest detection).

    Search is advisory (mention-based, under-counts PRs that never cite the
    issue number — documented upstream limitation). One cached search per
    issue; PR age comes from search result `created_at`.
    """
    key = f"gh:prs:{repo}#{issue_number}"
    cached = gh.get(key, PR_SEARCH_CACHE_TTL)
    if cached is not None:
        return cached
    q = urllib.parse.quote(f"repo:{repo} is:pr is:open {issue_number}")
    url = f"https://api.github.com/search/issues?q={q}&per_page=20"
    try:
        d = gh.gh(url, PR_SEARCH_CACHE_TTL)
        now = time.time()
        items = []
        for i in (d.get("items") or []):
            created = i.get("created_at") or ""
            try:
                age_days = max(0, int((now - time.mktime(time.strptime(created[:10], "%Y-%m-%d"))) / 86400))
            except Exception:
                age_days = None
            items.append({
                "number": i["number"],
                "title": (i.get("title") or "")[:80],
                "user": (i.get("user") or {}).get("login", "?"),
                "age_days": age_days,
            })
    except Exception:
        items = []
    gh.put(key, items)
    return items


def dead_attempts(gh, repo, issue_number):
    """Attempt history for an issue: closed-unmerged (dead) and merged PRs.

    One cached search (is:closed includes merged PRs; `merged_at` in the
    search result distinguishes them). Battle scars (DECISIONS.md D7):
    dead attempts = rejected work; merged attempts = the purse is likely
    already claimed while the listing may still show open.
    """
    key = f"gh:dead:{repo}#{issue_number}"
    cached = gh.get(key, PR_SEARCH_CACHE_TTL)
    if cached is not None:
        return cached
    q = urllib.parse.quote(f"repo:{repo} is:pr is:closed {issue_number}")
    url = f"https://api.github.com/search/issues?q={q}&per_page=20"
    out = {"dead": 0, "merged": 0}
    try:
        d = gh.gh(url, PR_SEARCH_CACHE_TTL)
        for i in (d.get("items") or []):
            pr = i.get("pull_request") or {}
            if pr.get("merged_at"):
                out["merged"] += 1
            else:
                out["dead"] += 1
    except Exception:
        pass
    gh.put(key, out)
    return out


def issue_thread(gh, repo, issue_number):
    """Responder signal for an issue: non-reporter replies (cached 6h).

    HONEST LIMITATION: a non-reporter reply is a *responder* signal, not
    proof the person is a maintainer. Collab status is not exposed by the
    REST API without per-repo permission checks. The strict bar (bar.py)
    treats it as a proxy and the poster says "responded", not "maintainer
    approved".
    """
    key = f"gh:thread:{repo}#{issue_number}"
    cached = gh.get(key, GITHUB_STATE_CACHE_TTL)
    if cached is not None:
        return cached
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments?per_page=50"
    try:
        d = gh.gh(url, GITHUB_STATE_CACHE_TTL)
        now = time.time()
        last_age = None
        replies = 0
        reporter = None
        iss = gh.gh(f"https://api.github.com/repos/{repo}/issues/{issue_number}")
        reporter = ((iss.get("user") or {}).get("login") or "").lower()
        for c in d if isinstance(d, list) else []:
            who = ((c.get("user") or {}).get("login") or "").lower()
            if who and who != reporter:
                replies += 1
                created = c.get("created_at") or ""
                try:
                    age = max(0, int((now - time.mktime(time.strptime(created[:10], "%Y-%m-%d"))) / 86400))
                    last_age = age if last_age is None else min(last_age, age)
                except Exception:
                    pass
        out = {"replies": replies, "last_reply_age_days": last_age}
    except Exception:
        out = {"replies": 0, "last_reply_age_days": None}
    gh.put(key, out)
    return out


def rate_rewarder(gh, username):
    """Heuristic trust flag for the account that funded a bounty."""
    if not username:
        return "unknown"
    key = f"gh:rewarder:{username}"
    cached = gh.get(key, 24 * 3600)
    if cached is not None:
        return cached
    try:
        u = gh_user_info(gh, username)
    except Exception:
        return "unknown"
    if isinstance(u, dict) and u.get("message"):
        return "unknown"
    created = u.get("created_at", "")
    followers = u.get("followers") or 0
    repos = (u.get("public_repos") or 0) + (u.get("public_gists") or 0)
    try:
        import datetime as dt
        age_days = (dt.date.today() - dt.date.fromisoformat(created[:10])).days
    except Exception:
        age_days = 9999
    flag = "low-trust" if (followers == 0 and age_days < 180 and repos < 3) else "ok"
    gh.put(key, flag)
    return flag


def language_of(gh, full_name, hints=None):
    hints = hints or {}
    if full_name in hints:
        return hints[full_name], "known"
    try:
        r = gh_repo_info(gh, full_name)
        lang = r.get("language") if isinstance(r, dict) else None
        return (lang.lower() if lang else "unknown"), "github"
    except Exception:
        return "unknown", "error"
