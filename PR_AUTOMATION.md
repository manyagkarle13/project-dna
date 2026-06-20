**Usage**: Add automated detection and PR creation

- **Detect issues**: Run tests and linters across the repo.

  - Command:

    ```bash
    python tools/code_assistant.py detect
    ```

- **Apply patch & create PR**: Apply a git-format patch, commit, push branch, and open a PR.

  - Command example using `gh` CLI (recommended):

    ```bash
    python tools/code_assistant.py apply --patch changes.patch --message "Fix bug" --pr-title "Fix: bug in X"
    ```

  - If you prefer the GitHub API instead of `gh`, set `GITHUB_TOKEN` or `GH_TOKEN` in the environment:

    ```powershell
    setx GITHUB_TOKEN "ghp_..."
    ```

- Notes:
  - The script expects to be run from the repository root.
  - Working tree must be clean before applying a patch.
  - The script will try `gh` first, then fall back to the GitHub API when a token is available.
