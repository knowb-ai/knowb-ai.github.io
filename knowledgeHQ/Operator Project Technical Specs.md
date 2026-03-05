# Operator — Code-Level Architecture Specification

## Purpose

This document defines how **Operator** is built as a code project. It describes the three core layers of the system and the contracts between them:

1. Knowledge Agents
2. Knowledge Base
3. Context and Memory Middleware

This is an engineering specification. It is not a product document.

---

## Ground Rules

The following constraints are non-negotiable:

- Operator is a **daemon**, not a library
- Operator is **local-first**
- Agents are **stateless executors**
- Memory is **not chat history**
- Knowledge is **not memory**
- CLI is the **control plane**

Violating these rules collapses the system into a chat application.

---

## 1. Knowledge Agents

### 1.1 Definition

A knowledge agent is a task executor that operates within Operator-managed constraints.

Agents:
- Do not own persistence
- Do not store files directly
- Do not maintain long-term memory
- Do not communicate with other agents directly

Agents only:
- Receive input
- Receive scoped context and memory
- Execute a task
- Emit structured output

---

### 1.2 Agent Contract

All agents must conform to the same contract.

Conceptual interface:

```
Agent {
  id
  type
  capabilities
  run(input, context, memory) -> output
}
```

Rules:
- Context is injected by Operator
- Memory is injected by Operator
- Output must be structured

---

### 1.3 Agent Types (v0)

At v0, Operator supports three abstract agent classes.

#### 1. Knowledge / Task Agent
- Reads from the Knowledge Base
- Writes structured outputs to the Knowledge Base
- Used for research, synthesis, extraction, and planning

#### 2. Code Agent
- Operates on local files and scripts
- Requests tool execution through Operator
- Cannot mutate the Knowledge Base directly

#### 3. Chat Agent
- Thin wrapper over external LLMs
- No memory of its own
- Always mediated by Operator context and memory

Chat agents are not special. They are the simplest agent type.

---

### 1.4 Execution Model

- Agents are spawned by Operator
- Agents are given scoped input, context, and memory
- Agents run
- Agents are terminated

Concurrency:
- Managed entirely by Operator
- Agents never communicate directly
- All shared state goes through memory or the Knowledge Base

---

## 2. Knowledge Base

### 2.1 Definition

The Knowledge Base (KB) is a durable, structured knowledge store.

It is:
- Not a chat log
- Not a vector dump
- Not a document folder

Conceptual layers:

```
Raw Data
→ Structured Facts
→ Entities
→ Relations
→ Semantic Index
```

---

### 2.2 Responsibilities

The Knowledge Base must:
- Store raw source data
- Store extracted knowledge
- Store agent outputs
- Track provenance
- Track versions
- Support symbolic and semantic queries

This implies multiple internal stores, not a single database.

---

### 2.3 Minimum Viable KB (v0)

v0 requires the following components:

1. Document Store
   - Files
   - Notes
   - Agent outputs
   - Versioned

2. Metadata Store
   - Source
   - Timestamp
   - Agent ID
   - Confidence / status

3. Semantic Index
   - Embeddings
   - Chunk references

v0 explicitly excludes:
- Full knowledge graphs
- Ontology engines
- Automated reasoning systems

---

### 2.4 Knowledge Base API (Conceptual)

Operator exposes a controlled KB interface:

- kb.ingest(source)
- kb.query(symbolic | semantic)
- kb.write(entity | fact | summary)
- kb.inspect(provenance)

Agents never interact with storage internals directly.

---

## 3. Context and Memory Middleware

### 3.1 Memory vs Knowledge

Memory and knowledge are separate systems.

| Memory | Knowledge |
|------|----------|
| Short / medium term | Long-term |
| Mutable | Stable |
| Contextual | Factual |
| Task-scoped | Canonical |

---

### 3.2 Memory Layers

Operator maintains three memory tiers.

#### 1. Working Memory
- Current task state
- Ephemeral
- Destroyed after task completion

#### 2. Session Memory
- Active session context
- Preferences
- Recent decisions
- Lives longer than one task

#### 3. Persistent Context
- User preferences
- Behavioral defaults
- Routing rules
- Survives restarts

Only selected memory is promoted into the Knowledge Base.

---

### 3.3 Memory as a Service

Memory is a middleware service, not a data structure.

It:
- Controls exposure
- Enforces scope
- Manages lifecycle
- Handles promotion and eviction

Agents request memory slices. They do not manage memory directly.

---

### 3.4 Memory API (Conceptual)

Operator provides:

- memory.read(scope)
- memory.write(scope, data)
- memory.promote(data → KB)
- memory.flush(scope)

Memory policy is enforced here, not in agents.

---

## 4. Layer Interaction Model

All interactions follow this flow:

```
User / CLI
 → Operator
   → Context & Memory
   → Knowledge Base
   → Agent(s)
   → Memory updates
   → Knowledge Base writes
```

There are no shortcuts.

---

## 5. Early Repository Structure

```
operator/
  core/
    daemon/
    config/
  agents/
    base
    knowledge
    code
    chat
  kb/
    store/
    index/
    metadata/
  memory/
    working/
    session/
    persistent/
  cli/
    commands/
  contracts/
    agent.md
    kb.md
    memory.md
```

This structure enforces separation of concerns.

---

## 6. Next Required Specs

Before implementation, the following must be locked:

1. Agent interface specification
2. Knowledge Base read/write contract
3. Memory scope and promotion rules
4. Daemon lifecycle (boot, steady state, shutdown)

Implementation choices come after contracts.

---

## Canonical Statement

Operator is the Knowledge OS runtime.
It owns knowledge, memory, context, and agents.

Everything else is a client.
