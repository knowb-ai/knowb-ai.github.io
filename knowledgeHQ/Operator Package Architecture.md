# Operator — Package Architecture & Stack Design

## Problem

Operator is a local Knowledge OS runtime that needs to be deployable in multiple modes:
- **Admin CLI** — on dev machines for init, inspect, manage
- **Worker daemon** — on remote servers, long-running, accepts workflows
- **Ephemeral** — single workflow execution, exits on completion (containerized)

All modes share the same core logic. The package architecture must enforce clean separation between domain logic and deployment concerns.

---

## Naming

Python's stdlib has an `operator` module — we need a distinct namespace.

- **PyPI packages**: `opx-core`, `opx-cli`, `opx-worker`
- **Python imports**: `opx_core`, `opx_cli`, `opx_worker`
- **CLI binary**: `opx` (admin), `opx-worker` (daemon)
- Alternatively: `knowb-operator-*` if you want the brand in the package name.

---

## Package Architecture

### 1. `opx-core` — The Brain (pure library, zero entrypoints)

All domain logic lives here. No CLI deps, no server deps. Importable by anything.

```
opx-core/
  src/opx_core/
    __init__.py
    runtime.py          # OperatorRuntime — the main class
    kb/
      __init__.py
      store.py          # Document store (SQLite-backed)
      index.py          # Semantic index (embeddings)
      metadata.py       # Provenance, versioning, source tracking
      models.py         # KB entity models (Pydantic)
    memory/
      __init__.py
      working.py        # Ephemeral task memory (in-process)
      session.py        # Session-scoped memory (survives tasks)
      persistent.py     # User prefs, defaults (survives restarts)
      promotion.py      # Memory → KB promotion logic
    context/
      __init__.py
      assembler.py      # Builds scoped context for agent injection
      environment.py    # User env, routing rules, behavioral defaults
    agents/
      __init__.py
      contract.py       # Agent interface (abstract base)
      registry.py       # Agent type registry & instantiation
      lifecycle.py      # Spawn, scope, execute, terminate
      types/
        knowledge.py    # Knowledge/Task agent
        code.py         # Code agent
        chat.py         # Chat agent (thin LLM wrapper)
    tasks/
      __init__.py
      graph.py          # Task DAG / coordination
      scheduler.py      # Execution ordering, parallelism
      synthesis.py      # Final output assembly from agent results
    config/
      __init__.py
      settings.py       # Pydantic Settings (env-driven config)
    errors.py           # Typed exceptions
    logging.py          # structlog configuration
  pyproject.toml
```

Key class: `OperatorRuntime` — instantiated per-client-per-workflow. Owns a KB handle, memory scope, context assembler, and agent lifecycle. This is the single object that "is" Operator.

---

### 2. `opx-cli` — Admin Tool (depends on opx-core)

Thin CLI shell. Provides the `opx` binary.

```
opx-cli/
  src/opx_cli/
    __init__.py
    main.py             # Typer app entrypoint
    commands/
      init.py           # opx init — scaffold a new KB workspace
      inspect.py        # opx inspect — show KB/memory/agent state
      run.py            # opx run <workflow> — execute locally
      config.py         # opx config — manage settings
      kb.py             # opx kb ingest/query/export
  pyproject.toml        # depends on opx-core, typer, rich
```

The CLI creates an `OperatorRuntime`, calls methods on it, formats output. That's it.

---

### 3. `opx-worker` — Server Daemon (depends on opx-core)

HTTP server that receives workflow requests and spawns `OperatorRuntime` instances.

```
opx-worker/
  src/opx_worker/
    __init__.py
    server.py           # FastAPI app
    runner.py           # Spawns OperatorRuntime per workflow
    routes/
      workflows.py      # POST /workflows — submit, GET /workflows/:id — status
      health.py         # GET /health
    middleware/
      auth.py           # Client auth (API key / token)
  pyproject.toml        # depends on opx-core, fastapi, uvicorn
```

Ephemeral mode: `opx-worker run --ephemeral --workflow-id=<id>` — starts, executes one workflow, exits. Same binary, different lifecycle.

---

## Monorepo Structure

```
operator/
  packages/
    opx-core/
    opx-cli/
    opx-worker/
  tests/
    unit/
    integration/
  docker/
    Dockerfile.worker
    Dockerfile.ephemeral
    docker-compose.yml
  pyproject.toml          # uv workspace root
  README.md
```

Managed by `uv` workspaces — each package is independently publishable to PyPI but developed together.

---

## Stack

- **Runtime**: Python 3.13
- **Package mgmt**: `uv` workspaces (monorepo, fast installs, lockfile)
- **Models/Config**: Pydantic v2 (all models, settings, validation)
- **CLI**: Typer + Rich (type-hint driven CLI, beautiful terminal output)
- **Worker API**: FastAPI + uvicorn (async HTTP, auto-docs)
- **KB Document Store**: SQLite via `aiosqlite` (local-first, zero-config, portable)
- **KB Semantic Index**: ChromaDB or LanceDB (local embeddings, no server needed)
- **Logging**: structlog (structured, JSON-friendly)
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: ruff (format + check, line-length 100)
- **Containers**: Docker (worker + ephemeral images)
- **CI/CD**: GitHub Actions

---

## Why NOT a Single Package

Separate packages because:

1. **Deployment footprint**: A remote worker server shouldn't install Typer/Rich. An admin machine doesn't need FastAPI/uvicorn.
2. **Dependency isolation**: Core has minimal deps (pydantic, sqlite, structlog). CLI adds Typer+Rich. Worker adds FastAPI+uvicorn. No bloat.
3. **Independent versioning**: Core can release a patch without touching CLI or Worker.
4. **Import clarity**: `from opx_core.kb import store` is unambiguous.

But they share the same monorepo and are tested together.

---

## Key Design Rules (from knowledgeHQ specs)

1. `OperatorRuntime` owns everything — KB, memory, context, agents. Nothing else does.
2. Agents are stateless. They receive `(input, context, memory)` and emit structured output.
3. Memory is NOT knowledge. Working memory dies with the task. Only promoted data enters KB.
4. CLI and Worker are clients of core, not extensions. They can be replaced.
5. No shortcuts in the data flow: `User → Runtime → Context+Memory → KB → Agent(s) → Memory updates → KB writes`.

---

## Development Flow

1. Scaffold monorepo with `uv init --lib` for each package
2. Build `opx-core` first — runtime, KB store, memory, agent contract
3. Wire `opx-cli` as the first consumer — `opx init`, `opx run`
4. Add `opx-worker` when ready for server deployment
5. Every step is testable, installable (`uv pip install -e`), and distributable
