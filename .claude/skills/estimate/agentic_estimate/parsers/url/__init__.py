"""URL parsing module for GitHub and web content."""

from .url_parser_github_api import GitHubURLParser
from .url_parser_web_fetch import WebURLParser

__all__ = ["GitHubURLParser", "WebURLParser"]
