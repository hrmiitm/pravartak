---
title: DeepSeek Harness
description: AI agents with tools and skill as plugins.
sidebar:
  order: 1
---


# DeepSeek Harness 

> **DeepSeek Harness (`dsh`)** is an open-source agent harness from DeepSeek AI. Its central idea is simple: **the model is only one part of an agent; the harness supplies the environment, tools, memory/session machinery, permissions, skills, and execution loop that lets the model actually work.**


---

## 1. What Are We Actually Learning?

Before talking about DeepSeek Harness, separate three concepts:

- **Model** — generates reasoning and responses.
- **Agent** — a model operating in a loop with tools and state.
- **Harness** — the runtime around the model that lets the agent interact with the real world.

A useful mental model is:

```text
                 ┌─────────────────────┐
                 │       MODEL         │
                 │  "What should I do?"│
                 └──────────┬──────────┘
                            │
                     model response
                            │
                            ▼
                 ┌─────────────────────┐
                 │      HARNESS        │
                 │                     │
                 │ tools               │
                 │ files               │
                 │ shell               │
                 │ sessions            │
                 │ permissions        │
                 │ skills              │
                 │ telemetry           │
                 │ agent loop          │
                 └──────────┬──────────┘
                            │
                      real actions
                            │
                            ▼
                 ┌─────────────────────┐
                 │     ENVIRONMENT     │
                 │ code / files / OS   │
                 │ APIs / services     │
                 └─────────────────────┘
```

The model alone cannot safely and reliably perform a multi-step software task.

For example, if you ask a raw LLM:

> "Fix the failing tests in this repository."

the model can describe what it *would* do, but it does not automatically have:

- access to the repository,
- a terminal,
- a way to execute tests,
- a persistent session,
- tool schemas,
- permission checks,
- a mechanism for continuing after a tool result,
- or a structured record of what happened.

A harness provides those pieces.

---

# 2. What Is an Agent Harness?

An **agent harness** is the software layer responsible for turning an LLM into a usable agent.

A simplified agent loop looks like:

```text
User task
   │
   ▼
Build context
   │
   ▼
Ask model
   │
   ▼
Model chooses:
   ├── answer
   └── tool call
          │
          ▼
      execute tool
          │
          ▼
      get result
          │
          ▼
      update state
          │
          └──────────────► ask model again
```

This loop may execute many times before the task is finished.

### Model vs Harness

| Model | Harness |
|---|---|
| Generates tokens | Runs the agent loop |
| Reasons about the task | Gives the model tools |
| Produces tool calls | Executes tool calls |
| Uses context | Builds/manages context |
| Has learned knowledge | Connects to the current environment |
| Does not inherently own a filesystem | Provides filesystem access |
| Does not inherently run commands | Provides shell/terminal capabilities |
| Does not inherently persist sessions | Stores session state/logs |
| Usually has no approval system | Can enforce permissions |

The DeepSeek Harness documentation summarizes this idea as:

> **Agent = Model + Harness**

The model is the "soul"; the harness keeps the agent working in a real environment.

---

# 3. Why DeepSeek Harness?

DeepSeek Harness is interesting because it is designed around a particularly strong architectural idea:

> **Everything is a plugin.**

That includes capabilities that many agent frameworks treat as built-in infrastructure.

DeepSeek's architecture makes components such as:

- model adapters,
- tools,
- sessions,
- skills,
- storage,
- loops,
- sandboxes,
- scheduling,
- and UI

replaceable or composable through plugins.

This is powered by **Cordis**, the plugin framework underneath DeepSeek Harness.

That makes DeepSeek Harness particularly interesting if you want to understand **agent infrastructure rather than just use an agent application**.

---

# 4. Why "Everything Is a Plugin" Matters

Imagine a traditional application:

```text
┌─────────────────────────────────────┐
│              CORE APP               │
│                                     │
│  Model                              │
│  Tools                              │
│  Memory                             │
│  Session                            │
│  Agent Loop                         │
│  UI                                 │
└─────────────────────────────────────┘
```

If you want to change something, you often modify the core.

DeepSeek Harness instead aims for:

```text
                  Cordis
                    │
       ┌────────────┼────────────┐
       │            │            │
    Model         Tools       Sessions
       │            │            │
     Skill       Sandbox       UI
       │            │            │
       └────────────┼────────────┘
                    │
                 Agent
```

Each capability registers itself with the shared runtime.

Conceptually:

```text
Plugin
  │
  ├── provides services
  ├── listens to events
  ├── registers capabilities
  └── can be mounted/unmounted
```

