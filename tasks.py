"""Everything here is shamelessly copied from compas_invocations2"""

import sys
import glob
import os
import shutil
import contextlib

import invoke


# NOTE: originally taken from invocations https://github.com/pyinvoke/invocations/blob/main/invocations/console.py
def confirm(question, assume_yes=True):
    """
    Ask user a yes/no question and return their response as a boolean.

    ``question`` should be a simple, grammatically complete question such as
    "Do you wish to continue?", and will have a string similar to ``" [Y/n] "``
    appended automatically. This function will *not* append a question mark for
    you.
    By default, when the user presses Enter without typing anything, "yes" is
    assumed. This can be changed by specifying ``assume_yes=False``.

    .. note::

        If the user does not supply input that is (case-insensitively) equal to
        "y", "yes", "n" or "no", they will be re-prompted until they do.

    Parameters
    ----------
    question : str
        The question part of the prompt.
    assume_yes : bool
        Whether to assume the affirmative answer by default. Defaults to ``True``.

    Returns
    -------
    bool
    """
    if assume_yes:
        suffix = "Y/n"
    else:
        suffix = "y/N"

    while True:
        response = input("{} [{}] ".format(question, suffix))
        response = response.lower().strip()

        if not response:
            return assume_yes

        if response in ["y", "yes"]:
            return True

        if response in ["n", "no"]:
            return False

        err = "Focus, kid! It is either (y)es or (n)o"
        print(err, file=sys.stderr)


@contextlib.contextmanager
def chdir(dirname=None):
    """Context-manager syntax to change to a directory and return to the current one afterwards."""
    current_dir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(current_dir)


@invoke.task()
def lint(ctx):
    """Check the consistency of coding style."""

    print("\nRunning ruff linter...")
    ctx.run("ruff check --fix src tests")

    print("\nRunning black linter...")
    ctx.run("black --check --diff --color src tests")

    print("\nAll linting is done!")


@invoke.task()
def format(ctx):
    """Reformat the code base using black."""

    print("\nRunning ruff formatter...")
    ctx.run("ruff format src tests")

    print("\nRunning black formatter...")
    ctx.run("black src tests")

    print("\nAll formatting is done!")


@invoke.task()
def check(ctx):
    """Check the consistency of documentation, coding style and a few other things."""

    with chdir(ctx.base_folder):
        lint(ctx)


@invoke.task(
    help={
        "docs": "True to clean up generated documentation, otherwise False",
        "bytecode": "True to clean up compiled python files, otherwise False.",
        "builds": "True to clean up build/packaging artifacts, otherwise False.",
    }
)
def clean(ctx, docs=True, bytecode=True, builds=True):
    """Cleans the local copy from compiled artifacts."""

    with chdir(ctx.base_folder):
        if bytecode:
            for root, dirs, files in os.walk(ctx.base_folder):
                for f in files:
                    if f.endswith(".pyc"):
                        os.remove(os.path.join(root, f))
                if ".git" in dirs:
                    dirs.remove(".git")

        folders = []

        if docs:
            folders.append("docs/api/generated")

        folders.append("dist/")

        if bytecode:
            for t in ("src", "tests"):
                folders.extend(glob.glob("{}/**/__pycache__".format(t), recursive=True))

        if builds:
            folders.append("build/")
            folders.extend(glob.glob("src/**/*.egg-info", recursive=False))

        for folder in folders:
            shutil.rmtree(os.path.join(ctx.base_folder, folder), ignore_errors=True)


@invoke.task(help={"release_type": "Type of release follows semver rules. Must be one of: major, minor, patch."})
def release(ctx, release_type):
    """Releases the project in one swift command!"""
    if release_type not in ("patch", "minor", "major"):
        raise invoke.Exit("The release type parameter is invalid.\nMust be one of: major, minor, patch.")

    # Run formatter
    ctx.run("invoke format")

    # Run checks
    ctx.run("invoke test")

    # Bump version and git tag it
    ctx.run("bump-my-version bump %s --verbose" % release_type)

    # Build project
    ctx.run("python -m build")

    # Prepare the change log for the next release
    prepare_changelog(ctx)

    # Clean up local artifacts
    clean(ctx)

    # Upload to pypi
    if confirm(
        "Everything is ready. You are about to push to git which will trigger a release to pypi.org. Are you sure?",
        assume_yes=False,
    ):
        ctx.run("git push --tags && git push")
    else:
        raise invoke.Exit("You need to manually revert the tag/commits created.")


@invoke.task
def prepare_changelog(ctx):
    """Prepare changelog for next release."""
    UNRELEASED_CHANGELOG_TEMPLATE = "## Unreleased\n\n### Added\n\n### Changed\n\n### Removed\n\n\n## "

    with chdir(ctx.base_folder):
        # Preparing changelog for next release
        with open("CHANGELOG.md", "r+") as changelog:
            content = changelog.read()
            changelog.seek(0)
            changelog.write(content.replace("## ", UNRELEASED_CHANGELOG_TEMPLATE, 1))

        ctx.run('git add CHANGELOG.md && git commit -m "Prepare changelog for next release"')
