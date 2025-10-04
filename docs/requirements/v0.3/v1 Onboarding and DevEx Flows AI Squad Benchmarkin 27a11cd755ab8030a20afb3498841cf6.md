# v1 Onboarding and DevEx Flows: AI Squad Benchmarking Tool

Created by: Brock Butler
Created time: September 26, 2025 6:57 PM
Category: Requirements, User Flows
Last edited by: Brock Butler
Last updated time: September 27, 2025 4:54 PM
Parent item: v1 (https://www.notion.so/v1-27a11cd755ab80efa99cfad4cd59780d?pvs=21)

# Agentic Framework Benchmark Tool: Approach, Rationale, Requirements & Onboarding Architecture

## Vision & Strategic Priorities

- Make onboarding, benchmarking, and config management fast, scalable, and accessible via an agent-driven CLI experience.
- Treat the onboarding/config UX—and the agentic workflows that deliver it—as product-code: versioned, reproducible, and extensible by core contributors and the community.
- Guarantee deterministic, auditable, and collaborative workflows for every user—from absolute beginner to R&D super-user.

## North Star Goal

**Anyone (Brock, an engineer, or an open source dev) can:**

- Discover the project and get a working environment
- Run an out-of-the-box benchmark in minutes
- Clearly understand the core concepts, their next options, and how to add/change things
- Walk away thinking “that was smooth,” not “WTF?”

## Problem Statement & Context

Modern dev teams face an explosion of AI agent frameworks and orchestration platforms, each with unique strengths, quirks, and trade-offs. Today, there is no credible, reproducible, or developer-friendly way to benchmark, compare, and iterate agent workflows as rapidly as the technology and user expectations are evolving.

**Key challenges:**

- Teams waste weeks wrestling with incompatible APIs, YAML hell, and hidden conventions—before running a single test on their own real code/docs.
- Benchmarking is either “demo-ware” (curated, narrowly scoped, not transparent) or “science project” (too technical, too slow, inaccessible to new users).
- There’s no actionable, transparent answer to “Which framework, agent, or prompt works best for my use-case—in my environment, with my data?”

---

## Strategic Solution

**Our answer:**

A fully agent-driven CLI + catalog system where users can install, describe their goal, and—through a conversational, human-in-the-loop process—get working benchmarks, tasks, and comparison results in minutes. The workflow is transparent, reproducible, and extensible, and all actions are logged and versioned.

**Why this approach?**

- It leverages the power (and reality) of agentic frameworks—demonstrating their value by making them the onboarding and config interface.
- It lowers barriers to entry with guided flows, but preserves all “super-user” power and manual control for advanced use, debugging, and R&D.
- The system keeps provenance, errors, iterated changes, and user approval at the center—making every outcome auditable and collaborative.
- It is both “batteries-included” for new users, and a composable toolkit for teams and open-source contributors.

---

## Success Criteria

### **Big-picture:**

- **Time to first meaningful benchmark:** New users reach a successful first custom task run and credible results in under 10 minutes, every time.
- **Repeatable and Trustworthy:** Every change, agent interaction, and config edit is logged, diffed, and can be replayed. Outputs are never “magic”—there’s always a clear record of the “why” and “how.”
- **Extensible and Community-Ready:** Contributors can build new onboarding agents, tasks, and rubrics as plugins and PRs, and every user can easily “fork” or adapt entity files to their stack and style.
- **No lock-in:** Nothing is hidden, silent, or proprietary. Manual editing is always possible, but never forced. All agent and onboarding workflows are open for inspection, criticism, and improvement.
- **Safety, rollback, and recovery:** Any error, ambiguity, or failed onboarding step leaves the user with a safe checkpoint and a provable way to start over, escalate, or publish for help.

---

## Alternative Solutions Considered

- **Pure CLI/config tool:** Too daunting for new users, error-prone for long YAML merges, and misses chance to “show, don’t tell” the value of agents in driving real workflows.
- **Web UI builder:** Adds infra/deploy complexity, splits the source of truth, and is less reproducible/headless for CI or team-centric adoption.
- **Multiple simultaneous onboarding agent frameworks:** Hard to maintain, would fragment UX, and undermine reproducibility; we’ll add plugins when/if contributor traction warrants.

**Choice rationale:**

A single, orchestrated agentic onboarding workflow is robust enough for present needs, easier to version/test, and keeps complexity tractable.

## Guiding Design Decisions

### I. Single Onboarding Workflow with Orchestrated Sub-Agents

- **Decision:** One default “onboarding agent” workflow will orchestrate a collection of sub-agents—mirroring modern “conductor plus expert agents” architectural patterns, e.g. as used in Claude Code or CrewAI.
- **Rationale:** Keeps user focus and reproducibility tight, accommodates complexity via specialization, and aligns with how most frameworks already work under the hood.

### II. ALL Actions Are Tracked—Change Log as JSONL

- **Decision:** Every step, action, and config change (both agent and human) is logged. Change logs are machine-parseable (JSONL) and include: agent workflow/versions, human username (if known), agent interaction history, and diffs. These can be replayed, mutated, and PR’d to the catalog/community.
- **Rationale:** This guarantees determinism, enables “replay” for both debugging and teaching, and supports rich provenance.

### III. Checkpointing & Rollback

- **Decision:** Automatic checkpoints are created after every significant onboarding/config generation step (e.g., after agent scaffolds a new Task or Rubric). Users can “rewind” one step at a time, or jump back to any named checkpoint. Backtracking will always present the state at that point and allow the flow to be restarted from there.
- **Rationale:** Enables “undo”/“reset” flows, handles agent/human error, and preserves the journey for postmortem or troubleshooting.

### IV. Diff, Approval, and Human-in-the-Loop

- **Decision:** Before any change is committed, agents present a detailed, “what’s about to change” diff; users can accept, reject, or request a redo. The user intent is summarized and included in the change log.
- **Rationale:** Builds trust, gives transparency, and offers efficient error correction.

### V. Onboarding Agent Plugins—Core vs. Peripheral

- **Decision:** Plugins can be contributed via PRs; only core-approved go into the official catalog, but anyone can add their own by dropping files into a “plugins” directory. Plugins are sandboxed: they can only perform actions defined by a minimal, extensible contract (no arbitrary code exec out-of-the-box).
- **Rationale:** Keeps core stable and safe, while enabling experimentation and extension at the edges.

### VI. Super-user Mode as Clean Fallback

- **Decision:** User can exit agentic onboarding at any checkpoint (e.g. by typing “exit” or selecting “manual edit”). On exit, a checkpoint is made. Any further YAML/config editing is explicitly tracked (“manual mode”). Super-user modifications must pass schema validation (and CI) before being accepted (esp. for PRs).
- **Rationale:** Ensures there’s always an escape hatch for advanced users or error recovery, with continued changelog support.

### VII. Metadata, Provenance, and Library Structure

- **Decision:**
    - **Catalog:** `/catalog/tasks/`, `/catalog/rubrics/`, etc. contains system-provided, versioned, docs-rich YAML entities.
    - **User Library:** `/user/tasks/`, `/user/rubrics/` receive all agent-generated, human-edited or forked entities, with metadata:
        - Source (catalog/user)
        - `created_by` (agent + version, username)
        - `agent_workflow_id`
        - Change log (intent, actions, diffs)
- **Rationale:** Transparency, extensibility, and supports “publish/PR back” workflows.

### VIII. Publishing and Community Contribution

- **Decision:** CLI supports “bench publish” (to a public registry or PR), and “bench add plugin” (to overlay new onboarding agents or skills). Contribution to core requires PR and code review; plugins are community-sourced and labeled accordingly.
- **Rationale:** Frictionless collaboration, but robust protection for the core set.

---

## Requirements Detail

### Requirements (Non-Negotiable)

1. **Agentic Onboarding CLI** walks users through setup, config, and entity generation as a single workflow—delegating to sub-agents as needed.
2. **Every step is logged** (JSONL), including all agent actions, user inputs, diffs, and intent summaries.
    - Changlogs attached to each user-entity file; reproducible and replayable.
3. **Automatic checkpoints** are created; users can rewind one step or to any prior checkpoint anytime.
4. **Prior to committing any config/entity** change, user sees a diff, can accept, reject, or speak/type desired changes for agent to try again.
5. **User can opt-out (“super-user mode”)** to directly edit YAML/spec files, at which point provenance metadata is continued, and CI validates on any PR/submission.
6. **Plugin onboarding/extension system** allows new onboarding workflows/agents to be loaded, but plugins are sandboxed and follow minimal safe contracts.
7. **Entity metadata:** Every task, rubric, agent, prompt, and onboarding workflow includes:
    - Source (catalog/user/plugin)
    - Authorship info (human/agent/workflow)
    - Version
    - Provenance pointer (parent, parent version)
    - Full changelog (with summary of each change)
8. **Publishing and contribution:**
    - CLI command for “bench publish” to a public registry, and classic PR flow for core updates.
    - Peripheral (plugin) contributions are labeled and can be discovered via tags.
9. **User-facing terminology:**
    - “Catalog” for system/library; “User Library” for all derived/forked/modified items.
    - “Onboarding Agent” or “Onboarding Workflow” for the core agentic interface; “Plugin” for user/community overlays.
10. **Provenance and replay:** At any checkpoint, the full state, logs, and conversation can be exported, shared, re-run, or PR’d.

---

## Minimum File/Folder Structure

```
catalog/
  tasks/
    onboarding-doc.yaml
  rubrics/
    doc-onboarding.yaml
  agents/
    doc-writer.yaml
  onboarding_workflows/
    default_onboarding_agent.yaml
  ...
user/
  tasks/
    custom-onboarding-doc.yaml
  rubrics/
    custom-onboarding.yaml
  agents/
    my-doc-writer.yaml
  onboarding_logs/
    changelog_2024-05-01_001.jsonl
plugins/
  onboarding_agents/
    research-onboarding.yaml

```

*All files versioned and include metadata anchoring origin, authorship, changelog, and any parent template.*

---

## Sample Schematic Onboarding Flow

1. **User starts onboarding:**
    - `bench onboarding`
    - Onboarding Agent: “Welcome! What do you want to benchmark today? (select or describe)”
    - User: “I want to test onboarding docs for Python backend engineers.”
2. **Agentic selection:**
    - Shows top relevant tasks, asks user to pick or refine.
    - User selects a task, agent fetches matching rubrics, frameworks, agents, and prompts.
3. **Approval cycles:**
    - Agent: “Here’s a proposed config change/diff for the task. (Shows key lines/fields)”
    - User: “I need the test to only accept Markdown output.”
    - Agent: Updates config, shows new diff.
    - User: “Yes, accept.”
4. **Checkpoint created, change logged.**
5. **Continue agentic iteration (for rubrics, frameworks, etc)—each step checks for approval, allows “back,” or switches to manual edit.**
6. **User says “exit” or “switch to manual.”**
    - Agent: “Checkpoint created! You can edit any file in /user/ and re-enter onboarding at any time. Don’t forget to validate before running.”
7. **On run, full provenance and changelog attached.**

---

### Next Steps (After Requirements)

**1. Scripted onboarding flows:**

- Prototypes of agent-led dialog covering each entity (task, rubric, agent, etc), checkpoints, approval, and diffs.

**2. Metadata fields & validation rules:**

- Exactly what must exist in every agent-generated user file for full provenance and playability.

**3. Contributor documentation:**

- Canonical “add plugin,” “fork entity,” “propose PR” guides; sample onboarding agent plugin structure; community and core contribution flows.

**4. PR/Publishing flow:**

- Design of “bench publish” and/or CLI-driven PR submission including metadata trails, core vs plugin/contributor track, and review criteria.

## Appendix: Example Dialogue-Driven Flow

### 0. Setup (Start/Initialize)

**User:**

`bench onboarding`

**Onboarding Agent (Orchestrator):**

Hi Brock! I’ll guide you through setting up your first benchmark.

What kind of benchmark or experiment would you like to run?

(Choose from catalog: [Code Bugfix], [Feature Addition], [Documentation], or describe your own goal)

---

### 1. Task Selection & Customization

**User:**

I want to create a benchmark for onboarding documentation for backend engineers.

**Onboarding Agent:**

Great! I found 3 relevant tasks in the catalog:

1. Onboarding Guide (docs-onboarding-v1)
2. API Quickstart Doc (api-quickstart-v1)
3. End-to-end Developer Onboarding (dev-onboarding-e2e-v2)
Would you like to select one to start? (or describe more/less, or see details for any option)

**User:**

Show me more about #1.

**Onboarding Agent:**

[Prints YAML summary for docs-onboarding-v1, plus description/rubric.]

Would you like to use this as your starting point, or customize some fields?

**User:**

Change the target audience to “Python developers” and add a “Required Tools” section.

**Sub-Agent (Task Editor):**

Updated preview (diff):

- `inputs.target_audience: “Python developers”`
- `sections += “Required Tools”`

[Shows YAML diff.]

Accept these changes? (accept / retry / back / see full diff / manual edit)

**User:**

Accept.

**Onboarding Agent:**

Checkpoint saved.

---

### 2. Rubric/Measure Selection & Approval

**Onboarding Agent:**

Here are the current rubrics/measures for this task:

- Clarity (1-5)
- Completeness (1-5)
- Formatting (1-5)

Would you like to add, remove, or edit any metrics? (You can add measures like “Token Efficiency” or “Manual Human Review.”)

**User:**

Add “Domain Specificity” (1-5).

**Sub-Agent (Rubric Editor):**

Proposed addition:

- `rubric += Domain Specificity (1-5): Is it tailored for backend/tooling context?`

[Shows full rubric diff.]

Accept, retry, or back?

**User:**

Accept.

**Onboarding Agent:**

Checkpoint saved.

---

### 3. Framework & Agent Selection

**Onboarding Agent:**

Select frameworks to benchmark:

[✅] CrewAI

[✅] Haystack

[ ] LangGraph

[ ] LlamaIndex

And here are recommended documentation-writer agents from the catalog:

1. doc-writer-v2 (Markdown, generic)
2. doc-mentor-v3 (more conversational)
Pick one or both, or customize an existing agent?

**User:**

Let’s use both.

**Onboarding Agent:**

Would you like to review, modify, or just use both as-is?

**User:**

Show me doc-mentor-v3’s prompts.

**Sub-Agent (Agent Inspector):**

[Prints agent and prompt YAML, shows differences.]

Edit prompt or proceed?

**User:**

Proceed.

**Onboarding Agent:**

Checkpoint saved.

---

### 4. Tool/Rule Selection

**Onboarding Agent:**

Recommended tools for this benchmark:

- Markdown Formatter
- Internal Reference Fetcher

Recommended rules to enforce:

- No Internal Links
- Output must be Markdown

Add/remove any?

**User:**

Add “No Unapproved Abbreviations” rule.

**Sub-Agent (Rule Agent):**

Proposed diff:

- `rules += No Unapproved Abbreviations (code/rule-no-abbr-v1)`

Diff and rule summary shown. Accept, retry, or back?

**User:**

Accept.

**Onboarding Agent:**

Checkpoint saved.

---

### 5. Final Diff/Approval and Execution

**Onboarding Agent:**

Here’s a summary of your complete benchmark config changes since the last checkpoint (shows aggregated diff for Task, Rubric, Agent, Rule):

[Unicode or color-code diffs inline.]

Ready to:

- [ ]  Accept and run this benchmark
- [ ]  Change something
- [ ]  Rewind to a previous step
- [ ]  Exit to manual edit

**User:**

Run benchmark.

**Onboarding Agent:**

Benchmark launched. Your config and all change logs/checkpoints are in `/user/`—you can view or publish them later. Watch progress or type `bench status` for a live update.

---

### 6. During/After Execution—Explore and Replay

**Onboarding Agent:**

Benchmark complete! Here are your results:

- Framework performance
- Evaluation scores
- Token/cost breakdown
- Any rubric/human/LLM review results
- Download/share full changelogs, YAMLs, or diffs

Would you like to publish your config, start another experiment, or exit?

---

### Additional User Controls

- `back`: Rewind one step.
- `go to checkpoint N`: Jump to a saved checkpoint.
- `undo`: Undo last human/agent action.
- `explain diff`: Get a plain-English summary of what’s changed.
- `exit`: Enter super-user mode (manual YAML edit).
- `bench publish`: Share for review/PR.

---

**This flow lets users:**

- Never get stuck—always can rewind/exit.
- See, review, and verify every change before anything is committed.
- Have a full provenance trail for every agent+human action.
- Combine conversational agentic setup with fallbacks for power-users and contributors.

---

**Ready for:**

- Required metadata/validation spec for agent-generated files
- Contributor plugin docs/requirements
- PR/publish flow details

Is this detailed, “real-world” enough for the agentic onboarding flow? Any tweaks before I move on to the next pieces?

## Appendix: Required Metadata & Validation Spec for Agentic Benchmark Entities

A clear, concrete metadata and validation blueprint for agent-generated files—so that both agents and human editors produce artifacts that are always reproducible, auditable, and programmatically checkable. 

### Universal Metadata (All Major Entities)

All entity/config files (task, agent, rubric, rule, plugin, onboarding agent, etc) **must** include these top-level fields:

```yaml
id: <UUID or globally unique string>
version: <semver, e.g., "1.0.0">
entity_type: <task|agent|rubric|rule|plugin|onboarding_agent|framework|diff|...>
created_at: <ISO datetime>
created_by:
  human: <username|email|GH handle|anon>
  agent: <agent_id, version>
  origin_workflow: <agentic_onboard_workflow_id, version>
provenance:
  source: <catalog|user_library|plugin|external>
  parent_id: <optional, id of base/forked template>
  parent_version: <if forked, version>
  changelog:
    - timestamp: <datetime>
      author: <username|agent>
      action: <"created"|"modified"|"reviewed"|"forked"|"approved"|"auto_generated">
      reason: <free text, include user prompt/summarized user intent if available>
      diff: |
        <actual YAML/JSON diff in unified style>

```

**Validation Rules:**

- `id` and `version` are required, unique per entity.
- `entity_type` must be one of an enumerated list; agents and onboarding agents must never be confused.
- `created_at` is required.
- `created_by` required; must include at least one of human or agent.
- `provenance.source` required. If forked, must reference parent id/version.
- `changelog` must be non-empty and append-only; each entry must have all fields.

---

### Entity-Specific Metadata

### Task

- `inputs:` must match a registered TaskType schema; non-required fields must default to null or documented default.
- `evaluation_type:` one or more values from the evaluations registry.
- `expected_artifact_types:` must use valid artifact_type enums.
- Referenced rubrics, rules, etc, must exist as valid versions.

### Agent

- `role:` from controlled enum.
- `prompt_ids, tool_ids, rule_ids:` all must reference known id/version combos; all must exist in catalog or user library.
- `config:` must match allowed keys/types for agent role.

### Rubric

- `criteria:` must each include `dimension`, `scale` (with min/max), and clear `description`.
- If rubric references an external checklist or scoring guide, it must have a `rubric_id`, `version`, and link.

### Onboarding Agent/Workflow

- `workflow_steps:` array of action/intent steps, each with required sub-agent (id/version), inputs, and outputs.
- Must include a minimal suite of FAQs, fallbacks, and recovery tickets.

### Plugin

- `plugin_type:` must be restricted—cannot escalate to arbitrary code execution without explicit admin permission.
- Must always reference the entities it will override or extend.

### Diff, Evaluation, Artifact

- All must reference correct entity ids/versions, and pass structure/type checks (e.g., diff.artifact_ids all exist; evaluations' source_artifact_ids exist, and evaluation_type matches schema).
- Diffs and evaluations must specify which checkpoints/versions they apply to.

---

### Example: Agent Entity Metadata

```yaml
id: agent-doc-writer-v2
version: 2.2.0
entity_type: agent
created_at: 2024-05-02T09:01:00Z
created_by:
  human: brock.butler
  agent: onboarding-orchestrator:1.4.2
  origin_workflow: onboarding-main:1.3.0
provenance:
  source: user_library
  parent_id: agent-doc-writer-template
  parent_version: 1.1.0
  changelog:
    - timestamp: 2024-05-02T09:01:00Z
      author: onboarding-orchestrator:1.4.2
      action: created
      reason: "Initial YAML scaffolding from catalog template."
      diff: |-
        + id: agent-doc-writer-v2
        + role: documentation_writer
        + config: { ... }
    - timestamp: 2024-05-02T09:03:30Z
      author: brock.butler
      action: modified
      reason: "Changed prompt to conversational doc-writing style."
      diff: |-
        - prompt_ids: [prompt-system-doc]
        + prompt_ids: [prompt-system-doc-bold]

```

---

### Machine Validation Contract (CI/CLI/Agent Rules)

- All required fields at top-level.
- No references to missing or unregistered id/version for related entities (tasks → agent, agent → prompt, etc).
- All referenced YAML files exist, are validated, and have provenance.
- All changelog diffs are well-formed.
- All modified entities auto-bump their version (semantic rules enforced).
- Plugins are checked for security and scope according to allowed actions.

---

### Human Validation/Review Criteria

- Changelog “reasons” are descriptive and useful.
- Design intent for each entity is commented if non-obvious.
- Entities lacking changelog or misreferenced entities are flagged for review and cannot be published/PR’d to core.

---

### Usage

- All `bench` CLI, agentic onboarding flows, and manual edits must maintain the integrity of this metadata.
- Failed validation blocks run, warnings can be displayed but must not allow silent or half-logged changes.
- Any entity (task, agent, rubric, plugin) not meeting the full metadata/validation contract cannot be published, merged, or executed, except in super-user/manual override/debug mode.

---

### JSON Schema

Here’s a JSON Schema that expresses the required metadata and validation logic for all agent‑generated entities. This top-level schema is designed for use with Task, Agent, Rubric, Plugin, Onboarding Agent Workflow, and extends with entity-specific sub-schemas where needed.

This schema can be used for:

- agentic onboarding validation,
- super-user/manual YAML validation,
- CI pipeline checks for entity files and PRs,
- agent/workflow auto-generation guarantees.

---

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agentic Benchmark Entity",
  "type": "object",
  "properties": {
    "id": { "type": "string", "description": "Globally unique ID (UUID or slug)" },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$", "description": "Semantic version (major.minor.patch)" },
    "entity_type": {
      "type": "string",
      "enum": [
        "task", "agent", "rubric", "rule", "plugin", "onboarding_agent", "framework", "diff", "artifact", "evaluation"
      ]
    },
    "created_at": { "type": "string", "format": "date-time" },
    "created_by": {
      "type": "object",
      "properties": {
        "human": { "type": "string", "description": "Username, email, or handle of human initiator" },
        "agent": { "type": "string", "description": "Agent ID and version" },
        "origin_workflow": { "type": "string", "description": "Onboarding workflow ID, agent version" }
      },
      "anyOf": [
        { "required": ["human"] },
        { "required": ["agent"] }
      ],
      "additionalProperties": false
    },
    "provenance": {
      "type": "object",
      "properties": {
        "source": { "type": "string", "enum": ["catalog", "user_library", "plugin", "external"] },
        "parent_id": { "type": "string" },
        "parent_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "changelog": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "properties": {
              "timestamp": { "type": "string", "format": "date-time" },
              "author": { "type": "string" },
              "action": {
                "type": "string",
                "enum": ["created", "modified", "reviewed", "forked", "approved", "auto_generated"]
              },
              "reason": { "type": "string" },
              "diff": { "type": "string" }
            },
            "required": ["timestamp", "author", "action", "reason", "diff"],
            "additionalProperties": false
          }
        }
      },
      "required": ["source", "changelog"],
      "additionalProperties": false
    }
    // --- ENTITY-SPECIFIC FIELDS GO BELOW ---
  },
  "required": [
    "id", "version", "entity_type", "created_at", "created_by", "provenance"
  ],
  "allOf": [
    // Entity-specific extensions (examples below--these would be referenced via $ref in real use)
    {
      "if": { "properties": { "entity_type": { "const": "task" } } },
      "then": {
        "properties": {
          "inputs": { "type": "object" },
          "evaluation_type": {
            "type": ["array", "string"], "items": { "type": "string" }
          },
          "expected_artifact_types": {
            "type": "array", "items": { "type": "string" }
          }
          // ... other task-specific fields ...
        },
        "required": ["inputs", "evaluation_type", "expected_artifact_types"]
      }
    },
    {
      "if": { "properties": { "entity_type": { "const": "agent" } } },
      "then": {
        "properties": {
          "role": { "type": "string" },
          "prompt_ids": { "type": "array", "items": { "type": "string" } },
          "tool_ids": { "type": "array", "items": { "type": "string" } },
          "rule_ids": { "type": "array", "items": { "type": "string" } },
          "config": { "type": "object" }
        },
        "required": ["role", "prompt_ids", "tool_ids", "rule_ids", "config"]
      }
    },
    {
      "if": { "properties": { "entity_type": { "const": "rubric" } } },
      "then": {
        "properties": {
          "criteria": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "properties": {
                "dimension": { "type": "string" },
                "scale": { "type": "array", "items": { "type": "integer" }, "minItems": 2 },
                "description": { "type": "string" }
              },
              "required": ["dimension", "scale", "description"],
              "additionalProperties": false
            }
          },
          "instructions": { "type": "string" }
        },
        "required": ["criteria"]
      }
    }
    // Additional "if/then" clauses for rules, plugins, onboarding_agent, etc.
  ]
}

