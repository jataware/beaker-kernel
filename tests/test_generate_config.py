"""
Tests for the ``beaker server generate-config`` CLI command.

These exercise the command end-to-end via click's ``CliRunner``, verifying that
a config file is actually written to disk with the expected name and content.
"""

from pathlib import Path

from click.testing import CliRunner

from beaker_notebook.cli.server import server


def test_generate_config_default_writes_config_file():
    """With no arguments, a ``beaker_config.py`` file is written."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(server, ["generate-config"])

        assert result.exit_code == 0, result.output

        config_path = Path("beaker_config.py")
        assert config_path.exists()

        content = config_path.read_text(encoding="utf-8")
        assert "Beaker Notebook Service Configuration File" in content
        assert "c = get_config()" in content


def test_generate_config_custom_file_option():
    """The ``--file`` option controls the output path."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(server, ["generate-config", "--file", "custom_config.py"])

        assert result.exit_code == 0, result.output

        assert Path("custom_config.py").exists()
        assert not Path("beaker_config.py").exists()


def test_generate_config_for_server_type():
    """Passing a server type names the file after that app's slug."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(server, ["generate-config", "server"])

        assert result.exit_code == 0, result.output

        config_path = Path("beaker_server_config.py")
        assert config_path.exists()
        assert "c = get_config()" in config_path.read_text(encoding="utf-8")
