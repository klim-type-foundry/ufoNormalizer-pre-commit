# ufoNormalizer-pre-commit

[![Checks](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/actions/workflows/check.yml/badge.svg?branch=main)](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/actions/workflows/check.yml)
[![Licence](https://img.shields.io/github/license/klim-type-foundry/ufoNormalizer-pre-commit)](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/blob/main/LICENSE.txt)

A [pre-commit](https://pre-commit.com/) hook that normalises
[UFO](https://unifiedfontobject.org) font sources with
[ufoNormalizer](https://github.com/unified-font-object/ufoNormalizer), so they
stay in a consistent format, whichever app saved them, and their Git diffs only
show real changes.

For each UFO that a committed file is in, the hook normalises all the files in
the UFO, the same as `ufonormalizer --all --no-mod-times`. It doesn't write the
normalisation times into the UFO, so normalising doesn't change files by itself.

## Install

Add this to your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/klim-type-foundry/ufoNormalizer-pre-commit
    rev: 2.0.0
    hooks:
      - id: ufonormalizer
```

When the hook changes a UFO, the commit stops, so you can review the changes,
add them and commit again. To add the changes to the commit automatically
instead, add `--autofix`:

```yaml
  - repo: https://github.com/klim-type-foundry/ufoNormalizer-pre-commit
    rev: 2.0.0
    hooks:
      - id: ufonormalizer
        args: [ --autofix ]
```

`--autofix` adds only the files in the UFO that Git already tracks, and is
ignored in CI (when the `CI` environment variable is set, as GitHub Actions
does), so CI still fails if a UFO isn't normalised.

The hook needs Python 3.11 or later. pre-commit installs ufoNormalizer for it.

## Usage

The hook runs on each commit. To normalise all the UFOs in the repo:

```shell
pre-commit run ufonormalizer --all-files
```

In CI, e.g. with [pre-commit/action](https://github.com/pre-commit/action), it
checks that all the UFOs are normalised.

## Contributing

Bug reports, ideas and pull requests are welcome: see the
[contributing guide](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/blob/main/CONTRIBUTING.md)
for how to set up the project and make a change. Please report security
problems privately, as the
[security policy](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/blob/main/SECURITY.md)
explains.

## Licence

[Apache License 2.0](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/blob/main/LICENSE.txt)