```

---

### Usage Notes

- **Extensibility:** For plugins/onboarding_agent, specify capabilities and referenced types. The “entity_type” switch is how to extend for new entity schemas.
- **References (prompt_ids, tool_ids, etc):** These must match an entity in `/catalog/` or `/user_library/` and have a valid id/version (CI can check this in a pre-merge hook).
- **Validation:** Tools like Ajv, python-jsonschema, or Go templates can enforce validation as part of the onboarding agentic flow, CI/CD, and “bench publish.”
- **Manual Override:** In super-user/manual mode, only skipped for development or debugging, as flagged in provenance/changelog.

---

Here’s a condensed version:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Benchmark Entity Metadata",
  "type": "object",
  "properties": {
    "id": { "type": "string", "pattern": "^[a-zA-Z0-9_-]+$" },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "entity_type": {
      "type": "string",
      "enum": [
        "task", "agent", "rubric", "rule", "plugin", "onboarding_agent", "framework", "evaluation", "diff", "artifact"
      ]
    },
    "created_at": { "type": "string", "format": "date-time" },
    "created_by": {
      "type": "object",
      "properties": {
        "human": { "type": "string" },
        "agent": { "type": "string" },
        "origin_workflow": { "type": "string" }
      },
      "minProperties": 1,
      "additionalProperties": false
    },
    "provenance": {
      "type": "object",
      "properties": {
        "source": { "type": "string", "enum": ["catalog", "user_library", "plugin", "external"] },
        "parent_id": { "type": "string" },
        "parent_version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "changelog": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "timestamp": { "type": "string", "format": "date-time" },
              "author": { "type": "string" },
              "action": { "type": "string" },
              "reason": { "type": "string" },
              "diff": { "type": "string" }
            },
            "required": ["timestamp", "author", "action", "reason", "diff"]
          }
        }
      },
      "required": ["source", "changelog"],
      "additionalProperties": false
    }
  },
  "required": ["id", "version", "entity_type", "created_at", "created_by", "provenance"]
}

```

