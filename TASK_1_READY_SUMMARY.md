# Task 1: Core Data Models and Schemas - READY TO START

## ✅ **ALL BLOCKING ARTIFACTS CREATED**

### **1. Database Schema & Migration** ✅
- **File**: `migrations/20251001_add_phase2_core.sql`
- **Content**: Complete PostgreSQL DDL with proper indexes, constraints, and triggers
- **Features**: 
  - Custom enums for mismatch_type, resolution_status, safety_level
  - Full provenance tracking with JSONB fields
  - Vector similarity support (pgvector ready)
  - Audit logging for all AI decisions
  - Proper foreign keys and cascading deletes

### **2. Runtime Configuration** ✅  
- **File**: `config/phase2_runtime.yaml`
- **Content**: Production-ready configuration with safety controls
- **Features**:
  - **Shadow mode by default** (auto_resolve.enabled: false)
  - **Hard budget limits** ($100/day, 5s analysis, 2s resolution)
  - **Circuit breakers** (≥2% FP rate → auto-disable)
  - **Environment-specific overrides** (dev/stage/prod)
  - **Kill switch** via PHASE2_DISABLE_AUTORESOLVE env var

### **3. Statistical Validation** ✅
- **File**: `scripts/kappa_ci.py`
- **Content**: Bootstrap confidence interval computation for Fleiss' kappa
- **Validation**: 
  - Current dataset: κ=0.832, CI=[0.333, 1.000] ❌ (lower bound < 0.75)
  - **BLOCKS production auto-resolve** until dataset ≥200 items
  - **Enforces quality gate** in CI pipeline

### **4. Golden Test Packs** ✅
- **Files**: `benchmark/goldens/{json_ordering,semantics_text,semantics_code}/*.json`
- **Content**: Deterministic regression tests independent of LLMs
- **Purpose**: Protect canonicalizers and analyzers from regressions

### **5. Adversarial Test Cases** ✅
- **File**: `benchmark/adversarial/semantics_text/subtle_content_change.json`
- **Content**: High-similarity but non-equivalent cases to catch false positives
- **Purpose**: Shake out edge cases where AI might over-accept

### **6. Policy Conformance Tests** ✅
- **File**: `tests/test_policy_conformance.py`
- **Content**: Pytest suite validating ResolutionPolicy enforcement
- **Status**: **9/9 tests passing** ✅
- **Coverage**: All mismatch types, environment progression, dual-key requirements

### **7. Provenance Contract** ✅
- **File**: `benchmark/manifests/run_manifest_v1.schema.json`
- **Content**: Complete JSON schema for run traceability
- **Features**: Environment, budgets, costs, timing, seeds, model versions

## 🎯 **EXECUTION GUIDANCE FOR TASK 1**

### **Lock Enums & IDs First**
```python
# common/phase2/enums.py - CREATE THIS FIRST
from enum import Enum

class MismatchType(Enum):
    WHITESPACE = "whitespace"
    MARKDOWN_FORMATTING = "markdown_formatting"
    JSON_ORDERING = "json_ordering"
    # ... all 8 types from schema
```

### **Migration Strategy**
1. **Apply DDL**: `psql -f migrations/20251001_add_phase2_core.sql`
2. **Dry run in prod**: `--fake-in-prod` flag for safety
3. **Verify FK/indices**: Check all constraints work

### **Schema Validators**
- Wire JSON Schema validation into CI for all YAML entities
- Validate EquivalenceCriterion and ResolutionPolicy on every commit

### **Persistence API**
- CRUD operations with idempotency on `resolution_plan.actions[]`
- Contract tests for all database operations

### **Shadow Wiring**
- Read `config/phase2_runtime.yaml` at startup
- Enforce kill switch at all entry points
- **NO AUTO-APPLY** until dataset scaling complete

## 🚨 **CRITICAL SAFETY CONTROLS**

### **Dataset Scaling Blocker**
- **Current**: 8 items, κ CI lower bound = 0.333 ❌
- **Required**: ≥200 items, κ CI lower bound ≥ 0.75 ✅
- **Action**: Scale dataset in parallel with Task 1 development

### **Production Safety**
- **Auto-resolve**: DISABLED by default (`auto_resolve.enabled: false`)
- **Kill switch**: `PHASE2_DISABLE_AUTORESOLVE=true` → immediate disable
- **Circuit breakers**: FP rate ≥2% → auto-disable with 2-week cooldown
- **Dual-key**: Required for all semantic operations

### **Budget Enforcement**
- **Analysis**: ≤$0.10 per 100KB, ≤5 seconds
- **Resolution**: ≤$0.05 per resolution, ≤2 seconds  
- **Daily**: ≤$100 total, ≤10K LLM calls
- **Alerts**: At 80% of any budget

## 📋 **TASK 1 CHECKLIST**

### **Phase 1: Core Models (Days 1-2)**
- [ ] Create `common/phase2/enums.py` with all enum definitions
- [ ] Create `common/phase2/models.py` with Mismatch, ResolutionPlan, etc.
- [ ] Add Pydantic validation and serialization
- [ ] Create factory methods and builders

### **Phase 2: Database Integration (Days 3-4)**
- [ ] Apply database migration with proper testing
- [ ] Create `common/phase2/persistence.py` with CRUD operations
- [ ] Add connection pooling and transaction management
- [ ] Write persistence contract tests

### **Phase 3: Configuration & Validation (Days 5-6)**
- [ ] Wire runtime configuration loading
- [ ] Add JSON schema validation for all entities
- [ ] Create configuration hot-reloading
- [ ] Add kill switch enforcement

### **Phase 4: Testing & Integration (Day 7)**
- [ ] Run all policy conformance tests
- [ ] Execute golden test pack validation
- [ ] Verify Phase 1 integration works
- [ ] Complete Task 1 acceptance criteria

## 🎯 **SUCCESS CRITERIA**

Task 1 is complete when:

1. **All data models implemented** with proper validation
2. **Database schema applied** with working CRUD operations  
3. **Configuration system working** with kill switch enforcement
4. **All tests passing** (policy conformance + golden tests)
5. **Phase 1 integration verified** (no breaking changes)
6. **Shadow mode confirmed** (no auto-resolution in any environment)

## 🚀 **READY TO START TASK 1**

All blocking artifacts are in place. The foundation is solid, safety controls are active, and the path forward is clear.

**Time to build the core data models and schemas for intelligent AI-powered mismatch resolution!** 🎉

---

**Next Command**: Start implementing `common/phase2/enums.py` with all enum definitions from the database schema.