# **Kenobi - Product Book v1.0**

---

## **1. Definition**

**Kenobi** is an AI-native knowledge operating system that enables organizations to query, reason over, and act on all internal data through a unified, secure, conversational interface.

It is the **product layer** on top of the KnowB system:

```txt
Kenobi = Operator + Knowledge OS + Knowledge Base + Agent Layer + UI
```

Kenobi does not store knowledge independently.  
It orchestrates access, reasoning, and execution across the system.

---

## **2. Problem**

Modern organizations operate across fragmented systems:

- Documents (Notion, Drive, Confluence)
- Data (SQL, warehouses, APIs)
- Communication (Slack, email)
- Operational systems (CRM, ERP)

This results in:

- No unified access layer
- Heavy reliance on analysts and BI teams
- Slow time-to-insight
- Inconsistent or unsafe AI usage
- Lack of traceability and context continuity

Traditional solutions fail:

|**Category**|**Limitation**|
|---|---|
|Dashboards|Static, predefined, non-exploratory|
|SQL|Skill-gated, slow, non-scalable across org|
|Knowledge Bases|Unstructured, not queryable, not intelligent|
|AI Copilots|Lack grounding, unsafe, limited to single ecosystem|

---

## **3. Solution**

Kenobi introduces a **knowledge-first system architecture**:

- All organizational data is unified into a **knowledge layer**
- Access is mediated through **AI agents**
- Interaction occurs via **natural language and structured workflows**
- Outputs are **traceable, permissioned, and grounded**

Core capability:

```txt
Ask → Retrieve → Reason → Act → Persist
```

---

## **4. Core System Architecture**

### **4.1 Operator (Runtime Layer)**

- Headless system daemon
- Owns orchestration, permissions, lifecycle
- Manages KB, memory, and agents

---

### **4.2 Knowledge Base (Durable Layer)**

Stores:

- Entities
- Facts
- Documents
- Relationships
- Derived outputs
- Provenance metadata

Properties:

- Local-first
- Model-agnostic
- Structured + unstructured
- Permission-aware

---

### **4.3 Knowledge OS (Context & Memory Layer)**

Handles:

- Working memory
- Session continuity
- Context packaging
- State transfer across agents

Rules:

- Memory is mutable
- Knowledge is durable
- Only validated memory is promoted

---

### **4.4 Agent Layer (Execution Layer)**

Types:

- Conversational agent (orchestrator)
- Task agents (scoped execution)
- Knowledge agents (retrieval + structuring)

Constraints:

- No direct persistence
- No uncontrolled tool access
- Structured outputs only
- Operator-controlled lifecycle

---

### **4.5 Kenobi Interface (Product Layer)**

Provides:

- Natural language interface
- Structured workflows
- Visual outputs (tables, summaries, actions)
- Multi-agent orchestration surface

---

## **5. Core Capabilities**

### **5.1 Unified Knowledge Access**

Query across:

- Structured data (SQL, APIs)
- Unstructured data (docs, PDFs, emails)
- System metadata
- Agent outputs

---

### **5.2 Conversational Querying**

Examples:

- “What changed in revenue last quarter and why?”
- “Summarize all vendor anomalies in the last 6 months”
- “Generate onboarding doc for product X”

---

### **5.3 Cross-Source Reasoning**

Combines:

- Metrics
- Documents
- Historical outputs
- Contextual memory

---

### **5.4 Agent-Orchestrated Execution**

- Task decomposition
- Parallel agent execution
- Result merging
- Context preservation

---

### **5.5 Knowledge Persistence**

- Structured outputs persisted to KB
- Versioning and provenance tracking
- Controlled mutation

---

### **5.6 Permissioned Retrieval**

- Role-based access
- Row-level filtering
- Context-aware visibility
- No data leakage into prompts

---

## **6. Knowledge Lifecycle**

```txt
Ingestion
→ Parsing
→ Metadata Extraction
→ Indexing (semantic + structured)
→ Retrieval
→ Agent Reasoning
→ Output Generation
→ Memory Update
→ Promotion to Knowledge Base
→ Provenance Tracking
```

---

## **7. Output Guarantees**

Kenobi outputs are:

- **Grounded** (derived from internal data)
- **Traceable** (source-linked)
- **Permissioned** (access-controlled)
- **Structured** (not free-form hallucination)
- **Persistable** (optional KB write)

---

## **8. Primary Use Cases**

### **8.1 Enterprise Search Replacement**

- Replace fragmented internal search
- Context-aware answers instead of document lists

---

### **8.2 Conversational Analytics (BI Abstraction)**

- Query data without SQL
- Replace static dashboards for most users

---