**Entity-type-specific sub-schemas** (for `task`, `agent`, `rubric`, etc.) can be included via `allOf`/`if-then` rules, as shown in detail in my prior response. You’ll attach those by `$ref`. CI should fail or warn if any required or referenced entity/version/id is missing or unregistered.

===

## Appendix: …

Excellent—let’s make this super clear and practical for new contributors, plugin authors, and PR submitters.

Below is a draft contributor guide section you can include with your documentation/codebase. It covers everything a power user or plugin writer needs to know for onboarding agent workflows, custom entities (tasks, rubrics, agents, etc.), plugin permission, and the PR/review process—with your core principles built in.

---

# Contributor Guide: Agentic Benchmark Onboarding Plugins & PRs

---

## Overview

The AI Dev Squad Enhancement Platform is designed from the ground up for safe, transparent, and community-driven extensibility. Whether you want to add a new onboarding agent, a new benchmarking task, contribute a custom rubric, or share a plugin for the onboarding conversation, here’s what you need to know.

---

## What You Can Contribute

- **Onboarding agent plugins:** Plug-in conversational/assistant flows that help new users (or your team) set up, modify, and validate configurations/entities.
- **New entity templates:** Well-structured tasks, agents, rubrics, rules, frameworks, tools, and onboarding workflows.
- **Improvements to the core catalog:** Better defaults, new evaluation/rubric patterns, new supported frameworks.
- **Peripheral (community) plugins:** Optional features or overlays for specific workflows, rules, validations, or integrations.

