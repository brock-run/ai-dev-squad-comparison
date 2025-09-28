# Repository Review Scratchpad — Raw Notes

Date: 2025-09-17
Reviewer: Junie (AI Dev Squad Comparison)
Scope: Read requirements under docs/requirements; scan repository to understand implemented capabilities vs planned; list findings, TODOs, and potential problems.

---

## 1) Requirements Understanding (from docs/requirements)
- PRD (docs/requirements/prd.md):
  - Goals: Standardized implementations across LangGraph, CrewAI, AutoGen, n8n, Semantic Kernel; objective comparisons; Ollama-first local execution; GitHub integration.
  - Acceptance criteria: Feature parity per framework; Ollama support; GitHub repo ops (clone, analyze, PRs); benchmark metrics (time, tokens, success rate) with consistent reporting.
  - Technical: Python 3.10+, .NET 7+ for SK, Docker support desirable, standardized logging.
  - Features/Modules: Framework implementations; Ollama integration; performance optimization; GitHub integration; benchmarking; dashboard.
- Benchmark methodology (docs/requirements/benchmark_methodology.md):
  - Standard test tasks (Fibonacci, refactor, API dev, bug fixing, full-stack feature).
  - Metrics (execution time, resource usage, token usage, success rate, code quality, etc.).
- Framework selection guide (docs/requirements/framework_selection_guide.md):
  - Decision matrix, pros/cons of frameworks; selection guidance.
- Sample agent prompts (docs/requirements/sample_agent_prompts.md):
  - Well-detailed prompts for Architect/Developer/Tester across frameworks.

---