### **8.3 Knowledge Operations Layer**

- Internal documentation generation
- Knowledge consolidation and maintenance

---

### **8.4 Compliance & Audit**

- Traceable decisions
- Source-linked outputs
- Historical reconstruction

---

### **8.5 Embedded AI Layer (B2B SaaS)**

- Customer-facing assistants
- Internal product copilots

---

## **9. Differentiation**

### **vs Knowledge Platforms (e.g. Glean)**

- Adds structured data reasoning
- Adds agent execution layer
- Adds persistence and memory

---

### **vs Conversational BI (e.g. Knowi)**

- Extends beyond structured data
- Includes unstructured knowledge + documents
- Enables cross-domain reasoning

---

### **vs Productivity Tools (e.g. Notion)**

- Not document-first
- System-first, agent-mediated architecture

---

### **vs AI Copilots (e.g. Microsoft Copilot)**

- Model-agnostic
- Not tied to single ecosystem
- Full control over data + permissions

---

## **10. Product Model**

### **10.1 Core Offering**

**Knowledgebase-as-a-Service (KaaS)**

Includes:

- Data ingestion layer
- Knowledge modeling
- Agent layer
- Kenobi interface

---

### **10.2 Add-ons**

- Domain-specific agents
- Compliance modules
- Embedded assistant SDK
- Private / on-prem deployment

---

### **10.3 Deployment Modes**

- Cloud-hosted
- VPC deployment
- Fully on-prem (regulated environments)

---

## **11. System Positioning**

Kenobi is not:

- A dashboard tool
- A document system
- A chatbot

Kenobi is:

**A knowledge execution system**

---

## **12. Future Extensions (Non-Core, Strategic)**

- Verifiable knowledge provenance (cryptographic chain)
- Cross-org knowledge verification
- Agent-to-agent trust protocols
- Autonomous execution workflows

---

## **13. Product Identity**

### **Visual System**

- Kenobi Yellow (`#FFD500`) as primary signal
- Warm, high-contrast, non-corporate UI
- Functional clarity over ornamentation

---

### **Design Principles**

- High signal density
- Minimal abstraction layers
- Immediate feedback loops
- No hidden state

---

## **14. Core Thesis**

```txt
Data systems store information.

Kenobi makes it usable.
```
# **Kenobi - Product Book v1.1**

---

## **1. Definition**

**Kenobi** is an AI-native **Context Operating System (Context OS)** that enables organizations and individuals to manage, transfer, and act on knowledge, memory, and context across models, systems, and agents through a unified interface.

```txt
Kenobi = Operator + Knowledge OS + Knowledge Base + Agent Layer + UI
```

Kenobi does not store knowledge independently.  
It is the **interaction and workflow layer** that operates on top of Operator.

---

## **2. Core Thesis**

```txt
Data systems store information.

Kenobi manages context.
```

Kenobi defines a new category:

> **Context Operating Systems (Context OS)**

Where:
- Data systems store data
- Workflow systems execute tasks
- AI copilots assist interaction

Kenobi manages:
- context
- memory
- reasoning continuity

---

## **3. Problem**

Modern systems suffer from:

- Fragmented knowledge across tools
- Loss of context across sessions and models
- Repeated re-explanation of intent
- Lack of memory continuity
- Unsafe and ungrounded AI usage

Traditional systems fail because they:

- Do not preserve context
- Do not unify memory
- Do not support multi-agent reasoning
- Do not allow model interoperability

---

## **4. Solution**

Kenobi introduces a **knowledge-first, context-driven system**:

```txt
Ask → Retrieve → Reason → Act → Persist → Transfer
```

Core ideas:
- Context is first-class
- Memory is portable
- Agents are controlled
- Knowledge is verifiable

---

## **5. Core System Architecture**

### **5.1 Operator (Runtime Layer)**

Owns:
- knowledge base
- memory
- agents
- orchestration
- permissions

Runs as:
- local daemon
- middleware layer

---

### **5.2 Knowledge Base (Durable Layer)**

Stores:
- facts
- entities
- documents
- relationships
- provenance

Properties:
- local-first
- model-agnostic
- permissioned
- durable

---

### **5.3 Knowledge OS (Context & Memory Layer)**

Handles:
- working memory
- session continuity
- context packaging
- state transfer

Rules:
- memory is mutable
- knowledge is durable
- only validated memory is promoted

---

### **5.4 Agent Layer (Execution Layer)**

Types:
- chat/orchestrator agent
- task agents
- knowledge agents

Rules:
- no direct persistence
- no uncontrolled tool access
- structured outputs only
- operator-controlled lifecycle

---

### **5.5 Kenobi Interface (Product Layer)**