---

## How to Contribute/Extend

### 1. **Fork or Clone the Repo**

Use the usual GitHub fork/clone pattern, then work in your own branch (named for your feature/entity).

### 2. **File Structure & Placement**

- **Catalog (core):**`/catalog/tasks/`, `/catalog/agents/`, `/catalog/rubrics/`, etc.—For PRs to the canonical system library.
- **User Library (yours or your team’s):**`/user/tasks/`, `/user/plugins/`, etc.—Personal, unreviewed, not public until contributed.
- **Plugins:**`/plugins/onboarding_agents/`, `/plugins/rules/`

### 3. **Editing or Creating an Entity**

- Always include **metadata** as required by the JSON Schema (id, version, entity_type, created_at, created_by, provenance, changelog).
- For onboarding agent plugins:
    - Place in `/plugins/onboarding_agents/`
    - Each workflow/agent must be a standalone YAML or JSON file.
- Reference (never inline) IDs of prompts, agents, rubrics, etc.—so they can be validated and reused.

### 4. **Testing and Validation**

- Run `bench validate` to check that:
    - All metadata fields are present and valid.
    - All referenced IDs/versions/entities exist and match the schema.
    - Only allowed fields and actions are declared in your plugin (see Plugin Permission).
- For onboarding agent plugins, test the conversational onboarding through `bench onboarding --plugin your-plugin.yaml`.

### 5. **Plugin Permissions/Sandboxing**

- Plugins can only modify/read/create entities and configuration files declared in their allowed scope.
- Plugins **cannot** execute arbitrary shell/code (unless a maintainer explicitly enables this for research purposes).
- Sandbox policies are checked at runtime and during CI.

### 6. **Pull Request (PR) and Review Flow**

**For Catalog/Core Additions:**

- Open a PR against the core repo.
- PR must pass all CI validation (including metadata schema checks, all entity references resolved, and reproducible changelogs).
- PR should include a **README** with:
    - Plugin/agent/entity purpose
    - Usage instructions and example dialog (for onboarding agents)
    - Changelog / authorship history
- **CI will block** any PR with missing or invalid metadata, schema violations, non-traceable provenance, or unresolved entity references.

**For Plugins/Community Extensions:**

- Upload to `/plugins/` (or through `bench publish --plugin` CLI command).
- Optional: Open a PR for review and inclusion in the plugin directory (plugins will be labeled `plugin-community`).
- Community/maintainers can review, comment, and help integrate your improvements for wider use.

### 7. **Publishing and Sharing**

- For public benchmarks or rubrics, follow the same PR flow.
- All additions should preserve provenance; forks/derivatives must reference source, intent/reason, and changelogs.
- Contributors are encouraged to improve, refactor, or adjust existing agentic onboarding flows—every conversation/decision is part of the system’s evolution.

---

## What Makes a Good Contribution?

- Well-documented: Succinct README, clear purpose, self-contained.
- Validated: Passes all schema checks, no orphaned/missing references.
- Transparent & Traceable: Each step/change logged for reproducibility.
- Safe: Plugins don’t escalate or break sandbox (no arbitrary code by default).
- Reusable: Entities and plugins reference catalog/user/plugin files, never hard-coded YAML blobs.

---

## Handy CLI

- `bench validate` – Checks all files/plugins for schema and cross-reference errors.
- `bench onboarding --plugin` – Runs onboarding/agent flows with your custom plugin.
- `bench publish` – Pushes plugin or entity to the registry or for pull request.
- `bench changelog` – Shows history of any config/entity.

---

**Next Steps:**
Ready for real plugin submission examples? Want to define a sample onboarding plugin contract, or elaborate further on CI checks or community review rules? Let me know which detail is most valuable to tackle next! Here’s a practical, contributor-focused guide for plugins, onboarding agents, and PR submissions. This should empower new folks and keep your core both clean and adaptable:

---

# Contributor Guide: Plugins, Onboarding Agents, & PR Process

## Overview

The Agentic Framework Benchmark Tool is built to be open, extensible, and community-driven. We welcome plugins, new onboarding agent workflows, and catalog entity contributions (tasks, rubrics, etc). But to keep everything reproducible, safe, and trustworthy, please follow this contract.

---

## What You Can Contribute

- **Onboarding Agents/Workflows:** YAML/JSON files in `/plugins/onboarding_agents/` describing dialog/logic for user setup and config generation.
- **Catalog Entities:** Tasks, agents, rubrics, rules, validations, etc., with full metadata, in `/catalog/` or `/user/` (if personal).
- **Plugins:** Optional extensions, onboarding skills, or new validators in `/plugins/`.
- **Improvements to existing agents, workflows, or core templates.**

---

## Structure & Metadata Requirements

**Each contributed file must include:**

- `id` (unique, consistent with entire system)
- `version` (semver, e.g. `1.0.0`)
- `entity_type` (see registry: `onboarding_agent`, `plugin`, `task`, etc.)
- `created_at` (ISO 8601)
- `created_by` (object—record human, agent, and workflow of origin)
- `provenance` (source: catalog|user_library|plugin|external, parent pointer if forked, full `changelog`)
- For onboarding agents: workflow/steps/skills must reference valid agent and prompt IDs.

**Validation:**