This is much closer to an operating-system/plugin architecture than a single monolithic agent program.

---

# 5. What Is Cordis?

**Cordis** is the plugin framework/kernel used by DeepSeek Harness.

You do not need to understand Cordis before using `dsh`, but it becomes important once you want to understand the architecture or build plugins.

Cordis provides a shared context where plugins can contribute:

- services,
- typed events,
- capabilities,
- registrations,
- and reversible effects.

A simplified view:

```text
                 Cordis Context
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     ctx.llm        ctx.tools      ctx.sessions
        │              │              │
   model adapter    tool registry   session log

        │              │              │
        └──────────────┼──────────────┘
                       │
                    Agent
```

The important idea is that plugins do not need to modify a giant central loop just to add behavior.

---

# 6. The DeepSeek Harness Architecture

At a high level:

```text
                    ┌──────────────────┐
                    │      User        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │       UI / CLI    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │      Agent       │
                    │      Loop        │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          System          Tools          Session
           Prompt         Registry          Log
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                         LLM Adapter
                             │
                             ▼
                           Model
```

The actual architecture is more modular than this diagram but it is good to understand it.


---

# 7. What Can DeepSeek Harness Do?

Once configured, a Harness agent can perform multi-step tasks such as:

- inspect repositories,
- read files,
- edit files,
- run commands,
- run tests,
- maintain plans,
- delegate work,
- use skills,
- maintain durable sessions,
- interact with configured tools,
- operate under permission policies,
- and work through repeated model/tool cycles.

For example:

```text
User:
"Find why the API tests are failing and fix them."

Agent:

1. Inspect repository
2. Find test files
3. Inspect implementation
4. Run tests
5. Read error
6. Modify source
7. Run tests again
8. Verify result
9. Explain changes
```

The important point is that the harness coordinates this process.

---

# 8. Installing DeepSeek Harness

DeepSeek Harness provides an npm-based quick start.

You need Node.js.

Run:

```bash
npx @deepseek-ai/dsh web
```

This starts the Web UI.

By default, it is served at:

```text
http://127.0.0.1:3080
```

The exact startup behavior can vary by environment.

For a source checkout:

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness

pnpm install
pnpm run build
pnpm dsh web
```

### Quick-start mental model

```text
npx
 │
 ▼
@deepseek-ai/dsh
 │
 ▼
dsh web
 │
 ▼
Harness server
 │
 ▼
Web UI
```

---

# 9. Running DeepSeek Harness

The simplest run is:

```bash
npx @deepseek-ai/dsh web
```

After startup, open the URL printed by the program.

You then:

1. Configure a model.
2. Choose a workspace.
3. Start a session.
4. Give the agent a task.

Example task:

```text
Summarize this repository and identify its main packages.
```

A more useful task:

```text
Inspect this repository, run the tests, identify the failing tests,
and fix the implementation without changing the test expectations.
```

The Harness can then use the available capabilities to perform the task.

---

# 10. Workspace: Where Does the Agent Work?

The Harness needs a workspace.

Think of the workspace as the agent's working directory:

```text
workspace/
├── src/
├── tests/
├── package.json
├── README.md
└── ...
```

The agent can then use its filesystem and command capabilities against that workspace, subject to the active permission policy.

This is important:

> **A model does not automatically have access to your entire computer.**

The harness decides what environment the agent can interact with.

---

# 11. Configuring a Model

Open:

```text
Settings → Models
```

The current Web UI lets you configure the DeepSeek provider by entering a DeepSeek API key.

After saving, the configured model route becomes available without restarting the server.

The model configuration system also supports other providers and custom OpenAI-compatible endpoints.

---

# 12. Model Provider vs Model

This distinction matters.

A **provider** answers:

> "Where does this model come from and how do I communicate with it?"

A **model** answers:

> "Which specific model should I call?"

For example:

```text
Provider
  └── DeepSeek
       ├── Model A
       ├── Model B
       └── Model C
```

Or:

```text
Provider
  └── OpenAI-compatible endpoint
       ├── local-model
       └── another-model
```

DeepSeek Harness separates the model-facing interface from the provider-specific implementation through an LLM adapter.

---

# 13. Can We Use Another Model?

Yes, this is one of the interesting consequences of the plugin architecture.

DeepSeek Harness is not conceptually hard-wired to one model.

The provider/model configuration supports other providers and custom OpenAI-compatible endpoints.

For example, a locally hosted model could conceptually look like:

```text
DeepSeek Harness
       │
       ▼
OpenAI-compatible endpoint
       │
       ▼
