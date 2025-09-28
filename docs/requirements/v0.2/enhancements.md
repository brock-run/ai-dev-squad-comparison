# Enhancements Backlog — AI Dev Squad Comparison

Last updated: 2025-09-17
Related docs: docs/requirements/prd.md, docs/requirements/benchmark_methodology.md, docs/plan.md, docs/review-scratchpad.md

Purpose: Consolidate remaining functionality, fixes, documentation work, testing strategy, and operationalization tasks to make the system complete and developer-friendly.

---

## 1) Cross-Cutting Enhancements

- Configuration and Environment
  - Standardize env var usage across implementations and document precedence (env > common config > defaults).
  - Provide .env.example in every implementation with consistent variable names (OLLAMA_BASE_URL, model per role, GITHUB_TOKEN, etc.).
  - Align framework-specific clients with common/ollama_integration.py where feasible.

- Developer Experience (DX)
  - Makefile targets: setup, test, bench (by framework), dash, lint, format.
  - Pre-commit hooks: black/ruff (Python), eslint/prettier (JS/TS), dotnet format (C#) where applicable.
  - Pin dependencies and generate lock files; add troubleshooting sections.

- Benchmarking & Results
  - Single, canonical invocation using benchmark/benchmark_suite.py; update any docs referencing run_benchmarks.py.
  - Ensure consistent metrics schema (time, memory, token usage, iterations, success rate, model).
  - Add Makefile recipes and a quickstart snippet in root README.

- GitHub Integration
  - Implement a shared GitHub client with retries, backoff, and rate-limit handling (least-privilege PAT).
  - Expose operations: clone/read, branch, commit, PR create, comment; include dry-run mode and clear errors for permission issues.
  - Add integration tests with mocked GitHub API.

---

## 2) Framework-Specific Gaps

- LangGraph
  - Verify StateGraph phases (Plan/Implement/Test/Review/Iterate) and persisted state (task, artifacts, results).
  - Add or verify unit tests for each state transition (some tests present; expand coverage and edge cases).

- CrewAI
  - Confirm agent role configs and task orchestration; add tests mirroring LangGraph scenarios.
  - Provide autonomous and human-in-the-loop variants.

- AutoGen
  - Ensure GroupChatManager wiring for architect/developer/tester and code execution tool.
  - Add tests for multi-turn refinement loop and stopping conditions.

- n8n
  - Provide exportable workflow JSON(s); add import script or instructions; verify custom nodes (agents/*_node.js).
  - Add a README section for credentials and environment mapping (Ollama/GitHub) including examples.

- Semantic Kernel
  - Confirm actual code presence for python/ and csharp/ directories (plugins and workflow orchestrators). If missing, scaffold minimal working examples.
  - Add tests for plugin orchestration and basic task execution.

- Claude Code Subagents
  - Document how to leverage subagents as prompt libraries for each implementation.
  - Provide examples integrating a few subagents (e.g., code-reviewer, ai-engineer) into workflows.

---

## 3) Testing Strategy

- Unit Tests
  - Agents (prompt shaping, parsing, decision logic with mocked LLMs).
  - Utilities (GitHub client, Ollama manager).

- Integration Tests
  - End-to-end task execution per framework against canonical tasks (Fibonacci, refactor, API skeleton) with mocked LLM responses for determinism.
  - GitHub read-only operations in a sandbox repo or mocked client.

- Cross-Implementation Tests
  - Shared fixtures/tasks and assertions for required capabilities across frameworks.

- Determinism & CI
  - Seedable randomness, recorded interactions where possible, and lightweight CI runs.

---

## 4) Documentation Improvements

- Root README
  - Capability overview and planned roadmap; clear links to requirements, scratchpad, enhancements, and research prompt.

- Implementation READMEs
  - Ensure parity in sections: setup, environment, quickstart, examples, tests, benchmarks, troubleshooting, FAQ.

- Configuration Docs
  - Central page explaining environment variables, Ollama model guidance, and performance tuning tips.

- Benchmarking Docs
  - Update run instructions to use benchmark_suite.py; add Makefile shortcuts; describe outputs consumed by dashboard.

---

## 5) Operationalization Tasks

- Setup scripts to bootstrap environments per framework (Python venv, dotnet build, n8n install).
- Docker Compose option (Ollama service, dashboard, per-framework runners) for reproducible demos.
- Security: Guidance on token storage, rotating PATs, and scopes.
- Resource guidance: Small-model options for low-RAM environments; graceful degradation toggles.

---

## 6) Open Risks and Mitigations

- Framework API drift → Pin versions; add quarterly upgrade guide and compatibility notes.
- Local model variability → Provide fallbacks and guidance for model selection per task.
- Language differences (Python/C#/JS) → Emphasize capability parity and provide adapters/mocks.

---

## 7) Quick Win Checklist

- [ ] Create .env.example in every implementation
- [ ] Unify benchmark instructions to benchmark_suite.py
- [ ] Add Makefile targets for bench and dash
- [ ] Add shared GitHub client skeleton
- [ ] Update root README with capabilities, links, placeholders
- [ ] Add tests parity plan and minimal tests for missing frameworks
