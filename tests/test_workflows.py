from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_runs_for_pull_requests() -> None:
    workflow = (ROOT / ".github/workflows/generate.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "github.event_name == 'pull_request'" in workflow
    assert "contents: write" in workflow


def test_telegram_update_runs_weekly_and_can_be_dispatched() -> None:
    workflow = (
        ROOT / ".github/workflows/update-telegram-ips.yml"
    ).read_text(encoding="utf-8")

    assert 'cron: "0 3 * * 1"' in workflow
    assert "workflow_dispatch:" in workflow


def test_safe_automerge_consumes_successful_generate_runs() -> None:
    workflow = (
        ROOT / ".github/workflows/safe-domain-automerge.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_run:" in workflow
    assert 'workflows: ["generate"]' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "commits/$EVENT_HEAD_SHA/pulls" in workflow
    assert "safe-domain-automerge-main" in workflow
    assert "persist-credentials: false" in workflow
    assert "classify_safe_domain_pr.py" in workflow
    assert "--match-head-commit" in workflow
    assert "actions: write" in workflow
    assert "gh workflow run generate.yml" in workflow