- Run `bench validate`. All refs to other entities (prompts, rubrics, etc.) must resolve; all metadata fields are required.
- Plugins **must not** execute arbitrary shell code or escalate permissions unless security-reviewed and enabled by a maintainer.

---

## PR Process

1. **Clone/fork, create branch** for your feature or fix.
2. **Place files in the proper directory** (`/plugins/onboarding_agents/`, `/catalog/rubrics/`, etc.). Never mix user entities with catalog-approved templates.
3. **Run `bench validate`** and ensure CI (on PR) passes.
4. **Write a README** describing your change, why it matters, and how to use it. Include any example dialog or usage flows if it's an onboarding agent.
5. **Open a pull request.** For:
    - **Core/catalog:** High review bar (tests, completeness, full changelog, security check).
    - **Plugin/peripheral:** Labeled as community; reviewed for safety/compat.
6. **Respond to review:** Maintainers may ask for clarifications, tweaks, or additional validation/scripts.
7. Once approved, your plugin/entity is merged and available to the world!

---

## Best Practices

- Each change in your entity/plugin must log a `changelog` event—reason, author, and diff.
- Make all steps traceable and reproducible; never “magic in the middle.”
- Fork or derive from catalog entities if possible—reference origin for proper provenance.
- For onboarding agents: keep your dialog modular; rely on catalog agents/prompts/tools as much as possible so future upgrades are easy.

---

## Example Contribution (file excerpt)

```yaml
id: onboarding-qa-faststart
version: 1.0.0
entity_type: onboarding_agent
created_at: 2024-05-12T10:10:10Z
created_by:
  human: open-source-contributor
  agent: onboarding-orchestrator:1.5.1
  origin_workflow: onboarding-main:1.5.1
provenance:
  source: plugin
  parent_id: onboarding-main
  parent_version: 1.2.0
  changelog:
    - timestamp: 2024-05-12T10:10:11Z
      author: open-source-contributor
      action: forked
      reason: "Adapted for rapid QA benchmarking"
      diff: |
        + new workflow steps for QA
        + updated prompt references

```

---

## Community & Safety

- All plugins/entities are sandboxed and reviewed for abusive code/behavior.
- If you want to publish to the wider catalog, be ready for a bit more scrutiny—especially for core flows.
- Use `bench publish` or regular GitHub PRs.

---

**Ready to add your first onboarding agent, rubric, or benchmarking task? See `/catalog/README.md` and `/plugins/README.md` for full details, or run `bench help` for command-line guidance.**

Let me know if you’d like a sample plugin (or onboarding agent) file, or want to see the details for onboarding-agent plugin contracts or acceptance criteria! Absolutely! Here’s a contributor/PR and plugin documentation draft you can use to set expectations, encourage contributions, and keep things traceable and high-quality.

---

# Contributor & Plugin Guide – Agentic Framework Benchmark Tool

## What You Can Contribute

**Core Catalog Entities:**

- Tasks, rubrics, agent definitions, prebuilt onboarding workflows, and rules (as user-ready starting points or best-practice modules).

**Onboarding Plugins:**

- New conversational “onboarding agent” workflows (YAML/JSON), placed in `/plugins/onboarding_agents/`, with provenance metadata and versioning.
- Specialized tools or rule sets, placed in `/plugins/tools/` or `/plugins/rules/`.

**Community Extensions:**

- Any workflow, entity, or agent design that works with the public schema—even if not part of the “core catalog.”

---

## Plugin/Onboarding Agent Structure

Each plugin/workflow MUST include:

- Metadata:
    - `id`, `version`, `entity_type`, `created_at`, `created_by` (including agent+human+workflow), and full `provenance`/changelog.
- Entity-specific fields, e.g. `workflow_steps` for onboarding agents, validated against the public schema.
- No shell or exec permissions (unless reviewed for core inclusion).
- All referenced entity IDs/versions (prompt, agent, rubric, tool) must resolve in `/catalog/` or `/user/`.

---

## How to Submit a Contribution/Plugin

1. **Fork the repo** and **create a branch** named for your feature.
2. **Place files in** `/user/` for private use, `/plugins/` for new onboarding flows/rules, or `/catalog/` for template improvements.
3. **Validate:** Run `bench validate` or `bench validate --plugin myplugin.yaml`.
4. **Document:** Add a README in your PR with usage, dialog samples, and metadata required by schema.
5. **PR check:** CI will block any PR with missing or invalid metadata, unresolved references, or unsafe code.
6. **Open a PR:**
    - Core/catalog: review is strict, validation and authorship required.
    - Plugins: labeled as “community” unless accepted to catalog after review.
7. **Respond to review:** Core merges are reviewed by maintainers for stability and provenance. Plugins are lightly reviewed for basic validation and safety.
8. **Publish:** Use `bench publish` for community visibility or public registry upload, or classic GitHub PR.

---

## Best Practices

- Always fill provenance, created_by, changelog, and parent_id for transparency and reproducibility.
- Fork or derive from templates; only create from scratch if necessary (reference parent entity/version).
- Maintain clear, self-explaining changelog entries for each step/decision.
- Never execute code outside of what the plugin permissions allow.
- Onboarding agent workflows should be modular, clear, and tested against at least minimal “hello world” flows.

---

## Example Plugin File Metadata (Excerpt)

```yaml
id: onboarding-doc-mentor
version: 1.1.0
entity_type: onboarding_agent
created_at: 2024-05-15T10:40:12Z
created_by:
  human: alice
  agent: onboarding-orchestrator:1.0.2
  origin_workflow: onboarding-main:1.0.2
provenance:
  source: plugin
  parent_id: onboarding-doc-template
  parent_version: 1.0.0
  changelog:
    - timestamp: 2024-05-15T10:42:01Z
      author: alice
      action: forked
      reason: "Added specialized dialog for mentoring new devs."
      diff: |-
        + workflow_steps: mentor instructions
        + updated Rubric reference

```

---

## Plugin Sandbox (Security Policy)

- Plugins can only read/write registered config/entity files.
- Plugins may not perform arbitrary network or shell actions except as defined by agent interface and permissions.
- All PRs to core/plugin directories are CI-checked for security and adherence to schema.

---

## How to Get Help or Propose Plugin Changes

- For major questions or issues, open a GitHub issue or discussion.
- Ping the maintainers in your PR, or on Discord.
- For quick review, run `bench changelog` and `bench validate` before submission.

---

**Ready to contribute? Fork, validate, document, and PR!**

======

# Onboarding Plugin Developer Contract

## Purpose

Onboarding plugins (onboarding agent workflows and skills) are conversational or stepwise guides that help users create, customize, and validate benchmark entities (tasks, agents, rubrics, etc). These plugins must be robust, traceable, and safe, as they are essential to the user experience and reproducibility of the platform.

---

## Required Structure, Metadata, and Conduct

### 1. **File Location & Naming**

- All onboarding plugins go in `/plugins/onboarding_agents/`.
- Filename must be unique and end with `.yaml` or `.json`.

### 2. **Top-Level Metadata**

Every onboarding plugin file **must include:**

- `id` (global, unique)
- `version` (`"MAJOR.MINOR.PATCH"`)
- `entity_type`: `"onboarding_agent"`
- `created_at`, `created_by` (with human, agent, and workflow version)
- `provenance` (origin, parent, changelog)
- `description` (short summary of intent and scenario covered)

### 3. **Workflow Steps/Skills**

- `workflow_steps` is an ordered array, each step of format:
    - `step_id` (unique within plugin)
    - `prompt` (agent/human message, question, or CLI task)
    - `expected_response_type` (“selection”, “free_form”, “edit_yaml”, “confirm_diff”, etc)
    - `entity_creates` (if the step generates/scaffolds/modifies a config/entity, specify which)
    - `approval_required` (boolean; if true, step does not proceed until user accepts diff/output)
    - `checkpoint` (bool; set to true so user can return to this step if needed)
    - `rollback_options` (optional; list of prior checkpoints/step_ids that can be restored from this point)
    - `intent_summary` (describe what human/agent aimed to accomplish)

### 4. **Plugin Actions & Permissions**

- Plugins can only read/modify supported config/entity types (no shell, file, or system access).
- Plugins may not execute arbitrary code or make external network calls.
- Plugins must defer all final entity file creation to platform’s validator/persistence layer.

### 5. **Provenance & Changelog**

- Every agent-generated file/entity from a plugin must log its originating plugin, version, workflow step sequence, and prompt/response record.
- Every change or rollback creates a changelog event.

### 6. **User Control**

- Plugins must honor user decisions: accept diff, request redo, rollback/rewind, exit to manual at any step.
- Users can always export a full replay/conversation log.

---

# Plugin PR Submission Checklist

