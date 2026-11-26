import os
import subprocess
from pathlib import Path

import pytest

# A glyph that isn't normalised: on one line, with its elements out of order
UNNORMALIZED_GLIF = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<glyph name="{name}" format="2"><unicode hex="0061"/><advance width="500"/>'
    "</glyph>"
)
METAINFO_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>creator</key><string>org.example.tests</string>
<key>formatVersion</key><integer>3</integer>
</dict>
</plist>
"""
LAYERCONTENTS_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<array><array><string>public.default</string><string>glyphs</string></array></array>
</plist>
"""


def contents_plist(glyphs: dict[str, str]) -> str:
    entries = "".join(
        f"<key>{name}</key><string>{file_name}</string>"
        for name, file_name in glyphs.items()
    )
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>{entries}</dict>
</plist>
"""


def build_ufo(path: Path, glyph_name: str = "a", glif: str | None = None) -> Path:
    """
    Saves a small UFO 3 with one glyph, which isn't normalised, and returns its
    path. The glyph's file is named after the glyph, e.g. `a.glif`.
    """
    if glif is None:
        glif = UNNORMALIZED_GLIF.format(name=glyph_name)
    glyphs_path = path / "glyphs"
    glyphs_path.mkdir(parents=True)
    path.joinpath("metainfo.plist").write_text(METAINFO_PLIST)
    path.joinpath("layercontents.plist").write_text(LAYERCONTENTS_PLIST)
    glyphs_path.joinpath("contents.plist").write_text(
        contents_plist({glyph_name: f"{glyph_name}.glif"})
    )
    glyphs_path.joinpath(f"{glyph_name}.glif").write_text(glif)
    return path


def ufo_files(ufo_path: Path) -> dict[str, str]:
    """
    Returns the contents of each file in a UFO, by its path in the UFO.
    """
    return {
        file.relative_to(ufo_path).as_posix(): file.read_text()
        for file in sorted(ufo_path.rglob("*"))
        if file.is_file()
    }


def git(repo_path: Path, *args: str) -> str:
    """
    Runs a Git command in a repo and returns its output.
    """
    result = subprocess.run(
        ["git", *args], cwd=repo_path, check=True, capture_output=True, text=True
    )
    return result.stdout


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch):
    """
    Runs each test outside CI, and without Git settings from the environment
    (e.g. when the tests run in a Git hook), so Git uses each test's repo.
    """
    monkeypatch.delenv("CI", raising=False)
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    An empty Git repo, which is the current directory during the test.
    """
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    git(repo_path, "init", "--quiet", "--initial-branch=main")
    git(repo_path, "config", "user.name", "Tests")
    git(repo_path, "config", "user.email", "tests@example.com")
    git(repo_path, "config", "commit.gpgsign", "false")
    monkeypatch.chdir(repo_path)
    return repo_path
