"""Tests for archie.init."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from archie.init import init


class TestInitCommand:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("archie.init.subprocess.run")
    @patch("archie.init.migrate_from_agent_kit")
    @patch("archie.init.load_config")
    @patch("archie.init.save_config")
    @patch("archie.init.save_credentials")
    @patch("archie.init.CONFIG_PATH")
    @patch("archie.init.CREDENTIALS_PATH")
    @patch("archie.init.ARCHIE_HOME")
    def test_creates_brain_structure(
        self,
        mock_home,
        mock_creds_path,
        mock_config_path,
        mock_save_creds,
        mock_save_config,
        mock_load,
        mock_migrate,
        mock_run,
        tmp_path,
    ):
        mock_home.mkdir = MagicMock()
        mock_config_path.exists.return_value = False
        mock_creds_path.exists.return_value = False
        mock_load.return_value = {"brain_dir": str(tmp_path)}
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Create a fake persona path for seed deployment
        with patch("archie.init._persona_path") as mock_persona:
            persona_dir = tmp_path / "persona"
            (persona_dir / "agents").mkdir(parents=True)
            (persona_dir / "agents" / "archie.md").write_text("# Soul")
            (persona_dir / "guidance").mkdir(parents=True)
            (persona_dir / "guidance" / "tools.md").write_text("# Tools")
            mock_persona.return_value = persona_dir

            result = self.runner.invoke(init)

        assert result.exit_code == 0

        # Directories created
        assert (tmp_path / "_archie").is_dir()
        assert (tmp_path / "_archie" / "memory").is_dir()
        assert (tmp_path / "_inbox").is_dir()
        assert (tmp_path / "_raw").is_dir()
        assert (tmp_path / "simon").is_dir()
        assert (tmp_path / "people").is_dir()
        assert (tmp_path / "projects").is_dir()
        assert (tmp_path / "knowledge").is_dir()

        # Files created
        assert (tmp_path / "BRAIN.md").exists()
        assert (tmp_path / "simon" / "profile.md").exists()
        assert (tmp_path / "_archie" / "soul.md").exists()
        assert (tmp_path / "_archie" / "tools.md").exists()

    @patch("archie.init.subprocess.run")
    @patch("archie.init.migrate_from_agent_kit")
    @patch("archie.init.load_config")
    @patch("archie.init.save_config")
    @patch("archie.init.save_credentials")
    @patch("archie.init.CONFIG_PATH")
    @patch("archie.init.CREDENTIALS_PATH")
    @patch("archie.init.ARCHIE_HOME")
    def test_hardcoded_simon(
        self,
        mock_home,
        mock_creds_path,
        mock_config_path,
        mock_save_creds,
        mock_save_config,
        mock_load,
        mock_migrate,
        mock_run,
        tmp_path,
    ):
        mock_home.mkdir = MagicMock()
        mock_config_path.exists.return_value = False
        mock_creds_path.exists.return_value = False
        mock_load.return_value = {"brain_dir": str(tmp_path)}
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("archie.init._persona_path") as mock_persona:
            persona_dir = tmp_path / "persona"
            (persona_dir / "agents").mkdir(parents=True)
            (persona_dir / "agents" / "archie.md").write_text("# Soul")
            (persona_dir / "guidance").mkdir(parents=True)
            (persona_dir / "guidance" / "tools.md").write_text("# Tools")
            mock_persona.return_value = persona_dir

            self.runner.invoke(init)

        brain_md = (tmp_path / "BRAIN.md").read_text()
        assert "simon" in brain_md.lower() or "Simon" in brain_md
        assert "{{USER}}" not in brain_md
        assert "{{AGENT}}" not in brain_md

        profile_md = (tmp_path / "simon" / "profile.md").read_text()
        assert "Simon" in profile_md

    @patch("archie.init.subprocess.run")
    @patch("archie.init.migrate_from_agent_kit")
    @patch("archie.init.load_config")
    @patch("archie.init.save_config")
    @patch("archie.init.save_credentials")
    @patch("archie.init.CONFIG_PATH")
    @patch("archie.init.CREDENTIALS_PATH")
    @patch("archie.init.ARCHIE_HOME")
    def test_idempotent_skips_existing(
        self,
        mock_home,
        mock_creds_path,
        mock_config_path,
        mock_save_creds,
        mock_save_config,
        mock_load,
        mock_migrate,
        mock_run,
        tmp_path,
    ):
        mock_home.mkdir = MagicMock()
        mock_config_path.exists.return_value = True  # config already exists
        mock_creds_path.exists.return_value = True  # creds already exist
        mock_load.return_value = {"brain_dir": str(tmp_path)}
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Pre-create brain structure
        (tmp_path / "_archie").mkdir()
        (tmp_path / "_archie" / "soul.md").write_text("# Existing soul")
        (tmp_path / "BRAIN.md").write_text("# Existing brain")
        (tmp_path / "simon").mkdir()
        (tmp_path / "simon" / "profile.md").write_text("# Existing profile")
        (tmp_path / ".git").mkdir()

        with patch("archie.init._persona_path") as mock_persona:
            persona_dir = tmp_path / "persona"
            (persona_dir / "agents").mkdir(parents=True)
            (persona_dir / "agents" / "archie.md").write_text("# New soul")
            (persona_dir / "guidance").mkdir(parents=True)
            (persona_dir / "guidance" / "tools.md").write_text("# New tools")
            mock_persona.return_value = persona_dir

            result = self.runner.invoke(init)

        assert result.exit_code == 0
        # Existing files should NOT be overwritten
        assert (tmp_path / "_archie" / "soul.md").read_text() == "# Existing soul"
        assert (tmp_path / "BRAIN.md").read_text() == "# Existing brain"
        assert (tmp_path / "simon" / "profile.md").read_text() == "# Existing profile"
        # save_config should NOT be called (config already exists)
        mock_save_config.assert_not_called()

    @patch("archie.init.subprocess.run")
    @patch("archie.init.migrate_from_agent_kit")
    @patch("archie.init.load_config")
    @patch("archie.init.save_config")
    @patch("archie.init.save_credentials")
    @patch("archie.init.CONFIG_PATH")
    @patch("archie.init.CREDENTIALS_PATH")
    @patch("archie.init.ARCHIE_HOME")
    def test_git_init_called(
        self,
        mock_home,
        mock_creds_path,
        mock_config_path,
        mock_save_creds,
        mock_save_config,
        mock_load,
        mock_migrate,
        mock_run,
        tmp_path,
    ):
        mock_home.mkdir = MagicMock()
        mock_config_path.exists.return_value = False
        mock_creds_path.exists.return_value = False
        mock_load.return_value = {"brain_dir": str(tmp_path)}
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("archie.init._persona_path") as mock_persona:
            persona_dir = tmp_path / "persona"
            (persona_dir / "agents").mkdir(parents=True)
            (persona_dir / "agents" / "archie.md").write_text("# Soul")
            (persona_dir / "guidance").mkdir(parents=True)
            (persona_dir / "guidance" / "tools.md").write_text("# Tools")
            mock_persona.return_value = persona_dir

            self.runner.invoke(init)

        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["git", "init"]
        assert mock_run.call_args[1]["cwd"] == tmp_path

    @patch("archie.init.subprocess.run")
    @patch("archie.init.migrate_from_agent_kit")
    @patch("archie.init.load_config")
    @patch("archie.init.save_config")
    @patch("archie.init.save_credentials")
    @patch("archie.init.CONFIG_PATH")
    @patch("archie.init.CREDENTIALS_PATH")
    @patch("archie.init.ARCHIE_HOME")
    def test_creates_database(
        self,
        mock_home,
        mock_creds_path,
        mock_config_path,
        mock_save_creds,
        mock_save_config,
        mock_load,
        mock_migrate,
        mock_run,
        tmp_path,
    ):
        import sqlite3

        mock_home.mkdir = MagicMock()
        mock_config_path.exists.return_value = False
        mock_creds_path.exists.return_value = False
        mock_load.return_value = {"brain_dir": str(tmp_path)}
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch("archie.init._persona_path") as mock_persona:
            persona_dir = tmp_path / "persona"
            (persona_dir / "agents").mkdir(parents=True)
            (persona_dir / "agents" / "archie.md").write_text("# Soul")
            (persona_dir / "guidance").mkdir(parents=True)
            (persona_dir / "guidance" / "tools.md").write_text("# Tools")
            mock_persona.return_value = persona_dir

            self.runner.invoke(init)

        db_path = tmp_path / "brain.db"
        assert db_path.exists()

        db = sqlite3.connect(db_path)
        # Verify tables exist
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        assert "refs" in table_names
        assert "provenance" in table_names
        db.close()
