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
Decision* (2026-10-22), as corrected by the owner on 2026-11-01: commits are
the invoking person's, and only pull request creation is the bot's.

- **Commits and pushes are made as the invoking person**, with their own git
  identity and GitHub login. Agents never commit or push as a bot.
- **Only opening a pull request goes through `knowb-kenobi[bot]`**, the
  `knowb-ai` GitHub App (App ID 5422911), with
  [`scripts/kenobi.sh`](scripts/kenobi.sh):

  ```sh
  git commit -m "..."
  git push -u origin my-branch
  scripts/kenobi.sh gh pr create --title "..." --body-file -
  ```

  The script reads the app key from the macOS Keychain (service
  `knowb-kenobi`) through knowledgeHQ's `mcp/scripts/as-kenobi.sh`, mints an
  installation token that reaches only this repository and expires within the
  hour, and never prints it. It runs nothing but `gh pr create`. Set
  `KNOWB_HQ` when knowledgeHQ is not checked out next to this repository.
- **The invoking person reviews.** The GitHub account that asked for the work
  is resolved from that person's own `gh` login and is set as both reviewer
  and assignee on every pull request the bot opens. Reviews, change requests,
  labels, and comments that person asks for are posted as them, never as the
  bot.
- **Attribution.** Every commit carries a `Co-Authored-By` trailer for the
  model or agent that wrote it.
- **The bot never merges.** The invoking reviewer merges.
- **No fallback.** If the Keychain item, the token, or knowledgeHQ is
  unavailable, do not open the pull request another way; stop and report it.
- **Enforcement.** `.claude/settings.json` denies raw `gh pr create` and
  `gh pr merge`, so pull requests open only through the script and agents
  never merge. Reading GitHub (`gh pr view`, `gh api` reads) needs no bot
  token.
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
