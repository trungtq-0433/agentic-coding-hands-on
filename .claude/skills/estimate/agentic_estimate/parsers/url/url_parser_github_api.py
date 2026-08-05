"""GitHub URL parser using gh CLI API.

Parses GitHub issues and discussions via `gh api` command.
"""

import json
import re
import subprocess

from ..parser_base_classes_and_data_models import (
    BaseParser,
    ParsedDocument,
    ParseFailedError,
)


class GitHubURLParser(BaseParser):
    """Parser for GitHub issues and discussions using gh CLI."""

    # URL patterns
    ISSUE_PATTERN = re.compile(r"(?:https?://)?github\.com/([^/]+)/([^/]+)/issues/(\d+)")
    DISCUSSION_PATTERN = re.compile(r"(?:https?://)?github\.com/([^/]+)/([^/]+)/discussions/(\d+)")
    PR_PATTERN = re.compile(r"(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)")

    def supports(self, source: str) -> bool:
        """Check if source is a GitHub issue, discussion, or PR URL."""
        return bool(
            self.ISSUE_PATTERN.match(source)
            or self.DISCUSSION_PATTERN.match(source)
            or self.PR_PATTERN.match(source)
        )

    def parse(self, source: str) -> ParsedDocument:
        """Parse GitHub URL and return structured content."""
        # Check gh CLI availability
        if not self._check_gh_cli():
            raise ParseFailedError(
                "GitHub CLI (gh) not installed or not authenticated. "
                "Install: https://cli.github.com/ and run: gh auth login",
                source,
            )

        # Determine URL type and parse
        if match := self.ISSUE_PATTERN.match(source):
            return self._parse_issue(source, *match.groups())
        elif match := self.DISCUSSION_PATTERN.match(source):
            return self._parse_discussion(source, *match.groups())
        elif match := self.PR_PATTERN.match(source):
            return self._parse_pull_request(source, *match.groups())
        else:
            raise ParseFailedError("URL pattern not recognized", source)

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _run_gh_api(self, endpoint: str) -> dict:
        """Run gh api command and return JSON response."""
        try:
            result = subprocess.run(
                ["gh", "api", endpoint],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise ParseFailedError(
                    f"gh api failed: {result.stderr}",
                    endpoint,
                )
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise ParseFailedError("gh api request timed out", endpoint)
        except json.JSONDecodeError as e:
            raise ParseFailedError(f"Invalid JSON response: {e}", endpoint)

    def _run_gh_graphql(self, query: str, variables: dict) -> dict:
        """Run gh api graphql command."""
        try:
            cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
            for key, value in variables.items():
                # Use -F for non-string types (int, bool, etc.), -f for strings
                if isinstance(value, (int, float, bool)):
                    cmd.extend(["-F", f"{key}={value}"])
                else:
                    cmd.extend(["-f", f"{key}={value}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise ParseFailedError(
                    f"gh graphql failed: {result.stderr}",
                    "graphql",
                )
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise ParseFailedError("gh graphql request timed out", "graphql")
        except json.JSONDecodeError as e:
            raise ParseFailedError(f"Invalid JSON response: {e}", "graphql")

    def _parse_issue(self, source: str, owner: str, repo: str, number: str) -> ParsedDocument:
        """Parse GitHub issue."""
        # Fetch issue data
        endpoint = f"/repos/{owner}/{repo}/issues/{number}"
        issue = self._run_gh_api(endpoint)

        # Fetch comments
        comments_endpoint = f"{endpoint}/comments"
        comments = self._run_gh_api(comments_endpoint)

        # Build content
        content_parts = [
            f"# {issue.get('title', 'Untitled Issue')}",
            "",
            f"**State:** {issue.get('state', 'unknown')}",
            f"**Author:** @{issue.get('user', {}).get('login', 'unknown')}",
            f"**Created:** {issue.get('created_at', 'unknown')}",
        ]

        # Labels
        labels = [label.get("name") for label in issue.get("labels", [])]
        if labels:
            content_parts.append(f"**Labels:** {', '.join(labels)}")

        # Assignees
        assignees = [a.get("login") for a in issue.get("assignees", [])]
        if assignees:
            content_parts.append(f"**Assignees:** {', '.join(assignees)}")

        content_parts.extend(["", "## Description", "", issue.get("body") or "(No description)"])

        # Add comments
        if comments:
            content_parts.extend(["", "## Comments", ""])
            for i, comment in enumerate(comments, 1):
                author = comment.get("user", {}).get("login", "unknown")
                created = comment.get("created_at", "")
                body = comment.get("body", "")
                content_parts.extend(
                    [
                        f"### Comment {i} by @{author} ({created})",
                        "",
                        body,
                        "",
                    ]
                )

        return ParsedDocument(
            source_path=source,
            source_type="github-issue",
            title=issue.get("title", ""),
            content="\n".join(content_parts),
            metadata={
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "state": issue.get("state"),
                "labels": labels,
                "assignees": assignees,
                "comment_count": len(comments),
                "url": issue.get("html_url", source),
            },
        )

    def _parse_discussion(self, source: str, owner: str, repo: str, number: str) -> ParsedDocument:
        """Parse GitHub discussion using GraphQL."""
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            discussion(number: $number) {
              title
              body
              createdAt
              author { login }
              category { name }
              labels(first: 10) { nodes { name } }
              comments(first: 50) {
                nodes {
                  body
                  createdAt
                  author { login }
                }
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo, "number": int(number)}
        response = self._run_gh_graphql(query, variables)

        discussion = response.get("data", {}).get("repository", {}).get("discussion")
        if not discussion:
            raise ParseFailedError(
                f"Discussion #{number} not found in {owner}/{repo}",
                source,
            )

        # Build content
        content_parts = [
            f"# {discussion.get('title', 'Untitled Discussion')}",
            "",
            f"**Category:** {discussion.get('category', {}).get('name', 'unknown')}",
            f"**Author:** @{discussion.get('author', {}).get('login', 'unknown')}",
            f"**Created:** {discussion.get('createdAt', 'unknown')}",
        ]

        # Labels
        labels = [label.get("name") for label in discussion.get("labels", {}).get("nodes", [])]
        if labels:
            content_parts.append(f"**Labels:** {', '.join(labels)}")

        content_parts.extend(
            [
                "",
                "## Description",
                "",
                discussion.get("body", ""),
            ]
        )

        # Add comments
        comments = discussion.get("comments", {}).get("nodes", [])
        if comments:
            content_parts.extend(["", "## Comments", ""])
            for i, comment in enumerate(comments, 1):
                author = comment.get("author", {}).get("login", "unknown")
                created = comment.get("createdAt", "")
                body = comment.get("body", "")
                content_parts.extend(
                    [
                        f"### Comment {i} by @{author} ({created})",
                        "",
                        body,
                        "",
                    ]
                )

        return ParsedDocument(
            source_path=source,
            source_type="github-discussion",
            title=discussion.get("title", ""),
            content="\n".join(content_parts),
            metadata={
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "category": discussion.get("category", {}).get("name"),
                "labels": labels,
                "comment_count": len(comments),
                "url": source,
            },
        )

    def _parse_pull_request(
        self, source: str, owner: str, repo: str, number: str
    ) -> ParsedDocument:
        """Parse GitHub pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{number}"
        pr = self._run_gh_api(endpoint)

        # Fetch comments
        comments_endpoint = f"/repos/{owner}/{repo}/issues/{number}/comments"
        comments = self._run_gh_api(comments_endpoint)

        # Build content
        content_parts = [
            f"# {pr.get('title', 'Untitled PR')}",
            "",
            f"**State:** {pr.get('state', 'unknown')}",
            f"**Author:** @{pr.get('user', {}).get('login', 'unknown')}",
            f"**Created:** {pr.get('created_at', 'unknown')}",
            f"**Base:** {pr.get('base', {}).get('ref', 'unknown')}",
            f"**Head:** {pr.get('head', {}).get('ref', 'unknown')}",
        ]

        # Labels
        labels = [label.get("name") for label in pr.get("labels", [])]
        if labels:
            content_parts.append(f"**Labels:** {', '.join(labels)}")

        # Reviewers
        reviewers = [r.get("login") for r in pr.get("requested_reviewers", [])]
        if reviewers:
            content_parts.append(f"**Reviewers:** {', '.join(reviewers)}")

        content_parts.extend(["", "## Description", "", pr.get("body") or "(No description)"])

        # Add comments
        if comments:
            content_parts.extend(["", "## Comments", ""])
            for i, comment in enumerate(comments, 1):
                author = comment.get("user", {}).get("login", "unknown")
                created = comment.get("created_at", "")
                body = comment.get("body", "")
                content_parts.extend(
                    [
                        f"### Comment {i} by @{author} ({created})",
                        "",
                        body,
                        "",
                    ]
                )

        return ParsedDocument(
            source_path=source,
            source_type="github-pr",
            title=pr.get("title", ""),
            content="\n".join(content_parts),
            metadata={
                "owner": owner,
                "repo": repo,
                "number": int(number),
                "state": pr.get("state"),
                "labels": labels,
                "reviewers": reviewers,
                "comment_count": len(comments),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "url": pr.get("html_url", source),
            },
        )
