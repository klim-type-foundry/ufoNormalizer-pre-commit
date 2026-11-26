"""
The hook's command: normalises each UFO that contains a file pre-commit passes to it.
"""

import argparse
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from importlib.metadata import version
from pathlib import Path

import ufonormalizer

DISTRIBUTION_NAME = "ufonormalizer-pre-commit"
UFO_SUFFIX = ".ufo"
# Values of the `CI` environment variable that don't mean it's running in CI
NOT_CI_VALUES = {"", "0", "false", "no"}


def get_ufo_path(file_path: str | Path) -> Path | None:
    """
    Returns the path of the UFO that a file is in, or None if it isn't in one.
    The UFO is the outermost folder in the path whose name ends in `.ufo` (in any
    case), e.g. `sources/Family.ufo` for `sources/Family.ufo/glyphs/a.glif`.
    """
    # Only the folders: a file can't be the UFO it's in
    folders = Path(file_path).parts[:-1]
    for index, folder in enumerate(folders):
        if folder.lower().endswith(UFO_SUFFIX):
            return Path(*folders[: index + 1])
    return None


def get_ufo_paths(file_paths: Iterable[str | Path]) -> list[Path]:
    """
    Returns the paths of the UFOs that the files are in, sorted and without
    duplicates. Files that aren't in a UFO, and UFOs that don't exist (e.g. as
    they've been deleted), are skipped.
    """
    ufo_paths = {get_ufo_path(file_path) for file_path in file_paths}
    return sorted(path for path in ufo_paths if path is not None and path.is_dir())


def is_ci() -> bool:
    """
    Returns whether the hook is running in CI, which sets the `CI` environment
    variable (e.g. GitHub Actions sets it to `true`).
    """
    return os.environ.get("CI", "").strip().lower() not in NOT_CI_VALUES


def normalize_ufo(ufo_path: Path) -> None:
    """
    Normalises all the files in a UFO, in place, the same as `ufonormalizer --all
    --no-mod-times`, so it doesn't write the normalisation times into the UFO.
    """
    ufonormalizer.normalizeUFO(str(ufo_path), onlyModified=False, writeModTimes=False)


def git_add(ufo_path: Path) -> None:
    """
    Adds the changes to the files in a UFO that Git already tracks to the index.
    """
    subprocess.run(
        ["git", "add", "--update", "--", str(ufo_path)],
        check=True,
        capture_output=True,
        text=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=DISTRIBUTION_NAME,
        description=(
            "Normalise each UFO that contains one of the given files, with ufoNormalizer."
        ),
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="files in the UFOs to normalise, as passed by pre-commit",
    )
    parser.add_argument(
        "--autofix",
        action="store_true",
        help=(
            "add the normalised UFOs to the commit, rather than failing so you can "
            "review the changes. Ignored in CI (when the CI environment variable "
            "is set), so CI still fails if a UFO isn't normalised"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version(DISTRIBUTION_NAME)}",
    )
    args = parser.parse_args(argv)
    autofix = args.autofix and not is_ci()

    exit_code = 0
    for ufo_path in get_ufo_paths(args.filenames):
        try:
            normalize_ufo(ufo_path)
        # ufoNormalizer raises various errors for UFOs it can't read (e.g. XML or
        # plist errors), so report any of them and carry on with the other UFOs
        except Exception as error:  # noqa: BLE001
            print(f"{ufo_path}: couldn't normalise the UFO: {error}", file=sys.stderr)
            exit_code = 1
            continue

        if autofix:
            try:
                git_add(ufo_path)
            except subprocess.CalledProcessError as error:
                print(
                    f"{ufo_path}: couldn't add the UFO to the commit: "
                    f"{error.stderr.strip()}",
                    file=sys.stderr,
                )
                exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