> All plugin PRs will be reviewed for these criteria before merge. Submissions not addressing these points will be requested to update.
> 

### ✅ **File Structure:** Plugin is in `/plugins/onboarding_agents/` with a unique, descriptive name.

### ✅ **Metadata:** All required fields at the top of the file; provenance and changelog populated for at least the initial creation/intent.

### ✅ **Workflow Steps:**

- Steps are complete, logically ordered, and every entity reference is resolvable.
- All `prompt` messages and `expected_response_type`s are clear and human-friendly.

### ✅ **Approval Flow:**

- Every major change/action presents a diff and requires user approval or is explicitly marked `approval_required: false` (with justification).
- All checkpoints are set at logical return points.

### ✅ **Validation:**

- Passes `bench validate` locally; all referenced ids/versions resolve.
- No shell/network-unsafe operations anywhere (static check).

### ✅ **Provenance/Reproducibility:**

- Final agent-generated configs/entities include full plugin/workflow origin, version, step sequence, and replay record.

### ✅ **Documentation:**

- README in PR with plugin summary, usage flow example, and fields covered.
- Any new skills/rubrics/tools referenced by id and documented or included in PR.

### ✅ **Testing:**

- At least one “happy path” walkthrough with results presented (screenshot, CLI output, or replay).

### ✅ **Labels:**

- PR labels itself as `plugin`, `onboarding_agent`, or both. If it’s a community-only extension, mark as `plugin-community`.

### ✅ **Contributor Communication:**

- Responds to requests for changes and updates changelog as needed.

---

## What Makes a Plugin “Core”-worthy?

- Handles user confusion and error cases gracefully
- Produces self-documenting artifacts and changelogs
- Modular, readable YAML/JSON and keeps dependencies clear
- Adds value not covered by existing onboarding flows

---

**Template plugin YAMLs, README examples, and a developer FAQ are available in `/plugins/docs/`—see the official repo for guidance and contact maintainers for any plugin-specific design or escalation questions.**

Ready for a sample plugin YAML scaffold or want to move to any other part of the onboarding/extension flow? Here’s a precise contract and checklist for onboarding agent plugins—clear, enforceable, and contributor-friendly:

---

# Onboarding Agent Plugin Contract

**Purpose:**

Onboarding plugins (“onboarding agents” or onboarding workflows) provide configurable conversational or stepwise flows to help users set up, modify, and validate benchmark tasks, agents, rubrics, and other entities using the platform CLI.

## Plugin File Requirements

- **Location:** `/plugins/onboarding_agents/`
- **File Name:** `<unique-descriptive-name>.yaml` or `.json`
- **Metadata:** All top-level fields required by the JSON Schema for plugins:
    - `id`, `version`, `entity_type: onboarding_agent`, `created_at`, `created_by`, `provenance.source (plugin)`, `changelog`, and `description`.
- **Workflow Definition:**
    - `workflow_steps:` array, each with:
        - `step_id` (unique)
        - `prompt` (message to user)
        - `input_type` (“selection”, “free_form”, “edit_yaml”, “confirm_diff”)
        - `entity_action` (“create”, “modify”, “fork”, etc.)
        - `target_entity_type` (“task”, “rubric”, etc.), if any.
        - `approval_required` (boolean)
        - `checkpoint: true` where applicable
- **Permissions:**
    - May only read/create/modify files in user library/catalog; cannot run arbitrary shell code or access system/network.
- **Provenance:**
    - Every file generated in a workflow must include `created_by` and a pointer to the plugin/workflow (id+version) that created or last modified it.
- **Changelog:**
    - Any modification, approval, or rollback must add an entry to the changelog in the affected file(s).
- **User Controls:**
    - Users must be able to exit, rewind, or accept/reject each major operation (step) and view diffs before committing changes.

---

# Plugin PR Checklist

**Files & Placement**

- [ ]  Files are in `/plugins/onboarding_agents/` with unique, human-friendly name.
- [ ]  Each plugin file contains required metadata and a short description.

**Schema & Validation**

- [ ]  All fields validate against latest JSON schema (run `bench validate --plugin your-plugin.yaml`).
- [ ]  No schema violations, missing references, or unregistered ids.

**Workflow Logic**

- [ ]  Each step is clear, modular, and provides user with necessary options.
- [ ]  Checkpoints are available at logical breakpoints.
- [ ]  All major actions show diffs and require user approval (unless documented as intentionally automated).

**Safety & Permissions**

- [ ]  No shell command execution, file/network system access, or unsafe code.
- [ ]  Plugin actions only write/read in approved directories.

**Provenance & Changelog**

- [ ]  All produced files reference plugin, workflow, and user as “created_by”.
- [ ]  Changelog entries are granular, descriptive, and linked to workflow steps.

**Documentation**

- [ ]  PR includes a README with plugin purpose, YAML snippet examples, and a walkthrough of a typical onboarding session.
- [ ]  Explains new skills or referenced entities.

**Testing**

- [ ]  At least one sample “happy path” output shown, with CLI or replay example attached to PR.

**Meta & Collaboration**

- [ ]  PR labels: `plugin`, `onboarding_agent`, or `plugin-community`.
- [ ]  Contributor is available for review discussion and change log updates.

---

Keep plugin YAML, documentation, and entity structure clean and reproducible—they’re first-class product code. For any uncertainty, contact maintainers, and see `/plugins/docs/` for scaffold files and advanced patterns.

Would you like a sample onboarding agent plugin YAML scaffold as a next step? Or want to see how community/plugin review labels and “bench publish” could tie in with this? Here’s a concrete, actionable contract and checklist for onboarding agent plugins and PRs.

---

# Onboarding Plugin Contract & PR Checklist

## Contract for Onboarding Plugins

**Scope:**

- Only files in `/plugins/onboarding_agents/`
- Each file represents a versioned, conversational/config workflow (YAML or JSON).

**Required Metadata:**

- `id` (unique, global)
- `version` (semver)
- `entity_type: onboarding_agent`
- `created_at` (ISO datetime)
- `created_by` (human/agent/workflow, all as available)
- `provenance` (source, parent_id/version if forked, changelog with every action)
- `description` (concise summary of workflow/intent)
- `workflow_steps`: ordered array, with:
    - `step_id`
    - `prompt` (natural language, what user sees)
    - `action_type` (ex: “create_entity”, “edit_entity”, “fork_entity”, “validate_entity”)
    - `target_entity_type` (`task`, `rubric`, `agent`, etc)
    - `approval_required` (true/false)
    - `checkpoint` (true/false)
    - `expected_response_type` (“confirm_diff”, “selection”, “yaml_patch” etc.)
    - `rollback_options` (optional; e.g. previous steps/checkpoints)
    - All diffs/edits made via this workflow must appear in the changelog for every entity touched.

**Plugin Limitations:**

- **NO external shell/system/network actions allowed.**
- Plugins may only read/write official config/entity files.
- All references (to agent/rubric/prompt/rule IDs) must exist at PR time.

**User Interactions:**

- Plugin must support:
    - User acceptance or edit of every diff
    - Back/rewind to checkpoints
    - Exit to manual edit mode
    - Access to full change/replay log at any step

---

## PR Checklist for Onboarding Plugins

### Metadata & Structure

- [ ]  File in `/plugins/onboarding_agents/`
- [ ]  All required fields present (metadata, provenance, changelog)
- [ ]  README included (what it does, sample dialog, entity types touched)

### Logic and Validation

- [ ]  Steps well-ordered, plain English prompts, actionable choices
- [ ]  `bench validate`/schema validation passes (no missing required or dangling refs)
- [ ]  No prohibited or unsafe plugin actions (shell, arbitrary exec)

### Provenance & Changelog

- [ ]  All created/edited entities point to plugin/workflow in `provenance`
- [ ]  Each changelog entry includes timestamp, user/agent, action, reason, and diff

### Approval, Safety, User Controls

- [ ]  Diffs shown for every write; approval gates present
- [ ]  Logical checkpoints; rollback options defined
- [ ]  Plugin consistently allows exit to manual-edit and replay/export

### Labeling & Submission

- [ ]  PR properly labeled (`plugin`, `onboarding_agent`, `plugin-community` if community-contributed)
- [ ]  Contributor responds to review and tracks further changes in changelog

### Testing & Documentation

- [ ]  Example “happy path” run provided (output transcript/cli replay)
- [ ]  Usage and contribution documented in plugin README; new skill/rubric IDs referenced and documented.

---

**Tip:** The best plugins are modular, reproducible, and easy for others to adapt. Fork catalog workflows for provenance, and use the contract to ensure CI and maintainers can help your contribution reach a broad audience!

