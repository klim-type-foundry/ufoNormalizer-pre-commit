import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import build_ufo, git

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def pre_commit_home(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    A pre-commit cache for the tests, so they install the hook from this repo
    rather than using an installed one. pre-commit needs to download the hook's
    dependencies the first time.
    """
    return tmp_path_factory.mktemp("pre-commit-home")


def try_hook(repo: Path, pre_commit_home: Path) -> subprocess.CompletedProcess[str]:
    """
    Installs the hook from this repo (with any uncommitted changes) and runs it on
    all the files in a repo, as in CI.
    """
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pre_commit",
            "try-repo",
            str(ROOT),
            "ufonormalizer",
            "--all-files",
            "--color=never",
        ],
        # It fails when the hook changes files, which the tests check
        check=False,
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ["PATH"],
            "HOME": str(Path.home()),
            "PRE_COMMIT_HOME": str(pre_commit_home),
        },
    )


def test_hook_fails_for_unnormalized_ufo(repo, pre_commit_home):
    build_ufo(repo / "sources" / "Family.ufo")
    repo.joinpath("README.md").write_text("Not in a UFO\n")
    git(repo, "add", ".")

    result = try_hook(repo, pre_commit_home)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "files were modified by this hook" in result.stdout
    assert "sources/Family.ufo/glyphs/a.glif" in git(repo, "diff", "--name-only")

    # Passes once the UFO is normalised
    git(repo, "add", ".")
    result = try_hook(repo, pre_commit_home)
    assert result.returncode == 0, result.stdout + result.stderr


def test_readme_uses_this_version():
    # The README's examples use the latest release, so they can be copied as is
    version = ROOT.joinpath("VERSION").read_text().strip()
    readme = ROOT.joinpath("README.md").read_text()
    revs = re.findall(r"^\s*rev: (\S+)$", readme, re.MULTILINE)
    assert revs
    assert set(revs) == {version}