Local inference server
       │
       ▼
Your model
```

The exact model must support the interface/capabilities expected by the configured adapter.

For a custom OpenAI-compatible server, you generally need:

```text
Base URL
API credential (if required)
Model name
Supported modalities/capabilities
```

Some endpoints expose `/models`, allowing automatic discovery; others require models to be entered manually.
---

# 14. What Is a Skill?

A **skill** is reusable instruction/context that teaches an agent how to perform a particular kind of work.

Think of it as:

```text
Skill = reusable procedure + instructions + optional resources
```

For example:

```text
code-review
documentation-writing
security-audit
database-migration
research-paper-analysis
```

A skill is not necessarily another model.

It is closer to a reusable operating procedure for the agent.

---

# 15. Skill vs Tool

This distinction is extremely important.

### Tool

A tool gives the model an **ability**.

Example:

```text
filesystem.read()
shell.execute()
web.search()
```

### Skill

A skill gives the model **guidance for using abilities**.

Example:

```text
"Before changing authentication code:
1. inspect the current auth flow
2. identify trust boundaries
3. run security tests
4. never expose credentials"
```

So:

```text
Tool  = WHAT the agent can do

Skill = HOW / WHEN the agent should approach a type of work
```

A useful analogy:

```text
Tool  → screwdriver
Skill → instructions for assembling the furniture
```

---

# 16. How Skills Work Internally

DeepSeek Harness has a skill capability family.

Important pieces include:

```text
ctx.skills
   │
   ├── skill providers
   │
   ├── local filesystem skills
   │
   └── packaged/other skill providers
            │
            ▼
       skill registry
            │
            ▼
       skill tool
            │
            ▼
          Model
```

The filesystem skill provider scans configured skill roots and discovers skills.

Skills can be:

```text
<name>/SKILL.md
```

or:

```text
<name>.md
```

The directory form is useful when the skill needs supporting files.

---

# 17. Where Do Skills Live?

The filesystem provider can scan locations including:

```text
~/.dsh/skills/
```

and:

```text
.dsh/skills/
```

There is also support for:

```text
~/.agents/
```

and custom skill directories through configuration.

A common structure is:

```text
my-project/
└── .dsh/
    └── skills/
        └── security-review/
            └── SKILL.md
```

Or a user-level skill:

```text
~/.dsh/
└── skills/
    └── security-review/
        └── SKILL.md
```

Project-level skills are useful when the skill belongs specifically to one repository.

User-level skills are useful when you want to reuse the skill across projects.

---

# 18. Creating Your First Skill

Create:

```text
.dsh/skills/security-review/SKILL.md
```

Put YAML frontmatter at the top:

```markdown
---
name: security-review
description: Review application code for common security vulnerabilities.
---

# Security Review

When reviewing security-sensitive code:

1. Identify trust boundaries.
2. Identify user-controlled input.
3. Check authentication and authorization.
4. Check secret handling.
5. Check injection risks.
6. Check filesystem and command execution.
7. Run relevant tests.
8. Explain findings with evidence.
```

The required frontmatter fields are:

```yaml
name: security-review
description: Review application code for common security vulnerabilities.
```

The name must use **kebab-case**.

---



# 19. A Better Real-World Skill

For example, create:

```text
.dsh/skills/research-paper-review/SKILL.md
```

with:

```markdown
---
name: research-paper-review
description: Analyze research papers for problem definition, novelty, methodology, experiments, limitations, and reproducibility.
---

# Research Paper Review

Follow this procedure:

## 1. Problem

Identify:
- the problem being solved
- why it matters
- the assumptions

## 2. Prior Work

Identify:
- closest existing approaches
- what the authors claim is different
- whether the novelty claim is convincing

## 3. Method

Explain:
- architecture
- data
- training procedure
- evaluation setup

## 4. Results

Check:
- datasets
- baselines
- metrics
- ablations
- statistical significance where relevant

## 5. Weaknesses

Look for:
- unsupported claims
- missing baselines
- data leakage
- weak evaluation
- reproducibility problems

## 6. Final Assessment

Return:

- Problem
- Contribution
- Novelty
- Method
- Evidence
- Weaknesses
- Questions
- Reproducibility
```

Now the agent has a reusable research workflow.

---

# 20. Plugins vs Skills

Do not confuse these.

## Skill

Usually:

```text
Instructions
+ workflow
+ supporting resources
```

## Plugin

A plugin can change the actual runtime.

A plugin can provide things such as:

```text
new model adapter
new tool
new storage provider
new filesystem provider
new event handler
new UI component
new scheduler
new sandbox
new capability
```

Think:

```text
Skill
  = teaches the agent

