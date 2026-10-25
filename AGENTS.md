# knowb.run agent instructions

This repository is the public `knowb.run` website, a Zola static site. Read
these instructions before changing anything here.

## Repository boundary

- This repository owns the public website only.
- The KnowB MCP connector, its project registry, and its releases live in the
  private [knowledgeHQ](https://github.com/knowb-ai/knowledgeHQ) repository.
  Register new projects there, never here.
- The canonical visual decisions also live in knowledgeHQ. `DESIGN_SYSTEM.md`
  and `ORGBRAND_GUIDELINES.md` here are public companions; change them only
  after the knowledgeHQ canon changes.

## GitHub identity and pull requests

This follows the knowledgeHQ *Connector Consolidation and Agent Identity
Decision* (2026-10-22).

- **Agents write to GitHub as `knowb-kenobi[bot]`**, the `knowb-ai` GitHub App
  (App ID 5422911). Commits, pushes, and pull requests from agents always go
  through [`scripts/kenobi.sh`](scripts/kenobi.sh):

  ```sh
  scripts/kenobi.sh git commit -m "..."
  scripts/kenobi.sh git push -u origin my-branch
  scripts/kenobi.sh gh pr create --title "..." --body-file -
  ```

  The script reads the app key from the macOS Keychain (service
  `knowb-kenobi`) through knowledgeHQ's `mcp/scripts/as-kenobi.sh`, mints an
  installation token that reaches only this repository and expires within the
  hour, and never prints it. Set `KNOWB_HQ` when knowledgeHQ is not checked
  out next to this repository.
- **The invoking person reviews.** The GitHub account that asked for the work
  is resolved from that person's own `gh` login and is set as both reviewer
  and assignee on every pull request the bot opens. It is also added as the
  human `Co-Authored-By` trailer on every bot commit.
- **Attribution.** Every commit carries two `Co-Authored-By` trailers: the
  model or agent that wrote it, and the invoking person. Put the model's
  trailer in the commit message; the script adds the person's.
- **The bot never merges.** The invoking reviewer merges. `scripts/kenobi.sh`
  refuses `gh pr merge`.
- **No fallback to a personal login.** Never commit, push, or open a pull
  request as the owner's own account on an agent's behalf. If the Keychain
  item, the token, or knowledgeHQ is unavailable, stop and report it.
- **Enforcement.** `.claude/settings.json` denies raw `git commit`,
  `git push`, `gh pr create`, and `gh pr merge` so these calls go through the
  script. Reading GitHub (`gh pr view`, `gh api` reads) needs no bot token.
- Open work in progress as a draft pull request and keep follow-up commits on
  the same branch and pull request unless the reviewer asks for a new one.

## Building and checking the site

- Local preview: `zola serve --port 1111 --interface 127.0.0.1` (also the
  `knowb-dev` entry in `.claude/launch.json`).
- Before opening or updating a pull request, run
  `zola check --skip-external-links` and look at the changed pages in the
  preview, at desktop and phone width.
- Text must meet WCAG 2.2 AA (4.5:1 for normal text). Pushes to `main` deploy
  through `.github/workflows/deploy.yml`, so `main` must always build.
