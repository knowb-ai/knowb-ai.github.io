# Operator — Package Architecture

## Single Package Design

One repo. One package. Library + CLI + daemon. No split.

- **Repo**: `knowb-ai/operator`
- **PyPI**: `knowb-operator`
- **Import**: `knowb_operator`
- **CLI binary**: `operator`

Operator is both importable as a library and usable as a CLI tool. Same install, two interfaces. Same pattern as `black`, `ruff`, `uvicorn`, `flask`.

---

## Usage Modes

### As a library
```python
from knowb_operator import OperatorRuntime
runtime = OperatorRuntime()
await runtime.start()
doc = await runtime.ingest("data.txt", content)
output = await runtime.run_agent("knowledge", input)
await runtime.stop()
```

### As a CLI tool
```bash
operator init                           # scaffold KB workspace
operator serve --port 8400              # start daemon mode
operator run <workflow>                 # ephemeral inline execution
operator status                         # ping daemon for agent/task progress
operator kb ingest data.zip             # manage knowledge base
operator kb query "vendor contracts"    # query KB
operator logs --agent-id <id>           # detailed logs by agent
operator logs --task-id <id>            # detailed logs by task
```

The daemon mode (`operator serve`) starts a FastAPI server on a local port. CLI commands can either talk to the daemon (if running) or execute inline (if not).

---

## Package Layout

```
knowb-operator/                         # knowb-ai/operator repo
  src/knowb_operator/
    __init__.py                         # OperatorRuntime + public API
    runtime.py                          # The main class
    cli.py                              # Typer app — all CLI commands
    server.py                           # FastAPI daemon app
    kb/
      __init__.py
      store.py                          # Document store (SQLite)
      index.py                          # Semantic index (embeddings)
      metadata.py                       # Provenance, versioning
      models.py                         # KB entity models (Pydantic)
    memory/
      __init__.py
      working.py                        # Ephemeral task memory
      session.py                        # Session-scoped memory
      persistent.py                     # User prefs, survives restarts
      promotion.py                      # Memory → KB promotion
    context/
      __init__.py
      assembler.py                      # Scoped context for agent injection
      environment.py                    # User env, routing rules
    agents/
      __init__.py
      contract.py                       # Agent ABC
      registry.py                       # Agent type registry
      lifecycle.py                      # Spawn, scope, execute, terminate
      types/
        knowledge.py                    # Knowledge/Task agent
        code.py                         # Code agent
        chat.py                         # Chat agent (LLM wrapper)
    tasks/
      __init__.py
      graph.py                          # Task DAG
      scheduler.py                      # Execution ordering, parallelism
      synthesis.py                      # Final output assembly
    config/
      settings.py                       # Pydantic Settings (env-driven)
    errors.py
    logging.py                          # structlog config
  tests/
    unit/
    integration/
  pyproject.toml
  README.md
```

---

## pyproject.toml

```toml
[project]
name = "knowb-operator"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "aiosqlite>=0.20.0",
    "structlog>=24.0.0",
    "typer>=0.15.0",
    "rich>=13.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[project.scripts]
operator = "knowb_operator.cli:app"
```

All deps bundled. No optional extras needed — this is a developer tool, not a constrained embedded system.

---

## Stack

- **Runtime**: Python 3.14
- **Package mgmt**: uv
- **Models/Config**: Pydantic v2
- **CLI**: Typer + Rich
- **Daemon API**: FastAPI + uvicorn
- **KB Store**: SQLite via aiosqlite
- **KB Semantic Index**: ChromaDB or LanceDB
- **Logging**: structlog
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: ruff (line-length 100)
- **CI/CD**: GitHub Actions

---

## Daemon Mode

`operator serve` starts a FastAPI server exposing:

- `GET /health` — version, uptime, agent count
- `GET /status` — running agents, task progress, KB stats
- `POST /workflows/` — submit a workflow
- `GET /workflows/:id` — workflow status and result
- `GET /agents/:id/logs` — detailed logs by agent
- `GET /tasks/:id/logs` — detailed logs by task
- `GET /kb/sources` — list KB sources and stats

CLI commands like `operator status` and `operator logs` hit these endpoints when the daemon is running. When it's not, they execute inline against the local KB directly.

---

## Design Rules

1. `OperatorRuntime` owns everything — KB, memory, context, agents.
2. Agents are stateless. They receive `(input, context, memory)` and emit structured output.
3. Memory is NOT knowledge. Working memory dies with the task.
4. No shortcuts in the data flow: `User → Runtime → Context+Memory → KB → Agent(s) → Memory updates → KB writes`.
5. The package is both importable and CLI-installable. Always.

---

## Development Flow

1. Create `knowb-ai/operator`, scaffold single package
2. Build runtime, KB store, memory, agent contract (port from emos-core patterns)
3. Wire CLI commands — `operator init`, `operator run`, `operator kb`
4. Add daemon mode — `operator serve` with status/logs endpoints
5. Every step: tested, installable, distributable