Plugin
  = extends the agent runtime
```

---

# 21. Why the Plugin Architecture Is Powerful

Suppose you want a new model provider.

A tightly coupled framework might require:

```text
modify core
   ↓
modify model manager
   ↓
modify configuration
   ↓
modify UI
   ↓
modify tests
```

With a plugin-oriented architecture, the goal is closer to:

```text
Build provider plugin
       │
       ▼
Register adapter on ctx.llm
       │
       ▼
Harness can use provider
```

DeepSeek's architecture explicitly defines:

```text
Add a model provider
→ register its adapter on ctx.llm
```

Similarly:

```text
Add a model-facing capability
→ register on ctx.tools
```

This is the core architectural advantage.

---

# 22. A Practical Mental Model

Remember these four layers:

```text
┌─────────────────────────────────────┐
│             MODEL                   │
│ "Reason / decide"                   │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│             HARNESS                 │
│ "Run the agent"                     │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│             PLUGINS                 │
│ "Extend capabilities"               │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│             SKILLS                  │
│ "Guide behavior/workflows"          │
└─────────────────────────────────────┘
```

More precisely, skills and plugins are not simply one above the other; they extend different parts of the system.

A better conceptual diagram is:

```text
                         MODEL
                           │
                           ▼
                       HARNESS
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Plugins           Tools           Sessions
          │                │                │
          └────────────────┼────────────────┘
                           │
                        Skills
                           │
                           ▼
                     Agent behavior
```

---





---

# 23. One Complete Example

Suppose you have:

```text
my-project/
├── src/
├── tests/
└── .dsh/
    └── skills/
        └── secure-coding/
            └── SKILL.md
```

Start Harness:

```bash
cd my-project
npx @deepseek-ai/dsh web
```

Configure the model.

Choose:

```text
my-project/
```

as the workspace.

Then ask:

```text
Review this project for security problems and fix the
high-confidence issues. Run the tests after making changes.
```

The conceptual execution is:

```text
User request
      │
      ▼
Agent
      │
      ├── discover relevant skill
      │
      ├── load secure-coding guidance
      │
      ├── inspect files
      │
      ├── identify issue
      │
      ├── edit code
      │
      ├── run tests
      │
      └── report result
```

This demonstrates the relationship between:

```text
Model
Harness
Skill
Tools
Workspace
Session
```

---

# 24. DeepSeek Harness in One Sentence

If you remember only one thing:

> **DeepSeek Harness is the runtime that turns an LLM into a persistent, tool-using agent, and its plugin architecture makes the runtime itself modular and replaceable.**

And if you remember two:

> **A tool gives the agent an ability. A skill gives the agent a reusable way of performing a class of work.**

---

# 25. Architecture Cheat Sheet

| Concept | Meaning |
|---|---|
| Model | Generates reasoning/output |
| Agent | Model operating through a harness |
| Harness | Runtime that coordinates model, tools, state and environment |
| Cordis | Plugin framework underneath DSH |
| Plugin | Runtime extension |
| Tool | Executable capability exposed to the agent |
| Skill | Reusable instructions/workflow |
| Session | Durable record of agent activity |
| Step | Model request + associated tool activity |
| Turn | Sequence of steps for a unit of work |
| Workspace | Environment/files the agent is allowed to operate on |
| Provider | Backend used to access models |
| LLM adapter | Bridges a provider/model to the harness LLM interface |

---

# 26. Useful Official Resources

- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- DeepSeek Harness website: https://deepseek.com/harness/en/
- Architecture: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
- User guide: https://github.com/deepseek-ai/deepseek-harness/tree/master/docs/user/guide
- Model providers: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md
- Skills subsystem: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md
- Python SDK: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/python-sdk.md
- LLM adapter cookbook: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cookbook/adding-an-llm-adapter.md

---

# 27. Final Mental Picture

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │   HARNESS   │
                    │             │
                    │ Agent Loop  │
                    │ Sessions    │
                    │ Permissions │
                    │ Context     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
            MODEL        TOOLS       SKILLS
              │            │            │
              │            │            │
              ▼            ▼            ▼
          Reasoning     Actions      Guidance
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                      ENVIRONMENT
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
            Files        Shell        APIs
```

That is the core idea behind DeepSeek Harness.

**Model = reasoning**

**Harness = execution**

**Tools = abilities**

**Skills = reusable procedures**

**Plugins = extensibility**

**Sessions = durable state/history**

**Cordis = the plugin architecture that ties the system together**
