"""Top-level init command — sets up config, credentials, and brain."""

import sqlite3
import subprocess
from importlib.resources import as_file, files
from pathlib import Path

import click

from archie.config import (
    ARCHIE_HOME,
    CONFIG_PATH,
    CREDENTIALS_PATH,
    load_config,
    migrate_from_agent_kit,
    save_config,
    save_credentials,
)
from archie.errors import handle_errors


def _load_template(name: str) -> str:
    """Load a template file from the package."""
    templates = files("archie").joinpath("brain", "templates", name)
    with as_file(templates) as path:
        return path.read_text()


def _persona_path() -> Path:
    """Resolve persona directory from source tree.

    In practice, archie is always run from an editable install (the repo is mounted
    and installed with -e). This function finds the persona directory relative to the
    source code location.
    """
    src = Path(__file__).resolve().parents[2] / "persona"
    if src.exists():
        return src
    raise FileNotFoundError("Persona directory not found — archie init requires an editable install")


@click.command()
@handle_errors
def init() -> None:
    """Initialise archie — config, credentials, and brain."""
    # Migrate from agent-kit if old paths exist
    migrate_from_agent_kit()

    # --- Config ---
    ARCHIE_HOME.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        click.echo(f"  Config exists: {CONFIG_PATH}")
    else:
        save_config(load_config())
        click.echo(f"  Created {CONFIG_PATH}")

    # --- Credentials ---
    if CREDENTIALS_PATH.exists():
        click.echo(f"  Credentials exists: {CREDENTIALS_PATH}")
    else:
        save_credentials({})
        click.echo(f"  Created {CREDENTIALS_PATH}")

    # --- Brain ---
    config = load_config()
    brain_dir = Path(config.get("brain_dir", "~/.archie/brain")).expanduser()

    # Directories
    dirs = [
        brain_dir / "_archie",
        brain_dir / "_archie" / "memory",
        brain_dir / "_raw",
        brain_dir / "_inbox",
        brain_dir / "simon",
        brain_dir / "people",
        brain_dir / "projects",
        brain_dir / "knowledge",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            click.echo(f"  Created {d.relative_to(brain_dir)}/")

    # Deploy soul.md from persona/agents/archie.md
    soul_dest = brain_dir / "_archie" / "soul.md"
    if not soul_dest.exists():
        persona = _persona_path()
        soul_src = persona / "agents" / "archie.md"
        if soul_src.exists():
            soul_dest.write_text(soul_src.read_text())
            click.echo("  Deployed _archie/soul.md")

    # Deploy tools.md from persona/guidance/tools.md
    tools_dest = brain_dir / "_archie" / "tools.md"
    if not tools_dest.exists():
        persona = _persona_path()
        tools_src = persona / "guidance" / "tools.md"
        if tools_src.exists():
            tools_dest.write_text(tools_src.read_text())
            click.echo("  Deployed _archie/tools.md")

    # BRAIN.md
    brain_md_path = brain_dir / "BRAIN.md"
    if not brain_md_path.exists():
        brain_md_path.write_text(_load_template("BRAIN.md"))
        click.echo("  Created BRAIN.md")

    # simon/profile.md
    profile_path = brain_dir / "simon" / "profile.md"
    if not profile_path.exists():
        profile_path.write_text(_load_template("profile.md"))
        click.echo("  Created simon/profile.md")

    # Database
    db_path = brain_dir / "brain.db"
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE IF NOT EXISTS refs (path TEXT NOT NULL, ts INTEGER NOT NULL)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_refs_path ON refs(path)")
    db.execute("""CREATE TABLE IF NOT EXISTS provenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT NOT NULL,
        ingested_at TEXT NOT NULL,
        entities_created TEXT,
        entities_updated TEXT
    )""")
    db.commit()
    db.close()

    # Gitignore
    gitignore = brain_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("brain.db\n.brain.lock\n")

    # Git repo
    if not (brain_dir / ".git").exists():
        result = subprocess.run(
            ["git", "init"],
            cwd=brain_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            click.echo("  Initialised git repo")
        else:
            click.echo(f"  Warning: git init failed: {result.stderr.strip()}")

    click.echo("Done.")
