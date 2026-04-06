# Operator — The Knowledge OS Runtime

## What It Is

Operator is a local-first, CLI-driven runtime that enables a Knowledge OS. It runs as a background daemon or inline tool, and owns everything: the knowledge base, memory, context, and agents.

Operator has no UI. It is headless, scriptable, automatable, and UI-agnostic. Products like Kenobi are clients of Operator, not replacements (see: Operator vs Kenobi).

---

## What It Does

### 1. Knowledge Base (KB)

Operator manages a local knowledge base where all organizational knowledge is stored and accessed: documents, entity knowledge, agent outputs, structured and unstructured data.

Properties: local-first, user-owned, persistent, model-agnostic.

The KB is not a chat log, not a vector dump, not a document folder. It is a durable, structured knowledge store with conceptual layers:

```
Raw Data → Structured Facts → Entities → Relations → Semantic Index
```

KB API (conceptual):
- kb.ingest(source)
- kb.query(symbolic | semantic)
- kb.write(entity | fact | summary)
- kb.inspect(provenance)

Minimum Viable KB (v0): Document store (versioned), metadata store (source, timestamp, agent ID, confidence), semantic index (embeddings + chunk refs). Excludes knowledge graphs, ontology engines, automated reasoning.

### 2. Memory and Context

Memory and knowledge are separate systems.

- **Memory**: short/medium term, mutable, contextual, task-scoped
- **Knowledge**: long-term, stable, factual, canonical

Three memory tiers:
1. **Working Memory** — current task state, ephemeral, destroyed after task
2. **Session Memory** — active session context, preferences, recent decisions
3. **Persistent Context** — user preferences, behavioral defaults, routing rules, survives restarts

Only selected memory is promoted into the KB.

Memory API (conceptual):
- memory.read(scope)
- memory.write(scope, data)
- memory.promote(data → KB)
- memory.flush(scope)

Agents do not manage memory independently. They read from and write to Operator-managed memory.

### 3. Agent Orchestration

Operator instantiates, scopes, executes, and terminates agents. Agents are stateless executors — they do not own persistence, do not store files, do not maintain long-term memory, do not communicate with other agents directly.

Agent contract:
```
Agent {
  id
  type
  capabilities
  run(input, context, memory) -> output
}
```

Agent types (v0):
1. **Knowledge/Task Agent** — reads/writes KB, used for research, synthesis, extraction
2. **Code Agent** — operates on local files, requests tool execution through Operator
3. **Chat Agent** — thin LLM wrapper, no memory of its own, always mediated by Operator

Concurrency is managed entirely by Operator. All shared state goes through memory or KB.

---

## Design Rules (Non-Negotiable)

1. Operator is a **daemon and a library**, not just one or the other
2. Operator is **local-first**
3. Agents are **stateless executors**
4. Memory is **not chat history**
5. Knowledge is **not memory**
6. CLI is the **control plane**
7. No shortcuts in the data flow: `User/CLI → Operator → Context+Memory → KB → Agent(s) → Memory updates → KB writes`

Violating these rules collapses the system into a chat application.

---

## Execution Model

- Runs as a **background daemon** on a local port, OR inline via CLI
- Controlled via **CLI commands**
- Long-running, restart-safe, crash-resilient
- Scriptable, automatable, composable

---

## What Operator Is Not

- A product UI
- A chat interface
- A dashboard
- A SaaS frontend

Those responsibilities belong to Kenobi or other future clients.

> Operator is the system.
> Everything else connects to it.