## 2) Repo Inventory & Structure (high-level)
- Implementations present:
  - autogen-implementation/ (README present; mentions agents/, workflows/; tests appear to exist per search)
  - crewai-implementation/ (README present; agents code; tests unknown)
  - langgraph-implementation/ (README present; agents/developer.py present; workflows and tests appear to exist)
  - n8n-implementation/ (README present; agents/*.js nodes; workflows JSON; JS/TS environment)
  - semantic-kernel-implementation/ (README present; describes Python and C# subdirs; actual code directories to verify)
  - claude-code-subagents/ (large catalog of subagent prompts and docs; integration path TBD)
- Common tooling:
  - common/ollama_integration.py (robust client, manager, and AgentInterface abstraction)
  - common/ollama_config.json (present)
- Benchmarks & results:
  - benchmark/benchmark_suite.py (classes for BenchmarkResult, PerformanceTracker, Suite; CLI)
  - comparison-results/dashboard.py (Dash app to visualize results)
  - comparison-results/README.md (how to run, metrics explained)
- Docs & Guides:
  - docs/requirements/* (PRD, methodology, selection guide, prompts)
  - docs/plan.md (comprehensive improvement plan aligned to PRD)
  - workflows/development_workflow.md (standard processes)
  - rules/ai-coding.md (coding standards; to open/verify)
  - code_lenses/code_lenses.md (to open/verify)

Other root items:
  - Makefile present; package.json present; node_modules present; personas/ directories exist (scope/purpose unclear relative to comparison project).

---

## 3) Implementation Spot Checks
- LangGraph DeveloperAgent (langgraph-implementation/agents/developer.py):
  - Uses langchain_community ChatOllama with env vars OLLAMA_BASE_URL, OLLAMA_MODEL_DEVELOPER, TEMPERATURE.
  - implement_code(task, design, language) and refine_code(code, feedback) with prompt templates; _extract_code helper.
  - Good initial functionality; integration with a workflow likely in workflows/development_workflow.py (exists per search and tests reference).
- CrewAI DeveloperAgent (crewai-implementation/agents/developer.py):
  - File exists (per RelevantCode). Not yet opened here; likely creates CrewAI tasks for implementation/refinement.
- AutoGen implementation:
  - README outlines agents, group chat manager, usage example; code presence assumed in agents/ and workflows/ directories (not opened in this pass).
- Semantic Kernel implementation:
  - README describes both Python and C# structures; need to confirm if python/ and csharp/ directories exist with actual code (not yet verified).
- n8n implementation:
  - README outlines nodes (architect_node.js, developer_node.js, tester_node.js) and a development_workflow.json; tester_node.js exists per search; good surface area.
- Claude Code Subagents:
  - Extensive agent library documentation; may not be wired into orchestration frameworks yet. Useful for prompts/personas.
- Benchmarks:
  - benchmark_suite.py includes metrics tracking, results saving, report gen, and visualizations. CLI parses framework and output directory options.
- Results Dashboard:
  - Dash app builds DataFrame from raw result JSON, plots time/memory/tokens/cost/quality.

---

## 4) Documentation & Links
- Root README currently provides overview, structure, Ollama usage, benchmarking instructions, testing, etc.
- It lists: docs/benchmark/unit_test_framework.md (file exists).
- Some READMEs mention running a non-existent script name: comparison-results/README.md suggests `../benchmark/run_benchmarks.py` but repo seems to provide `benchmark/benchmark_suite.py`. 
  - POTENTIAL PROBLEM: Benchmark invocation mismatch (run_benchmarks.py vs benchmark_suite.py). Update docs accordingly.
- Many implementation READMEs reference `.env.example`. Need to confirm these files exist in each implementation.
  - POTENTIAL PROBLEM: Missing .env.example templates across implementations.

---

## 5) Configuration & Environment
- common/ollama_integration.py provides Manager with config file discovery (default: common/ollama_config.json). Supports role-based model selection and parameter overrides.
- Environment variables in agents (e.g., OLLAMA_BASE_URL, OLLAMA_MODEL_DEVELOPER) may duplicate common config.
  - TODO: Align per-implementation env usage with common manager; document precedence (env > config file > defaults).

---

## 6) Testing Status
- Found tests in:
  - langgraph-implementation/tests/workflows/test_development_workflow.py (unit tests for workflow states)
  - autogen-implementation/tests/workflows/test_group_chat_manager.py (unit tests for agent setup)
- Not verified for CrewAI, SK, n8n; likely TODOs.
  - TODO: Ensure minimum test coverage across all frameworks with shared task fixtures.

---

## 7) GitHub Integration
- Multiple READMEs claim GitHub integration (clone, PR). Central code for GitHub client/utilities not yet located.
  - TODO: Add or locate a shared GitHub utility module with retries/backoff, and per-implementation wrappers.
  - POTENTIAL PROBLEM: Claims of GitHub integration may be aspirational pending implementation.

---

## 8) Benchmarking & Results Consistency
- benchmark_suite.py writes outputs to comparison-results by default; dashboard expects raw JSON folders.
- Docs mismatch in how to trigger benchmarks (see above). Need unified instructions and Makefile targets.
  - TODO: Add Makefile target `make bench FRAMEWORK=langgraph` linking to benchmark_suite.py.

---

## 9) DX & Tooling
- Makefile exists; content TBD for convenience targets.
- package.json present; node_modules in root (n8n or other JS tooling). Ensure n8n-specific dependencies isolated.
  - TODO: Document Node version and npx usage clearly in n8n README (already mentions `npm install` then `npx n8n start`). Verify.
- Pre-commit hooks and linting not verified.
  - TODO: Add black/ruff, eslint/prettier, dotnet format guidance.

---

## 10) Misc/Uncategorized Observations
- Extra directories (personas) may be demos or unrelated; clarify scope in main README.
  - TODO: Add a section in README explaining auxiliary directories or move to examples/ if out-of-scope.
- docs/plan.md is an excellent improvement plan aligned to PRD; leverage for enhancements backlog.

---

## 11) Actionable TODOs
- Update root README to:
  - Summarize implemented capabilities and planned items; link to docs/requirements and docs/plan.md.
  - Add framework status table (Complete/In Progress/Planned) and deep-dive placeholders.
  - Fix benchmark run instructions; reference benchmark_suite.py and dashboard usage.
- Create docs/enhancements.md consolidating gaps: GitHub integration utilities, tests parity, .env.example templates, benchmarking commands, DX tooling, SK code scaffolding.
- Create docs/research/agent_research_prompt.md to guide an AI agent to investigate additional frameworks (OpenAI Swarm) and capabilities.
- Standardize env & config docs per implementation; ensure .env.example exists everywhere.
- Verify presence of Semantic Kernel python/ and csharp/ code; scaffold if missing.

---

## 12) Potential Problems (to track)
- POTENTIAL PROBLEM: Benchmark docs reference run_benchmarks.py which doesn’t exist; should be benchmark_suite.py or add a thin wrapper script.
- POTENTIAL PROBLEM: GitHub integration claims vs actual code—risk of inconsistency.
- POTENTIAL PROBLEM: Semantic Kernel implementation may be documentation-only without code; acceptance requires working example.
- POTENTIAL PROBLEM: Mixed config patterns (env vs common manager) can cause confusion; consolidate and document precedence.
- POTENTIAL PROBLEM: Node modules in repo root may bloat and confuse; ensure locked and scoped, or document rationale.

---

## 13) Quick Wins Identified
- Update READMEs and add missing docs (enhancements + research prompt).
- Add Makefile targets to harmonize benchmark runs and dashboard launch.
- Create .env.example templates and link to common config.
- Ensure links are consistent and fix known mismatches.
