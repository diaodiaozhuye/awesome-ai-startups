"""Tests for the CLI commands."""

from __future__ import annotations

from click.testing import CliRunner

from scrapers.cli import cli


class TestCLI:
    def test_validate_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_generate_stats_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["generate-stats"])
        assert result.exit_code == 0
        assert "Done!" in result.output

    def test_show_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "openai"])
        assert result.exit_code == 0
        assert "OpenAI" in result.output

    def test_show_nonexistent(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "nonexistent-company-xyz"])
        assert result.exit_code == 1

    def test_scrape_dry_run(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["scrape", "--source", "crunchbase", "--dry-run"])
        assert result.exit_code == 0