Want a YAML starter template for an onboarding agent plugin, or an example modular skill to illustrate these principles?

=======

Here’s a simple but real “modular onboarding plugin skill” as a YAML file you could drop into `/plugins/onboarding_agents/`. This agent skill handles one focused aspect of onboarding: helping a user pick or edit a rubric for a new task, with full approvals, diff, and checkpointing.

---

```yaml
id: onboarding-select-rubric
version: "1.0.0"
entity_type: onboarding_agent
created_at: 2024-05-15T15:40:00Z
created_by:
  human: brock.butler
  agent: onboarding-orchestrator:1.0.0
  origin_workflow: onboarding-main:1.0.0
provenance:
  source: plugin
  parent_id: rubric-selector-template
  parent_version: 1.0.0
  changelog:
    - timestamp: 2024-05-15T15:40:00Z
      author: brock.butler
      action: created
      reason: "Initial rubric selection skill for onboarding flow"
      diff: |-
        + Adds rubric selection and customization for new tasks

description: |
  Modular onboarding skill—guides the user through selecting, editing, or creating a rubric for their current benchmark task. Handles lookup, preview, diff, approval, and checkpoint.

workflow_steps:
  - step_id: select-rubric
    prompt: |
      "Let's choose a rubric for evaluating this task. Here are top recommendations:
      1. doc-quality-rubric-v1 (Clarity, Completeness, Formatting)
      2. qa-reliability-rubric-v2 (Correctness, Robustness, Token Efficiency)
      3. custom/new rubric
      Please select by number, or describe what you'd like evaluated."
    expected_response_type: selection
    approval_required: true
    checkpoint: true

  - step_id: preview-selected-rubric
    prompt: |
      "Here is your selected rubric:
      {rubric_yaml_snippet}
      Would you like to accept, edit dimensions/thresholds, or see options again?"
    expected_response_type: selection # [accept/edit/see_options]
    approval_required: true
    checkpoint: true

  - step_id: edit-rubric
    prompt: |
      "What would you like to change? (You can add, remove, or rename dimensions, adjust scales/thresholds, or add descriptions.)"
    expected_response_type: free_form
    entity_action: modify
    target_entity_type: rubric
    approval_required: true
    checkpoint: true

  - step_id: show-diff
    prompt: |
      "Here is the diff to your rubric:
      {rubric_diff}
      Accept, retry edit, go back to previous checkpoint, or exit to manual edit?"
    expected_response_type: confirm_diff
    approval_required: true
    checkpoint: true
    rollback_options: [select-rubric, preview-selected-rubric]

  - step_id: finalize
    prompt: |
      "Rubric finalized and saved. Do you want to continue onboarding (next step: agent selection) or exit?"
    expected_response_type: selection
    approval_required: false

```

---

## What Makes This a Good Modular Skill?

- Uses only catalog/user-registered rubrics—references by id; no inline YAML except in diffs/preview.
- All state changes and approvals are user-driven.
- Each step is checkpointed so the user can “rewind” if stuck.
- Every entity changed (rubric chosen/edited) gets an updated changelog and provenance.
- Modular: This skill can be injected into any onboarding workflow (agent can say: “let’s now run onboarding-select-rubric!”).

---

**How this fits:**

You can chain modular skills like this together (rubric selection, agent selection, framework selection) to assemble more complex, multi-step onboarding flows. Each skill remains focused, testable, and reusable.

Want a similar skill example for agent or tool selection/editing, or shall we move ahead to another documentation or workflow artifact?

=====

You got it, Brock! Here’s a punchy, no-fluff README/landing page that puts your agentic onboarding, fast start path, and modular flexibility front-and-center. This will attract both skeptical engineers (“show me it works!”), open-source contributors, and future advocates. The tone is confident but friendly—just enough voice to make adoption feel personal but pro.

---

# AI Dev Squad Enhancement Platform

## Benchmark Any Agentic Framework. Ship Safer, Faster, and Smarter.

---

### TL;DR

**Ever wish you could actually compare LangGraph, CrewAI, Haystack, Claude, and more—in minutes, not weeks?**

With the AI Dev Squad Enhancement Platform, you pick what you want to test, and an agent walks you through setup, benchmarking, and results. Everything is reproducible, everything is open, and power-users can script, extend, or PR new onboarding flows and templates as easily as running `git pull`.

---

## Why Does This Exist?

- You’re tired of marketing benchmarks and YAML hell.
- You want to know which agentic framework or prompt works best for your codebase, docs, or workflow, not somebody else’s demo repo.
- “Install, describe your goal, run benchmark”—no more hand-wiring, black-box wizardry, or cloud lock-in.

---

## Features

- **Agentic onboarding—CLI that talks with you, not at you.**
    - Conversational, stepwise setup for tasks, rubrics, agents, frameworks, and more.
    - Diffs and approval at every step.
- **Zero-to-benchmark in under 10 minutes.**
    - `git clone`, `make install`, `bench onboarding`—done.
- **Pluggable everything.**
    - Tasks, agents, onboarding skills, and validations are simple YAML/JSON—fork, edit, remix, PR.
- **Full-trace provenance and rollback.**
    - Every config/entity records who/what/when/how.
    - Rewind and replay, or drop to super-user manual mode any time.
- **Export, share, and PR with confidence.**
    - All results are fully reproducible by you or the community—all the way down to random seed, agent prompt, and environment.

---

## Quickstart

```bash
git clone https://github.com/runningexpression/ai-dev-squad-comparison.git
cd ai-dev-squad-comparison
make install
bench onboarding

```

That’s it. You’ll be talking to an agent, setting up your first real, runnable benchmark in minutes. At each step, you approve or customize; everything is tracked and provenanced.

---

## What’s In the Box

- **/catalog**: A curated set of tasks, rubrics, agent definitions, onboarding agent workflows, and frameworks for instant use.
- **/plugins**: Community and extension onboarding agents/skills—yours to fork, extend, or PR.
- **/user**: Your private library—every custom entity, changelog, or experiment is versioned and owned by you.

---

## For Contributors & Power Users

- Write onboarding plugins or extend onboarding flows—see `/plugins/onboarding_agents/`.
- Fork any catalog entity (task, rubric, agent, or onboarding agent), tweak, and run manually or agentically.
- Use `bench validate` to enforce required fields and references before running or PR’ing.
- Want to PR back to core? Just fork, commit, and open a PR; metadata and changelogs will keep you honest.

---

## Not for Sale (Yet)

No forced cloud, no proprietary agents, no dashboard required.

Just honest, fast, transparent benchmarks—at scale.

---

## Start Benchmarking Smarter—Today.

- Want a real benchmark, not a sales deck?
- Want onboarding that learns from you, with versioning, rollback, and explainability built in?
- Curious how your favorite framework actually stacks up on your problem?

Let’s go.

**`bench onboarding`**

---

