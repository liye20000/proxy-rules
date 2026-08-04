#!/usr/bin/env python3
"""Classify whether a domain-only pull request is safe to merge unattended.

The script is intentionally conservative. It is executed from the trusted default
branch by ``safe-domain-automerge.yml`` and never imports or runs code from the PR.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import generate


ALLOWED_CHANGED_FILES = {
    "proxy-list.txt",
    "v2rayn-rules.json",
    "shadowrocket.module",
    "shadowrocket.conf",
}

# Ordinary suffix rules for these shared providers have a very large blast radius.
# Exact host rules under the same providers remain eligible for automatic merging.
HIGH_IMPACT_ROOT_DOMAINS = {
    "akamaihd.net",
    "akamaized.net",
    "amazonaws.com",
    "apple.com",
    "azureedge.net",
    "cloudflare.com",
    "fastly.net",
    "github.com",
    "githubusercontent.com",
    "google.com",
    "googleapis.com",
    "gstatic.com",
    "jsdelivr.net",
    "live.com",
    "microsoft.com",
    "npmjs.com",
    "paypal.com",
    "stripe.com",
    "unpkg.com",
}

SAFE_BRANCH_PATTERN = re.compile(r"^codex/domain-[a-z0-9][a-z0-9-]*-[0-9]{8}$")


class UnsafePullRequest(ValueError):
    """Raised when a PR does not satisfy the unattended-merge policy."""


def classify(
    *,
    repository: str,
    event_head_sha: str,
    pr: dict,
    changed_files: set[str],
    base_text: str,
    head_text: str,
) -> list[str]:
    """Return added domain rules, or raise ``UnsafePullRequest`` with a reason."""

    if pr.get("state") != "open":
        raise UnsafePullRequest("pull request is not open")
    if pr.get("draft"):
        raise UnsafePullRequest("draft pull requests require manual review")
    if pr.get("mergeable") is not True or pr.get("mergeable_state") != "clean":
        raise UnsafePullRequest("pull request is not cleanly mergeable against current main")
    if pr.get("author_association") != "OWNER":
        raise UnsafePullRequest("pull request author is not the repository owner")
    if pr.get("base", {}).get("ref") != "main":
        raise UnsafePullRequest("base branch is not main")

    head = pr.get("head", {})
    if head.get("repo", {}).get("full_name") != repository:
        raise UnsafePullRequest("head branch is not in the same repository")
    if not SAFE_BRANCH_PATTERN.fullmatch(head.get("ref", "")):
        raise UnsafePullRequest("head branch does not match codex/domain-<service>-<YYYYMMDD>")
    if head.get("sha") != event_head_sha:
        raise UnsafePullRequest("successful CI does not belong to the current PR head")

    if changed_files != ALLOWED_CHANGED_FILES:
        missing = sorted(ALLOWED_CHANGED_FILES - changed_files)
        unexpected = sorted(changed_files - ALLOWED_CHANGED_FILES)
        details = []
        if missing:
            details.append(f"missing generated files: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected files: {', '.join(unexpected)}")
        raise UnsafePullRequest("; ".join(details))

    base_rules = set(generate.parse_domain_list(base_text))
    head_rules = set(generate.parse_domain_list(head_text))
    removed = sorted(base_rules - head_rules)
    added = sorted(head_rules - base_rules)

    if removed:
        raise UnsafePullRequest(f"domain rules were removed: {', '.join(removed)}")
    if not added:
        raise UnsafePullRequest("no domain rule was added")

    broad = sorted(
        rule
        for rule in added
        if not rule.startswith("exact:") and rule in HIGH_IMPACT_ROOT_DOMAINS
    )
    if broad:
        raise UnsafePullRequest(
            f"high-impact shared root requires manual review: {', '.join(broad)}"
        )

    return added


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--event-head-sha", required=True)
    parser.add_argument("--pr-json", type=Path, required=True)
    parser.add_argument("--changed-files", type=Path, required=True)
    parser.add_argument("--base-list", type=Path, required=True)
    parser.add_argument("--head-list", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    pr = json.loads(args.pr_json.read_text(encoding="utf-8"))
    changed_files = {
        line.strip()
        for line in args.changed_files.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    try:
        added = classify(
            repository=args.repository,
            event_head_sha=args.event_head_sha,
            pr=pr,
            changed_files=changed_files,
            base_text=args.base_list.read_text(encoding="utf-8"),
            head_text=args.head_list.read_text(encoding="utf-8"),
        )
    except UnsafePullRequest as error:
        print(f"Manual review required: {error}")
        return 1

    print(f"Safe additive domain PR: {', '.join(added)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
