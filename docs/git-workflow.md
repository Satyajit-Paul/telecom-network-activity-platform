# Git workflow

Each project stage starts from the latest `main` on its own branch. Changes are committed and pushed to that branch, checked, and merged into `main` through a pull request. Retain milestone branches so their final commits remain easy to find.

1. Start with a clean working tree and update `main` from GitHub using `git pull --ff-only origin main`.
2. Create a descriptive branch, for example `milestone/03-dbt-warehouse`, from the updated `main`.
3. Implement the stage in focused commits. Keep credentials, generated data, and downloaded source files out of Git.
4. Run checks appropriate to the stage, including Python and database integration tests when ingestion changes, and dbt build/tests when dbt models change. Record the actual results in the pull request. Automated CI will be added in stage 6; do not claim it has passed before it exists.
5. Push the branch and open a pull request targeting `main`. Explain the change, checks, and remaining limitations. Review the diff and ensure required checks pass.
6. Merge the tested pull request using a merge commit, retain the milestone branch, and update local `main` with `git pull --ff-only origin main`. Verify local and remote `main` match.

Do not force-push or rewrite shared history as part of routine stage work. If a check fails, fix it on the branch and rerun the affected checks before merging.

## Existing history

Stages 1 and 2 were originally committed directly to `main` before this workflow was established. The branches `milestone/01-design-and-fixtures` and `milestone/02-ingestion` were added afterward as historical markers. Their commits were already on `main`; they were not retrospectively merged through pull requests. All later stages should follow the workflow above.
