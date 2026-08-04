from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generate_runs_for_pull_requests() -> None:
    workflow = (ROOT / ".github/workflows/generate.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow


def test_telegram_update_runs_weekly_and_can_be_dispatched() -> None:
    workflow = (
        ROOT / ".github/workflows/update-telegram-ips.yml"
    ).read_text(encoding="utf-8")

    assert 'cron: "0 3 * * 1"' in workflow
    assert "workflow_dispatch:" in workflow
