#!/usr/bin/env python3
"""Build the resume, or publish its source to Overleaf and its PDF to GitHub."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "resume/overleaf.json"
SOURCE = ROOT / "resume/main.tex"
PDF = ROOT / "folder/Intern_Resume.pdf"
PUBLISH_PATHS = [
    "resume/main.tex", "resume/overleaf.json", "folder/Intern_Resume.pdf",
    "scripts/sync_resume.py", "README.md", ".gitignore", "index.html", "cv.html",
]
IDENTITY = ["-c", "user.name=Mingyu Zhao", "-c", "user.email=zhao.mingyu@rutgers.edu"]


def run(*args, cwd=ROOT, capture=False):
    result = subprocess.run(
        args, cwd=cwd, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return result.stdout.strip() if capture else None


def build():
    if not shutil.which("xelatex"):
        raise RuntimeError("XeLaTeX is required to build this fontspec-based resume.")
    build_dir = ROOT / ".build/resume"
    build_dir.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        result = subprocess.run(
            ["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={build_dir}", str(SOURCE)],
            cwd=SOURCE.parent, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if result.returncode:
            print(result.stdout[-6000:])
            raise RuntimeError(f"Compilation failed; see {build_dir / 'main.log'}")
    shutil.copyfile(build_dir / "main.pdf", PDF)
    print(f"Built {PDF.relative_to(ROOT)}", flush=True)


def check_github():
    if run("git", "branch", "--show-current", capture=True) != "main":
        raise RuntimeError("Publish from the website's main branch.")
    staged = run("git", "diff", "--cached", "--name-only", capture=True)
    if staged:
        raise RuntimeError("The index has staged changes; commit or unstage them before publishing.")
    run("git", "fetch", "--quiet", "origin", "main")
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"], cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError("GitHub has changes missing locally. Integrate them before publishing.")


def sync(publish):
    config = json.loads(CONFIG.read_text())
    if publish:
        check_github()
    with tempfile.TemporaryDirectory(prefix="resume-overleaf-") as directory:
        checkout = Path(directory) / "source"
        run("git", "clone", "--quiet", "--single-branch", "--branch", config["branch"],
            config["git_url"], str(checkout))
        remote_head = run("git", "rev-parse", "HEAD", cwd=checkout, capture=True)
        remote_source = checkout / "main.tex"
        identical = remote_source.exists() and remote_source.read_bytes() == SOURCE.read_bytes()
        if remote_head != config["last_synced_commit"] and not identical:
            raise RuntimeError(
                "Overleaf has new changes. Compare its main.tex with resume/main.tex and "
                "merge them first; then set last_synced_commit in resume/overleaf.json "
                f"to the reviewed commit {remote_head}. Nothing was published."
            )
        build()
        if not publish:
            print("Overleaf check passed. No remote changes were made.")
            return
        if not identical:
            shutil.copyfile(SOURCE, remote_source)
            run("git", "add", "main.tex", cwd=checkout)
            run("git", *IDENTITY, "commit", "-m", "Update resume from website source", cwd=checkout)
            run("git", "push", "origin", f"HEAD:{config['branch']}", cwd=checkout)
        config["last_synced_commit"] = run("git", "rev-parse", "HEAD", cwd=checkout, capture=True)
        CONFIG.write_text(json.dumps(config, indent=2) + "\n")

    run("git", "add", "--", *PUBLISH_PATHS)
    if run("git", "diff", "--cached", "--name-only", capture=True):
        run("git", *IDENTITY, "commit", "-m", "Update resume and synchronize Overleaf source")
    run("git", "push", "origin", "HEAD:main")
    print("Published resume source to Overleaf and resume PDF to GitHub.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Check Overleaf and build, without publishing")
    group.add_argument("--publish", action="store_true", help="Build and publish to Overleaf and GitHub")
    args = parser.parse_args()
    try:
        if args.check or args.publish:
            sync(args.publish)
        else:
            build()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Resume update stopped: {error}\n")


if __name__ == "__main__":
    main()
