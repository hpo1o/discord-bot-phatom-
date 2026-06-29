"""Pure helpers for the 108-hour Discord link ownership report."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit


_URL_RE = re.compile(r"https?://[^\s<>\"]+", re.IGNORECASE)
_TRAILING_PUNCTUATION = ".,!?;:)]}'\""


def normalize_url(raw_url: str) -> str | None:
    """Return a stable URL key while preserving referral query parameters."""
    candidate = raw_url.strip().rstrip(_TRAILING_PUNCTUATION)
    if not candidate:
        return None

    try:
        parsed = urlsplit(candidate)
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        return None

    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        return None

    # Treat HTTP/HTTPS and www/non-www spellings as the same destination.
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    if port and port not in {80, 443}:
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"

    return urlunsplit(("https", netloc, path, parsed.query, ""))


def extract_links(content: str) -> set[str]:
    """Extract and normalize unique HTTP(S) links from a Discord message."""
    links = set()
    for match in _URL_RE.finditer(content or ""):
        normalized = normalize_url(match.group(0))
        if normalized:
            links.add(normalized)
    return links


def find_eligible_user_ids(
    messages: Iterable[tuple[str, str]]
) -> list[str]:
    """Return users who never posted a link first posted by another user.

    Messages must be supplied in chronological order. The first author of a
    normalized link is its owner. Reposting one's own link is allowed; a later
    different author is excluded from the report.
    """
    link_owners: dict[str, str] = {}
    users_with_links: set[str] = set()
    disqualified_users: set[str] = set()

    for author_id, content in messages:
        author_id = str(author_id)
        links = extract_links(content)
        if not links:
            continue

        users_with_links.add(author_id)
        for link in links:
            owner_id = link_owners.setdefault(link, author_id)
            if owner_id != author_id:
                disqualified_users.add(author_id)

    eligible = users_with_links - disqualified_users
    return sorted(
        eligible,
        key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value)
    )


def build_discord_id_csv(discord_ids: Iterable[str]) -> bytes:
    """Build a UTF-8 CSV containing only the Discord ID column."""
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["discord_id"])
    for discord_id in discord_ids:
        writer.writerow([str(discord_id)])
    return output.getvalue().encode("utf-8")