Provides:
- conversational interface
- workflow abstraction
- multi-agent orchestration surface
- context control primitives

Kenobi never executes directly.  
All execution flows through Operator.

---

## **6. Chatroom Runtime Model**

Every interaction occurs inside a **Chatroom**.

A Chatroom is the atomic execution unit.

It encapsulates:
- transcript (conversation)
- intermediate representation (IR)
- memory scope
- active model
- agent topology

The Chatroom defines:
- execution boundary
- context continuity
- agent collaboration scope

---

## **7. Agent Execution Model**

Every interaction follows:

```txt
User → Chat Agent → Operator → Task Agents → Operator → Chat Agent → User
```

### **Chat Agent**
- owns conversation
- interprets intent
- delegates work
- merges outputs

### **Task Agents**
- execute scoped tasks
- return structured outputs
- have no persistence or memory ownership

### **Operator**
- mediates execution
- manages memory updates
- enforces permissions

---

## **8. Intermediate Representation (IR)**

Kenobi uses an **Intermediate Representation (IR)** instead of raw transcripts.

IR contains:
- goals
- entities
- constraints
- decisions
- open questions
- relevant context

Purpose:
- model-agnostic context transfer
- efficient prompt construction
- stable reasoning across sessions

---

## **9. Context Control Primitives**

Kenobi introduces three core operations:

### **Switch**
Move context across models.

### **Fork**
Branch a conversation into a new reasoning path.

### **Clone**
Replicate full conversational state into a new session.

These enable:
- model interoperability
- parallel reasoning
- persistent context continuity

---

## **10. Memory Scope Model**

Kenobi operates across memory scopes:

- **Local Memory** — device-level
- **Space Memory** — project/workspace level
- **Global Memory** — account-level

Memory continuity is preserved across:
- sessions
- models
- devices

---

## **11. Multi-Agent Collaboration**

Kenobi enables structured collaboration:

- parallel task agents
- controlled context sharing
- structured result merging
- traceable decision flows

Agents do not communicate directly.  
All coordination is mediated by Operator.

---

## **12. Knowledge Lifecycle**

```txt
Ingestion
→ Parsing
→ Metadata Extraction
→ Indexing
→ Retrieval
→ Agent Reasoning
→ Output Generation
→ Memory Update
→ Promotion to Knowledge Base
→ Provenance Tracking
```

---

## **13. Output Guarantees**

All outputs are:

- grounded
- traceable
- permissioned
- structured
- persistable

---

## **14. Local-First Architecture**

Kenobi is local-first:

- knowledge remains user-controlled
- no forced centralization
- sync is optional and controlled

Global awareness is achieved via:
- knowledge agents
- controlled synchronization

---

## **15. Knowledge Integrity & Provenance**

Kenobi tracks:

- source
- transformation steps
- contributing inputs
- agent execution path

Future extensions:
- cryptographic memory evolution chains
- verifiable knowledge lineage

---

## **16. Core Capabilities**

- unified knowledge access
- conversational querying
- cross-source reasoning
- agent orchestration
- knowledge persistence
- permissioned retrieval
- context transfer across models

---

## **17. Primary Use Cases**

- enterprise search replacement
- conversational analytics
- knowledge operations
- compliance and audit
- embedded AI systems
- cross-model workflows

---

## **18. Differentiation**

Kenobi differs by:

- managing context, not just data
- enabling model interoperability
- supporting multi-agent execution
- preserving memory continuity
- enabling structured reasoning

---

## **19. Product Model**

### Core:
Knowledgebase-as-a-Service (KaaS)

### Add-ons:
- domain agents
- compliance modules
- embedded SDKs

### Deployment:
- cloud
- VPC
- on-prem

---

## **20. System Positioning**

Kenobi is not:
- a chatbot
- a dashboard
- a document tool

Kenobi is:
> **A context execution system**

---

## **21. Open Design Decisions**

The following decisions remain intentionally open:

- IR schema standardization format
- Chatroom persistence model (full vs partial transcript retention)
- Sync protocol across devices and KBs
- Agent scheduling strategy (sequential vs parallel defaults)
- Model adapter standardization layer
- Provenance depth vs performance tradeoffs
- Cryptographic verification implementation approach
- Memory promotion thresholds (memory → knowledge)
- Permission enforcement granularity (row vs object vs semantic)
- UI surface (CLI-first vs desktop-first vs hybrid)

---

## **22. Product Identity**

Design principles:
- high signal density
- minimal abstraction
- no hidden state
- immediate feedback

---

## **23. Final Statement**

```txt
Kenobi makes knowledge usable,
context portable,
and reasoning continuous.
```