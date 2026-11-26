from pathlib import Path

import pytest

from tests.conftest import build_ufo, git, ufo_files
from ufonormalizer_pre_commit import cli

NORMALIZED_GLIF = """\
<?xml version="1.0" encoding="UTF-8"?>
<glyph name="{name}" format="2">
\t<unicode hex="0061"/>
\t<advance width="500"/>
</glyph>
"""


def normalized_glif(name: str = "a") -> str:
    return NORMALIZED_GLIF.format(name=name)


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        ("sources/Family.ufo/glyphs/a.glif", Path("sources/Family.ufo")),
        ("Family.ufo/metainfo.plist", Path("Family.ufo")),
        ("sources/Family.UFO/glyphs/a.glif", Path("sources/Family.UFO")),
        # The glyph's file name has "ufo" in it, which isn't the UFO
        ("sources/Family.ufo/glyphs/ufo.glif", Path("sources/Family.ufo")),
        ("sources/Family.ufo/glyphs/a.ufo_alt.glif", Path("sources/Family.ufo")),
        # The outermost UFO
        ("Family.ufo/data/Other.ufo/metainfo.plist", Path("Family.ufo")),
        # Non-ASCII paths
        ("sources/Café.ufo/glyphs/a.glif", Path("sources/Café.ufo")),
        # Not in a UFO
        ("sources/Family.ufo", None),
        ("sources/Family.ufoz/metainfo.plist", None),
        ("sources/Bufo/a.glif", None),
        ("README.md", None),
    ],
)
def test_get_ufo_path(file_path, expected):
    assert cli.get_ufo_path(file_path) == expected


def test_get_ufo_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build_ufo(tmp_path / "B.ufo")
    build_ufo(tmp_path / "sources" / "A.ufo")
    paths = cli.get_ufo_paths(
        [
            "B.ufo/glyphs/a.glif",
            "sources/A.ufo/metainfo.plist",
            "B.ufo/metainfo.plist",
            "README.md",
            # A deleted UFO
            "Deleted.ufo/metainfo.plist",
        ]
    )
    assert paths == [Path("B.ufo"), Path("sources/A.ufo")]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        ("0", False),
        ("false", False),
        ("False", False),
        ("no", False),
        ("true", True),
        ("1", True),
        ("yes", True),
    ],
)
def test_is_ci(monkeypatch, value, expected):
    if value is not None:
        monkeypatch.setenv("CI", value)
    assert cli.is_ci() is expected


def test_normalizes_ufos(repo):
    ufo_path = build_ufo(repo / "sources" / "Family.ufo")
    other_ufo_path = build_ufo(repo / "Other.ufo")

    assert cli.main(["sources/Family.ufo/glyphs/a.glif", "README.md"]) == 0

    assert ufo_path.joinpath("glyphs", "a.glif").read_text() == normalized_glif()
    # All the files in the UFO, not only the one given
    assert ufo_files(ufo_path)["metainfo.plist"].count("\n\t") > 0
    # Without writing the normalisation times
    assert not ufo_path.joinpath("data", "org.unifiedfontobject.normalizer").exists()
    # Only the UFOs that the given files are in
    assert ufo_files(other_ufo_path) == ufo_files(build_ufo(repo / "Unchanged.ufo"))


def test_normalized_ufo_is_unchanged(repo):
    ufo_path = build_ufo(repo / "Family.ufo")
    assert cli.main(["Family.ufo/metainfo.plist"]) == 0
    normalized = ufo_files(ufo_path)

    assert cli.main(["Family.ufo/metainfo.plist"]) == 0
    assert ufo_files(ufo_path) == normalized


def test_glyph_named_ufo(repo):
    ufo_path = build_ufo(repo / "Family.ufo", glyph_name="ufo")
    assert cli.main(["Family.ufo/glyphs/ufo.glif"]) == 0
    assert ufo_path.joinpath("glyphs", "ufo.glif").read_text() == normalized_glif("ufo")


def test_no_files(repo):
    assert cli.main([]) == 0


def test_does_not_add_to_index_without_autofix(repo):
    build_ufo(repo / "Family.ufo")
    git(repo, "add", ".")

    assert cli.main(["Family.ufo/glyphs/a.glif"]) == 0

    # Normalised in the working tree only, so pre-commit sees the changes and fails
    assert git(repo, "diff", "--name-only").splitlines() == [
        "Family.ufo/glyphs/a.glif",
        "Family.ufo/glyphs/contents.plist",
        "Family.ufo/layercontents.plist",
        "Family.ufo/metainfo.plist",
    ]


def test_autofix_adds_to_index(repo):
    build_ufo(repo / "Family.ufo")
    # An untracked file in the UFO, which isn't added
    repo.joinpath("Family.ufo", "untracked.txt").write_text("untracked")
    git(repo, "add", "Family.ufo/glyphs", "Family.ufo/*.plist")

    assert cli.main(["--autofix", "Family.ufo/glyphs/a.glif"]) == 0

    assert git(repo, "diff", "--name-only") == ""
    assert git(repo, "show", ":Family.ufo/glyphs/a.glif") == normalized_glif()
    assert git(repo, "ls-files", "--others") == "Family.ufo/untracked.txt\n"


def test_autofix_ignored_in_ci(repo, monkeypatch):
    monkeypatch.setenv("CI", "true")
    build_ufo(repo / "Family.ufo")
    git(repo, "add", ".")

    assert cli.main(["--autofix", "Family.ufo/glyphs/a.glif"]) == 0

    # Normalised, but not added, so pre-commit sees the changes and fails
    assert repo.joinpath("Family.ufo", "glyphs", "a.glif").read_text() == (
        normalized_glif()
    )
    assert "Family.ufo/glyphs/a.glif" in git(repo, "diff", "--name-only")


def test_autofix_git_error(tmp_path, monkeypatch, capsys):
    # Not in a Git repo, so `git add` fails
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    ufo_path = build_ufo(tmp_path / "Family.ufo")

    assert cli.main(["--autofix", "Family.ufo/glyphs/a.glif"]) == 1

    assert ufo_path.joinpath("glyphs", "a.glif").read_text() == normalized_glif()
    error = capsys.readouterr().err
    assert error.startswith("Family.ufo: couldn't add the UFO to the commit: ")
    assert "not a git repository" in error


def test_invalid_ufo(repo, capsys):
    build_ufo(repo / "Broken.ufo", glif="<glyph name='a'")
    ufo_path = build_ufo(repo / "Family.ufo")

    assert cli.main(["Broken.ufo/glyphs/a.glif", "Family.ufo/glyphs/a.glif"]) == 1

    assert capsys.readouterr().err.startswith(
        "Broken.ufo: couldn't normalise the UFO: "
    )
    # The other UFOs are still normalised
    assert ufo_path.joinpath("glyphs", "a.glif").read_text() == normalized_glif()


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--version"])
    assert exit_info.value.code == 0
    version = Path(__file__).parent.parent.joinpath("VERSION").read_text().strip()
    assert capsys.readouterr().out == f"ufonormalizer-pre-commit {version}\n"
