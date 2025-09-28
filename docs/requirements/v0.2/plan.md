# AI Dev Squad Comparison — Improvement Plan

Last updated: 2025-08-26
Source requirements: docs/requirements/prd.md (plus supporting: benchmark_methodology.md, framework_selection_guide.md, sample_agent_prompts.md)

Note on source document: The requested path docs/requirements.md does not exist in the repository. We used docs/requirements/prd.md as the authoritative requirements document. If a consolidated docs/requirements.md is desired, we recommend generating/curating it from prd.md and the supporting docs.


## 1. Executive Summary
This plan operationalizes the PRD by prioritizing concrete improvements across implementations, tooling, benchmarking, and documentation. The goals are to deliver standardized, Ollama-first multi-agent implementations across frameworks; enable objective, reproducible comparisons; and support practical GitHub-integrated workflows. The plan includes quick wins, phased milestones, and risk mitigations.


## 2. Key Goals (from PRD)
- Provide standardized implementations of AI development squads across major frameworks (LangGraph, CrewAI, AutoGen, n8n, Semantic Kernel).
- Enable objective comparison of capabilities, performance, and ease of use via a common benchmark suite and metrics.
- Support local execution with Ollama for accessibility and cost-effectiveness.
- Demonstrate practical GitHub integration for real-world development workflows (clone, analyze, PR creation).


## 3. Constraints and Assumptions
- Language diversity: Python (most), C# (.NET 7+) for Semantic Kernel, JS/TS for n8n.
- Local resources may be limited; require graceful degradation and clear fallbacks (e.g., optional cloud LLMs).
- Standardized logging and measurement are required for fair comparisons.
- Docker support desirable for reproducibility; security for tokens and rate-limiting for GitHub are mandatory.


## 4. Cross-Cutting Principles
- Consistency first: uniform directory structure, agent roles (Architect, Developer, Tester), and naming across frameworks.
- Reproducibility: pinned dependencies, versioned configs, deterministic benchmarks where feasible.
- Observability: standardized logging schema and metrics emission across implementations.
- Modularity: separate configuration from code, inject dependencies (LLM backends, repos, credentials).
- Documentation parity: each implementation must reach the same documentation quality bar (setup, examples, tests, benchmarks, trade-offs).


## 5. Architecture and Code Structure
Rationale: PRD requires consistent structure for fair comparison; current repo partially aligns but needs hardening across all frameworks.
- Standardize implementation skeletons
  - Ensure each [framework]-implementation/ has: README.md, requirements.txt (or package.json/.csproj), agents/, workflows/, tests/, scripts/ (optional), and config/ (ollama + credentials templates).
  - Provide a shared template in docs/templates/implementation_documentation_template.md and sample code skeletons under a /templates/ directory (or reuse existing docs/templates where applicable).
- Dependency management and pinning
  - Pin framework versions; capture in requirements files and lock files where possible (pip-tools/poetry/nuget lock equivalents; npm package-lock.json for n8n nodes).
- Configuration abstraction
  - Centralize environment variables: model names, temperature, max tokens, GitHub tokens, repo URLs.
  - Provide .env.example per implementation and reference it in README.
- DI and interface contracts
  - Define minimal agent interfaces (generate, critique, plan, test) and workflow orchestration contracts to ease cross-framework parity.


## 6. Framework Implementations Completeness
Rationale: Acceptance criteria mandate feature parity and working examples across frameworks.
- LangGraph
  - Implement StateGraph with phases: Plan (Architect), Implement (Developer), Test (Tester), Review (optional human-in-the-loop), and Iterate on failure.
  - Persist minimal state (task spec, code artifacts, test results) and enable step-wise execution.
- CrewAI
  - Define role configs (goals, backstories), tasks with expected outputs, and sequential orchestration.
  - Provide autonomous and human-in-the-loop variants.
- AutoGen
  - Group chat manager with specialized agents, code execution tool for Developer, feedback loop from Tester.
  - Support stopping criteria and injection of human messages.
- n8n
  - Visual workflow with nodes for Architect/Developer/Tester and edges representing phases; include HTTP nodes/tools for GitHub.
  - Provide exportable workflow JSON and a script to import into n8n.
- Semantic Kernel
  - Plugins/skills for roles; orchestrate via Planner or custom kernel logic.
  - C# example as primary; optional Python parity if feasible.
- Common example task
  - Ensure every framework implements the same canonical tasks (e.g., “Fibonacci function with tests,” “Refactor function X,” “Add README linter”) to support comparable results.


## 7. Ollama Integration and Performance
Rationale: Local execution is a P0; must work with recommended models and perform acceptably.
- Model configuration
  - Default to llama3.1:8b for general tasks; codellama:13b for code-heavy tasks (document trade-offs).
  - Configurable via common/ollama_config.json and per-implementation overrides.
- Prompt and token optimization
  - Trim system prompts; encourage concise role instructions; cap context windows sensibly; stream outputs where available.
- Graceful degradation
  - Detect low-resource environments; offer options to reduce context, switch to smaller models, or offload to cloud with clear docs.
- Metrics
  - Emit token usage (if available), latency per step, and cache hits; integrate with benchmark logger.


## 8. GitHub Integration
Rationale: PRD P1 with security and error handling requirements.
- Auth and security
  - Use PAT via env var (e.g., GITHUB_TOKEN) with least-privilege scopes; provide .env.example and secure loading.
  - Centralize GitHub client utilities per implementation with retry, backoff, and rate-limit handling.
