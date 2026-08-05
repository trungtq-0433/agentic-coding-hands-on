"""Kensan collection + dedup helpers.

Stdlib-only modules (watchlist, normalize) are import-safe without third-party
deps. The collector modules import feedparser/requests lazily inside each function
so importing the package never fails when deps are absent.
"""
