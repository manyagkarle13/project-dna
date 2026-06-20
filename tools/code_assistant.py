#!/usr/bin/env python3
"""Code assistant CLI to detect issues and create PRs from patches.

Usage:
  python tools/code_assistant.py detect
  python tools/code_assistant.py apply --patch mychange.patch --message "Fix bug" --pr-title "Fix: ..."

This script:
- Runs tests to detect failures (`detect`).
- Applies a git patch, creates a branch, commits, pushes, and opens a PR (`apply`).

It prefers the `gh` CLI for creating PRs, otherwise falls back to the GitHub REST API using `GITHUB_TOKEN`.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_cmd(cmd, cwd=None, capture=False):
    try:
        if capture:
            return subprocess.run(cmd, cwd=cwd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        else:
            return subprocess.run(cmd, cwd=cwd, check=False)
    except FileNotFoundError:
        return None


def detect(args):
    print("Running backend tests with pytest...")
    res = run_cmd([sys.executable, "-m", "pytest", "-q", "Backend"]) 
    if res is None:
        print("pytest not found. Make sure pytest is installed in your environment.")
        return 2
    code = res.returncode
    if code == 0:
        print("All tests passed (Backend).")
    else:
        print(f"Tests failed (exit code {code}). See above output.")

    # Try frontend lint if Node/npm available and Frontend exists
    if (Path("Frontend") / "package.json").exists() and shutil.which("npm"):
        print("Running frontend lint (if configured)...")
        # run npm run lint if script exists
        try:
            package = (Path("Frontend") / "package.json").read_text()
            if '"lint"' in package:
                run_cmd(["npm", "--prefix", "Frontend", "run", "lint"]) 
            else:
                print("No lint script configured in Frontend/package.json.")
        except Exception:
            print("Failed to run frontend lint.")

    return code


def apply_patch(args):
    patch = Path(args.patch)
    if not patch.exists():
        print(f"Patch file not found: {patch}")
        return 1

    # ensure we're in a git repo
    if run_cmd(["git", "rev-parse", "--is-inside-work-tree"], capture=True).returncode != 0:
        print("Not a git repository. Run this from the repository root.")
        return 1

    # ensure clean working tree
    st = run_cmd(["git", "status", "--porcelain"], capture=True)
    if st and st.stdout.strip():
        print("Working tree is not clean. Please commit or stash changes first.")
        return 1

    branch = args.branch or f"auto/edit-{int(time.time())}"
    print(f"Creating branch {branch}...")
    if run_cmd(["git", "checkout", "-b", branch]).returncode != 0:
        print("Failed to create branch.")
        return 1

    print(f"Applying patch {patch}...")
    apply_res = run_cmd(["git", "apply", str(patch)])
    if apply_res is None or apply_res.returncode != 0:
        print("git apply failed. Aborting and switching back to previous branch.")
        run_cmd(["git", "checkout", "-"], capture=False)
        return 1

    run_cmd(["git", "add", "-A"]) 
    commit_msg = args.message or f"Automated edit: {patch.name}"
    if run_cmd(["git", "commit", "-m", commit_msg]).returncode != 0:
        print("Nothing to commit after applying patch. Switching back to previous branch.")
        run_cmd(["git", "checkout", "-"], capture=False)
        return 1

    print(f"Pushing branch {branch} to origin...")
    if run_cmd(["git", "push", "-u", "origin", branch]).returncode != 0:
        print("Failed to push branch. Please check remote settings and permissions.")
        return 1

    pr_title = args.pr_title or commit_msg
    pr_body = args.pr_body or "Automated PR created by code_assistant.py"

    # Try gh CLI first
    if shutil.which("gh"):
        print("Creating PR using gh CLI...")
        cmd = ["gh", "pr", "create", "--title", pr_title, "--body", pr_body]
        if args.base:
            cmd += ["--base", args.base]
        res = run_cmd(cmd)
        if res and res.returncode == 0:
            print("PR created successfully via gh.")
            return 0
        else:
            print("gh CLI failed to create PR; falling back to API if token is present.")

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("No GITHUB_TOKEN or GH_TOKEN found. Install or login with `gh` CLI, or set GITHUB_TOKEN in environment to enable automatic PR creation.")
        print("Branch pushed; you can create a PR manually.")
        return 0

    # Try GitHub API
    import json
    import urllib.request

    repo = get_remote_repo()
    if not repo:
        print("Unable to determine remote repository (origin).")
        return 1

    owner, repo_name = repo
    data = {"title": pr_title, "body": pr_body, "head": branch, "base": args.base or "main"}
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            print("PR created via API:", body)
            return 0
    except Exception as e:
        print("Failed to create PR via API:", e)
        return 1


def get_remote_repo():
    # parse origin url like git@github.com:owner/repo.git or https://github.com/owner/repo.git
    res = run_cmd(["git", "config", "--get", "remote.origin.url"], capture=True)
    if res is None or res.returncode != 0:
        return None
    url = res.stdout.strip()
    if url.startswith("git@github.com:"):
        path = url.split(":", 1)[1]
    elif url.startswith("https://github.com/"):
        path = url.split("github.com/", 1)[1]
    else:
        return None
    if path.endswith(".git"):
        path = path[:-4]
    if "/" in path:
        owner, repo = path.split("/", 1)
        return owner, repo
    return None


def main():
    parser = argparse.ArgumentParser(description="Project DNA code assistant: detect issues and create PRs from patches.")
    sub = parser.add_subparsers(dest="cmd")

    d = sub.add_parser("detect")

    a = sub.add_parser("apply")
    a.add_argument("--patch", required=True, help="Path to a git-format patch or diff to apply")
    a.add_argument("--message", help="Commit message for the applied changes")
    a.add_argument("--pr-title", help="Pull request title")
    a.add_argument("--pr-body", help="Pull request body")
    a.add_argument("--branch", help="Branch name to create (defaults to auto/...)")
    a.add_argument("--base", help="Base branch for the PR (default: main)")

    args = parser.parse_args()
    if args.cmd == "detect":
        code = detect(args)
        sys.exit(code if isinstance(code, int) else 0)
    elif args.cmd == "apply":
        sys.exit(apply_patch(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
