import pytest

from classify_safe_domain_pr import (
    ALLOWED_CHANGED_FILES,
    UnsafePullRequest,
    classify,
)


REPOSITORY = "liye20000/proxy-rules"
HEAD_SHA = "abc123"


def make_pr(**overrides):
    pr = {
        "state": "open",
        "draft": False,
        "mergeable": True,
        "mergeable_state": "clean",
        "author_association": "OWNER",
        "base": {"ref": "main"},
        "head": {
            "ref": "codex/domain-example-20260804",
            "sha": HEAD_SHA,
            "repo": {"full_name": REPOSITORY},
        },
    }
    pr.update(overrides)
    return pr


def classify_example(
    *,
    pr=None,
    files=None,
    base="existing.com\n",
    head="existing.com\nexample.com\n",
):
    return classify(
        repository=REPOSITORY,
        event_head_sha=HEAD_SHA,
        pr=pr if pr is not None else make_pr(),
        changed_files=files if files is not None else set(ALLOWED_CHANGED_FILES),
        base_text=base,
        head_text=head,
    )


def test_accepts_additive_domain_only_pr():
    assert classify_example() == ["example.com"]


def test_accepts_exact_host_under_shared_provider():
    added = classify_example(head="existing.com\nexact:api.cloudflare.com\n")
    assert added == ["exact:api.cloudflare.com"]


@pytest.mark.parametrize(
    ("pr", "reason"),
    [
        (make_pr(draft=True), "draft"),
        (make_pr(mergeable=False, mergeable_state="dirty"), "cleanly mergeable"),
        (make_pr(author_association="CONTRIBUTOR"), "owner"),
        (make_pr(base={"ref": "release"}), "main"),
        (
            make_pr(
                head={
                    "ref": "codex/domain-example-20260804",
                    "sha": HEAD_SHA,
                    "repo": {"full_name": "someone/fork"},
                }
            ),
            "same repository",
        ),
        (
            make_pr(
                head={
                    "ref": "feature/example",
                    "sha": HEAD_SHA,
                    "repo": {"full_name": REPOSITORY},
                }
            ),
            "codex/domain",
        ),
    ],
)
def test_rejects_untrusted_pr_metadata(pr, reason):
    with pytest.raises(UnsafePullRequest, match=reason):
        classify_example(pr=pr)


def test_rejects_ci_for_stale_head():
    with pytest.raises(UnsafePullRequest, match="current PR head"):
        classify(
            repository=REPOSITORY,
            event_head_sha="stale",
            pr=make_pr(),
            changed_files=set(ALLOWED_CHANGED_FILES),
            base_text="existing.com\n",
            head_text="existing.com\nexample.com\n",
        )


def test_rejects_unexpected_or_missing_files():
    with pytest.raises(UnsafePullRequest, match="unexpected files"):
        classify_example(files=set(ALLOWED_CHANGED_FILES) | {"generate.py"})

    with pytest.raises(UnsafePullRequest, match="missing generated files"):
        classify_example(files={"proxy-list.txt"})


def test_rejects_domain_removal():
    with pytest.raises(UnsafePullRequest, match="removed"):
        classify_example(base="existing.com\nold.example\n", head="existing.com\nexample.com\n")


def test_rejects_high_impact_shared_root():
    with pytest.raises(UnsafePullRequest, match="high-impact"):
        classify_example(head="existing.com\ncloudflare.com\n")


def test_rejects_pr_without_new_domain():
    with pytest.raises(UnsafePullRequest, match="no domain"):
        classify_example(head="existing.com\n")
