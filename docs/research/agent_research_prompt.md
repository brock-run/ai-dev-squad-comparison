# Research Prompt — AI Dev Squad Comparison

Last updated: 2025-09-17

## Context

This repository compares multiple AI agent orchestration frameworks for building AI development squads (architect, developer, tester). It aims to provide standardized implementations, objective benchmarking, and practical, Ollama-first local execution with optional GitHub integration.

Core goals (see PRD at docs/requirements/prd.md):
- Standardized, working implementations across LangGraph, CrewAI, AutoGen, n8n, and Semantic Kernel
- Objective comparison via a common benchmark suite (see docs/requirements/benchmark_methodology.md)
- Local execution using Ollama (with recommended models) and consistent configuration
- GitHub integration for real-world workflows (clone, analysis, PR creation) with robust error handling

Current state (high-level):
- Implementation scaffolds and READMEs exist for all target frameworks
- Common Ollama integration module available at common/ollama_integration.py
- Benchmarking suite (benchmark/benchmark_suite.py) and dashboard (comparison-results/dashboard.py) are present
- Standard workflows and prompts are documented under workflows/ and docs/requirements/
- Enhancements backlog and review notes summarize gaps: docs/enhancements.md, docs/review-scratchpad.md

Known gaps/risks (from scratchpad and backlog):
- GitHub integration utilities not centralized/verified
- Documentation mismatches for benchmark invocation in one doc
- Semantic Kernel code parity (Python/C#) to verify/scaffold
- Env/config precedence and .env.example parity across implementations

## Research Objectives
Investigate additional approaches and capabilities that should be added to improve this project’s completeness, robustness, and utility. Provide actionable recommendations with references, trade-offs, and proposed implementation plans.

## Priority Research Areas
1. Additional Frameworks / Orchestrators
   - OpenAI Swarm (educational baseline), Langroid, TaskWeaver, LlamaIndex Agents, Haystack Agents, CrewAI v2 patterns
   - Criteria: maturity, community, extensibility, local-model friendliness, licensing
2. Tooling & Safety
   - Secure tool execution (sandboxing, timeouts, resource limits)
   - Command execution guards, filesystem access policies, network egress controls for agents
   - Prompt injection defenses; model spec and safety best practices
3. GitHub Integration Best Practices
   - Robust rate-limit handling, retries with jitter, backoff strategies
   - Fine-grained permissions (least privilege), app vs PAT trade-offs
   - PR quality gates, review workflows, and automated annotations
4. Evaluation & Determinism
   - Agent evaluation techniques: rubric-based grading, self-consistency, programmatic verification
   - Mocking LLMs for deterministic tests; record-replay; seedable sampling
   - Quality metrics beyond correctness (maintainability, security checks)
5. Performance & Cost Optimization (Ollama-first)
   - Model selection guidance by task; prompt compression; response truncation
   - Caching strategies (prompt/result caching), partial reruns, streaming
   - Hardware-aware configurations; fallbacks to smaller models
6. Observability & Telemetry
   - Unified logging schema; tracing (OpenTelemetry) for agent steps
   - Token accounting and cost estimators; event logs for dashboards
7. Reproducibility & Packaging
   - Docker Compose setup with Ollama + per-framework runners + dashboard
   - Dependency pinning and lock files; environment capture scripts

## Deliverables Expected
- Landscape review (2–3 pages) per topic with: what, why, pros/cons, maturity, and adoption examples
- Concrete proposals (1–2 pages each) with:
  - Implementation sketch (folders/files, interfaces, pseudocode)
  - Incremental rollout plan and milestones
  - Risks and mitigations
  - Test plan and metrics to verify success
- Update recommendations to docs/enhancements.md and root README where applicable

## Inputs and Constraints
- Must keep Ollama/local-first workflow as a primary path
- Prefer minimal changes to public interfaces; add adapters where possible
- Keep parity across frameworks for fair comparison
- Ensure new capabilities integrate with benchmark_suite.py and dashboard

## Reference Materials
- PRD: docs/requirements/prd.md
- Benchmark: docs/requirements/benchmark_methodology.md
- Framework selection guide: docs/requirements/framework_selection_guide.md
- Sample prompts: docs/requirements/sample_agent_prompts.md
- Improvement plan: docs/plan.md
- Enhancements backlog: docs/enhancements.md
- Review scratchpad: docs/review-scratchpad.md
- Implementations: */*-implementation/ directories
- Benchmark suite: benchmark/benchmark_suite.py
- Dashboard: comparison-results/dashboard.py
- Ollama integration: common/ollama_integration.py

## Output Format
- Create one main report under docs/research/research_findings.md summarizing your recommendations and linking to any deep dives you create in docs/research/
- Use Markdown with headings, code blocks, and links. Provide a TL;DR at the top and an action list at the bottom.
- Provide a PR checklist for integrating recommendations (tests, docs, benchmarks, dashboards).

## Kickoff Prompt (for an AI Agent)
“You are an expert AI engineering researcher tasked with extending an AI multi-agent orchestration comparison project. Read the referenced documents to understand current capabilities and constraints. Propose pragmatic, incremental improvements across frameworks, tooling, safety, GitHub integration, evaluation, and performance. For each recommendation, provide rationale, alternatives, risks, and a stepwise implementation and testing plan compatible with local Ollama execution. Ensure proposals maintain cross-framework parity and integrate with the benchmarking and dashboard tooling.”
