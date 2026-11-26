# Contributing

Thanks for helping to improve ufoNormalizer-pre-commit! Bug reports, ideas and
pull requests are all welcome.

## Reporting a bug or asking for a feature

[Open an issue](https://github.com/klim-type-foundry/ufoNormalizer-pre-commit/issues/new/choose)
and pick the form that fits. For a bug, it helps to know:

- the hook's version (the `rev:` in your `.pre-commit-config.yaml`)
- your operating system, Python version and pre-commit version, or the CI
  service
- the command you ran, and the hook's output
- what you expected, and what happened instead

If you can share a UFO that shows the problem, please do. If you can't share it,
say so, and we'll work out another way.

The hook runs [ufoNormalizer](https://github.com/unified-font-object/ufoNormalizer)
as it is, so please report problems with how it formats UFOs to ufoNormalizer.

Please report security problems privately, not in an issue: see
[SECURITY.md](SECURITY.md).

## Making a change

For anything bigger than a small fix, please open an issue first, so we can
agree on the approach before you spend time on it.

### Setting up

With [uv](https://docs.astral.sh/uv/) installed:

```shell
make init
```

This sets up the Python environment in `.venv/` with the exact package versions
from `uv.lock`, and installs the [pre-commit](https://pre-commit.com/) hooks.

### Checks

```shell
make test
```

Before each commit, the pre-commit hooks run Ruff (linting and formatting), mypy
and some general file checks. The same checks and the tests run on every pull
request.

- **Tests:** add or update tests in `tests/` for what you change. Some tests
  install the hook from this repo with pre-commit and run it, as users do. They
  use the files Git tracks, so `git add` any new files before running them.
- **Types:** the code is fully type-annotated, and mypy must pass with no errors.
- **Documentation:** if you change the hook's options or behaviour, update the
  [README](README.md) too.

### Pull requests

- Keep each pull request to one change, and describe what it changes and why.
- Pull requests are squash-merged, so the pull request's title becomes the
  commit message on `main`: write it as a short summary of the change, e.g.
  "Skip UFOs that have been deleted".
- Don't change `VERSION`: the maintainers do that when releasing.

## Releasing (maintainers)

To release a new version, change the version in `VERSION`, and the `rev:` in the
README's examples to match (a test checks this), and merge it into `main`. The
release workflow runs the checks, and then tags the commit with the version
(e.g. `2.0.0`, without a `v`, as in users' `rev:`) and creates a GitHub release
for it. pre-commit installs the hook from the tag, and `pre-commit autoupdate`
finds it, so there's nothing to publish anywhere else.

If a change to `.github/workflows` is merged into `main` after the release
commit but before the GitHub release is created, GitHub doesn't let the
workflow tag the release commit, so the "create GitHub release" job fails. Its
log shows how to finish the release: push the tag yourself and re-run the job,
or create the release by hand. To avoid this, don't merge workflow changes
(such as Dependabot's) while a release is running.

## Licence

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE.txt), the same as the rest of the project.

## Code of conduct

This project follows a [code of conduct](CODE_OF_CONDUCT.md). By taking part,
you agree to follow it.
