"""Source adapters — one per platform, all emitting Posters.

Adapters are dumb fetchers: platform → Poster, nothing else. All judgment
(enrichment, trap verdicts, the wall bar) happens later in the pipeline, so
adding a source can never change the rules.
"""