- Operations
  - Implement clone/read, branch creation, commit, PR creation, and issue comment posting.
  - Provide dry-run mode that avoids write operations for safe demos.
- Error handling
  - Clear errors for permission issues; structured errors for rate limits; retries with jitter.


## 9. Benchmarking and Metrics
Rationale: Objective comparison requires standardized tasks and measurement.
- Benchmark suite alignment
  - Ensure benchmark/benchmark_suite.py covers PRD tasks spectrum (simple → complex) and can target each framework via a uniform CLI.
  - Add fixtures for common tasks; ensure tasks deterministic where possible.
- Measurement methodology
  - Capture: execution time, token usage, success rate, number of iterations, and model used.
  - Write logs to JSONL with a common schema; include environment and versions.
- Reproducibility
  - Provide seedable randomness where applicable; publish environment capture (pip freeze, npm list, dotnet list package).


## 10. Comparison Results Dashboard
Rationale: Results must be easily consumable and filterable.
- Data pipeline
  - Standardize output directory structures per run with metadata (timestamp, framework, model).
- Visualization
  - Ensure comparison-results/dashboard.py supports filtering by framework, task, model; include histograms for latency, bar charts for success rates.
- Documentation
  - Add “How to interpret metrics” section and caveats (different language ecosystems, plugin maturity).


## 11. Testing Strategy (Unit, Integration, E2E)
Rationale: Ensure quality and prevent regressions.
- Unit tests
  - For agents’ prompt/decision logic (mock LLM responses) and GitHub utilities (mock API).
- Integration tests
  - End-to-end task execution in a mocked or sandbox repo; local LLM mocked when needed for determinism.
- Cross-implementation tests
  - Shared tests that validate the required behaviors (e.g., ability to generate code, create tests, and iterate on failures) across frameworks.


## 12. Documentation Improvements
Rationale: PRD demands clear, consistent docs and setup guides.
- Implementation READMEs
  - Ensure parity: installation, environment setup (Ollama + models), quickstart, examples, troubleshooting, FAQ.
- Central README updates
  - Link to each implementation’s README and state status (Complete, In Progress, Planned).
- Configuration docs
  - Document env vars, model selection guidance, and performance tuning tips.


## 13. Developer Experience (DX) and Tooling
Rationale: Lower friction to contribute and evaluate.
- Makefile tasks
  - make setup, make test, make bench FRAMEWORK=..., make dash, make lint.
- Pre-commit hooks
  - Black/ruff (Python), eslint/prettier (JS/TS), dotnet format (C#).
- Templates
  - Add cookiecutter-like templates for new frameworks or agents.


## 14. Governance and Contribution Process
Rationale: Keep comparisons fair and contributions consistent.
- Contribution checklist
  - Parity with structure, tests, benchmarks, and docs; include comparison-results update.
- Review guidelines
  - Ensure measurements are taken with pinned versions; require a benchmark run for changes affecting performance.


## 15. Risk Management and Mitigations
- Framework API drift: Pin versions, track release notes, add a quarterly upgrade guide.
- Ollama performance variability: Offer alternative small models and cloud fallback with flags.
- Language ecosystem differences: Emphasize capability parity; provide adapters and mocks where needed.


## 16. Phased Roadmap
- Phase 0 — Quick Wins (1–2 weeks)
  - Add .env.example and config unification across implementations.
  - Pin dependencies; add lock files where feasible.
  - Ensure each implementation exposes the same canonical example task (Fibonacci) with tests.
  - Standardize logging schema and ensure benchmark_suite captures required metrics.
- Phase 1 — Feature Parity & Benchmarks (2–3 weeks)
  - Complete missing features per framework acceptance criteria (state graphs, group chat manager, n8n workflow export, SK plugins).
  - Implement GitHub integration (read-only first, then PR creation) with robust error handling.
  - Validate benchmarks and publish initial comparison results via dashboard.
- Phase 2 — Performance & DX (2 weeks)
  - Optimize prompts and workflows for Ollama; add caching where applicable.
  - Add Makefile tasks, pre-commit hooks, and improved CI scripts.
  - Expand documentation with troubleshooting and model guidance.
- Phase 3 — Advanced Scenarios (ongoing)
  - Add complex tasks (multi-file refactors, test flakiness fixes) and long-running workflow support.
  - Explore additional frameworks (OpenAI Swarm) and cloud-model baselines.


## 17. Success Metrics and Verification
- Framework setup time < 30 minutes: verify via timed setup scripts and contributor feedback.
- Task completion rate > 90% on benchmark suite: track pass/fail per task.
- Token usage < 2000 tokens/task and simple-task response time < 5s: measure via standardized logging.
- Documentation completeness: checklist per implementation with CI badge.


## 18. Action Items and Ownership
- Create/enforce config and logging standards (Owner: Maintainers).
- Close gaps in framework implementations per acceptance criteria (Owner: Implementation leads).
- Harden benchmark suite and dashboard (Owner: Benchmark WG).
- Improve READMEs and templates (Owner: Docs WG).
- Establish contribution checklist and pre-commit (Owner: Maintainers).


## 19. Open Follow-Ups
- Decide whether to add a consolidated docs/requirements.md generated from prd.md for discoverability.
- Evaluate adding OpenAI Swarm as an additional baseline implementation.
- Consider containerized runners for deterministic benchmarking (Docker Compose with Ollama service).