Want to contribute or have questions? See [CONTRIBUTING.md](https://app.chatprd.ai/chat/CONTRIBUTING.md), the `/plugins/docs/` directory, or ping Brock and the team.

---

Let me know if you want an even shorter “one-liner” for social/GitHub description, or if you’d like to add specific examples/screenshots—always happy to tailor for your real audience! Absolutely! Here’s a punchy README/landing page draft:

---

# AI Dev Squad Enhancement Platform

### TL;DR

Benchmark and compare any agentic AI framework—LangGraph, CrewAI, Haystack, Claude, more—in minutes, using an agentic CLI that guides you through every step, diffs your changes, and keeps everything reproducible.

---

## Why This Exists

**Picking an AI orchestration framework shouldn’t be a guessing game.**

You want real, apples-to-apples benchmarks—using your code and your tasks. Most tools bury you in YAML or demoware. This platform puts agents in charge, walks you through setup via CLI (no black-box magic), and lets you rerun or fork anything—no cloud lock-in, no dashboard dependency.

---

## Zero-to-Benchmark, Fast

```bash
git clone https://github.com/YOURORG/ai-dev-squad-comparison.git
cd ai-dev-squad-comparison
make install
bench onboarding

```

You’ll be in a conversational CLI-onboarding flow, seeing changes, diffs, and approvals at every step. First custom benchmark up and running in <10 min.

---

## What Makes It Different

- **Agentic onboarding:** Human-in-the-loop at every step; agents help you pick, tweak, and validate everything.
- **Full provenance:** Every config, prompt, tweak, and action is tracked. Rollback, replay, or fork—your history is never lost.
- **Plug-and-play:** Extend or create new tasks, agents, rubrics, or onboarding skills as modular files—no code required.
- **Powerful fallback:** Hit the edge or want super-user mode? Drop right to manual YAML and go wild.
- **Community first:** Share any plugin or upgrade with a single CLI: submit as a PR, or use plugin labels to go “community” or “core.”

---

## For Contributors

- Add a new onboarding agent skill or workflow in `/plugins/onboarding_agents/`
- All plugins/entities must pass `bench validate` (see contributing docs for schema/info)
- Every user or plugin-generated file must track authorship and full changelog
- See `/plugins/docs/` for sample plugins, templates, and PR checklists

---

## Community & Roadmap

- Everything is open-source, MIT-licensed, and ready for you to contribute, test, fork, or discuss.
- Want to run a public benchmark or suggest a new agent? PRs and feedback always welcome.

---

## Questions?

See [CONTRIBUTING.md](https://app.chatprd.ai/chat/CONTRIBUTING.md) and `/plugins/docs/`, or open an issue.

Let’s benchmark smarter, together.

---

Let me know if you want this trimmed/tuned further (or want a visual badge, screenshot, or “success in three steps” sidebar). This should make anyone landing on your repo want to install and click “start” without dread!

====

You’re in a strong position, Brock—the foundation is clear, the workflow is ambitious but tractable, and you’re anchoring everything in reproducibility, agentic UX, and true community extensibility. Here are my pragmatic, product-owner thoughts on what will matter most from here and can really set you up for MVP and long-term success:

---

### 1. Prototype a Zero-to-First-Run Experience

Before scaling onboarding plugins or docs any further, actually wire up a minimal “bench onboarding” flow that runs end-to-end—even if 80% of the config is fixed or stubbed, and only the key approval/diff/checkpoint apparatus is working with a single onboarding agent plugin. This will surface any truly hairy UX, validation, or agent orchestration blind spots right away, and will force the essentials into place.

---

### 2. Aggressively Dogfood and Test Your Metadata/Validation Loop

It’s easy for “required metadata” and provenance/spec rules to look great in a doc, but to fall apart when YAML is forked, hand-edited, or merged. Explicitly try to break your own CI/validate flow:

- What real, ugly errors or “unknown field” logs show up?
- Does the CLI/agentic onboarding always catch missing or out-of-sync entities—but without making users feel like they’re fighting an unforgiving validator?

---

### 3. “Happy Path” and “Edge Case” Walkthroughs

After the basics work, do complete “from nothing” and “fix a broken config/flow” stories. Record the time, error messages, and UX pain points that happen for both new users and superusers—these are where your agent skills and CLI fallback needs will stand out (positively or negatively).

---

### 4. Templating and Scaffolding

Seed your `/catalog/` and `/plugins/` directories with 2-3 reference onboarding skills, tasks, rubrics, and agents—fully documented.

- Encourage users/contributors to “copy and fork” rather than start from nothing.
- Every onboarding plugin should start from a template that’s both strict enough to pass schema and fully annotated in YAML.

---

### 5. “Bench Validate” and “Bench Publish” Should Shine

Make these two commands absolutely bulletproof and user-understandable. They’re the security blanket for the whole flow; any error should be understandable, with clear next steps (“here’s the missing field, here’s a reference, here’s how to auto-fix or rollback”).

---

### 6. Version Bumping: Automate If Possible

Where you can, auto-bump entity versions on agent-accepted changes (with sensible rules). If that’s too ambitious day 1, at least make missed manual bumps a warn-not-error.

---

### 7. Community: Docs, Tutorials, and Friendly Labels

People will want to share what they build.

- Include step-by-step “How I created my onboarding agent plugin” or “How I forked a task” walk-throughs.
- Show how to submit PRs for plugins, how tags/labels work (core, plugin-community, peripheral).
- “Starter kit” for onboarding plugins: link to reference YAML, full metadata, and a “hello world” dialog.

---

### 8. Feedback Loop

Set up a public issue link or form: “If onboarding plugin X was unclear or failed, click here”—so you can triage and iterate based on real-world first use.

---

**After MVP is working:**

- Consider a simple registry web page or badge for the most-used onboarding agent plugins.
- If contributor traction is strong, consider light governance for the canonical catalog vs. plugin community extensions.

---

**Bottom Line:**

You’re on the right track. Focus on end-to-end value as experienced by real users/developers, automate all that is feasible for validation and provenance, and make sure every config error or onboarding roadblock has a clear, actionable fix (or fallback).

What would most move the needle right now: more sample onboarding skills, more error/edge-case stories, a typical contributor onboarding doc, or a sample "bench validate" error/output? Or do you want to brainstorm a punchy README/landing page for new users?

=======

## Onboarding Flows

### 1. **Quickstart Onboarding (Zero-to-Benchmark in Minutes)**

- **Entry:** User lands on the repo or project page.
- **Step 1:**
Installs with a single command:
    - `git clone ... && cd ... && make install` or `docker-compose up`
    - No undebuggable pip/npm/venv or random dependency hell.
- **Step 2:**
Runs `bench quickstart` (or `make quickstart`). Runs a default config—no editing needed.
- **Step 3:**
Sees clear CLI output confirming the system health, test run, and where to find results.

**Success =** User runs a complete, meaningful benchmark scenario (on default code, doc, or test repo) in <10 minutes, no failed steps, with a clear summary and artifact output at the end.

---

### 2. **Configuration and Customization Flow**

- **Entry:** User now wants to tweak—add their repo, configure frameworks/agents, or add a new task.
- **Step 1:**
Uses `bench config show` to view current YAML settings, with in-line help or doc links.
- **Step 2:**
Runs `bench config edit` or edits the YAML file in their editor.
    - In-file, all core entity types (framework, agent, rule, etc) are referenced, with IDs not raw inline blobs.
- **Step 3:**
Can validate config (“bench config check”)—CLI tells user if anything is missing, unsupported, or has a typo, and exactly what to do about it.

**Success =** User can add or switch frameworks/agents/tasks with <5 lines/CLI edits, gets instant feedback if misconfigured, and can easily rerun/reproduce with new settings.

---

### 3. **Adding a New Task or Benchmark**

- **Entry:** User wants to try a benchmark on their own repo/code/workflow.
- **Step 1:**
Runs a guided CLI, e.g.,
    - `bench create task` (walks user through required fields: type, inputs, evaluation)
    - CLI autogenerates a task YAML, shows where/how to place it in config.
- **Step 2:**
Runs `bench run` again, sees both default and new task in results, side-by-side.

**Success =** User gets help (inline hints, auto-completion, error messages) so no copying 100+ lines of YAML from examples repo is needed.

---

### 4. **Diagnostic and Recovery Flow**

- **Entry:** Something goes wrong—bad env, framework, or code bug.
- **Step 1:**`bench doctor` analyzes system/dep/env status, suggests clear actions (“Ollama not running—run this command,” “v1.1.3 of CrewAI required,” etc.)
- **Step 2:**`bench explain log:run-123` fetches and displays relevant logs/errors/artifacts.
- **Step 3:**
Direct link to Discord/Issues/Community, with full config/env snapshot for fast help.

**Success =** User never gets blocked by “Unknown error”/“Could not find.../Failed silently.” Every error has a next action and easy path to help.

---

## Requirements & Acceptance Criteria

1. **Quickstart runs a default benchmark with a single Docker or make command.**
    - *Acceptance:* New users report <10 min to first working run, no manual YAML edits needed.
2. **CLI generates config YAMLS for all major entities and validates completeness/types.**
    - *Acceptance:* All config errors are caught before run, with actionable CLI error messages.
3. **Changes to config (add framework, agent, or task) take effect on next run, without restarts.**
    - *Acceptance:* Testers can go zero-to-customized benchmark with at most a CLI edit and a reload.
4. **Onboarding guides are discoverable (README, CLI help, `bench help`, doc links) and always up-to-date.**
    - *Acceptance:* Every step in onboarding links to next-step documentation or in-CLI help.
5. **Every error state in onboarding (bad config, setup, missing dependency) produces a user-facing explanation with at least one suggested fix.**
6. **Users can always view logs and artifacts immediately after a run, from a predictable folder or CLI command.**

**Bonus:**

- **Onboarding path is tested in CI, so new releases never break “bench quickstart”.**
- **A “ten minute onboarding” badge is shown in repo/docs based on actual user/maintainer feedback and PR review.**

---

## Success Indicators

- Reduction in new user “blocked” issues and setup complaints on GH/Discord.
- Ratio of first-run failures to successes is <5% over time.
- “I got my custom agent/framework/task running in under an hour” posts and endorsements.

---

Let me know if you want more detail in any section, or if you want to move directly to writing onboarding checklists, scripting the auto-validate tool, or preparing the contributor onboarding experience. What’s your highest leverage area to dig in next?