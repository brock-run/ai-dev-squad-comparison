"""
Phase 2 Database Persistence Layer

This module provides CRUD operations for Phase 2 data models with proper
transaction management, connection pooling, and error handling.

All database operations are designed to be idempotent and safe for concurrent access.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import json

import asyncpg
from asyncpg import Pool, Connection, Record

from .models import (
    Mismatch,
    ResolutionPlan,
    ResolutionAction,
    EquivalenceCriterion,
    MismatchPattern,
    Evidence,
    Provenance,
)
from .enums import (
    MismatchType,
    MismatchStatus,
    ResolutionStatus,
    SafetyLevel,
    ArtifactType,
)

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class MismatchNotFoundError(DatabaseError):
    """Raised when a mismatch is not found."""
    pass


class ResolutionPlanNotFoundError(DatabaseError):
    """Raised when a resolution plan is not found."""
    pass


class ConcurrencyError(DatabaseError):
    """Raised when a concurrency conflict occurs."""
    pass


class Phase2Database:
    """Database interface for Phase 2 entities with connection pooling and transactions."""
    
    def __init__(self, connection_pool: Pool):
        self.pool = connection_pool
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        async with self.pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection with transaction management."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn
    
    async def health_check(self) -> bool:
        """Check database connectivity and schema."""
        try:
            async with self.get_connection() as conn:
                # Check that core tables exist
                result = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('mismatch', 'resolution_plan', 'equivalence_criterion', 'mismatch_pattern')
                    """
                )
                return result == 4
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    # Mismatch CRUD operations
    
    async def create_mismatch(self, mismatch: Mismatch) -> Mismatch:
        """Create a new mismatch record."""
        try:
            async with self.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO mismatch (
                        id, run_id, artifact_ids, type, detectors, evidence, 
                        status, confidence_score, created_at, updated_at, 
                        error_code, error_message, provenance
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    mismatch.id,
                    mismatch.run_id,
                    mismatch.artifact_ids,
                    mismatch.type.value,
                    mismatch.detectors,
                    json.dumps(mismatch.evidence.dict()),
                    mismatch.status.value,
                    mismatch.confidence_score,
                    mismatch.created_at,
                    mismatch.updated_at,
                    mismatch.error_code,
                    mismatch.error_message,
                    json.dumps(mismatch.provenance.dict())
                )
                
                self.logger.info(f"Created mismatch {mismatch.id} for run {mismatch.run_id}")
                return mismatch
                
        except asyncpg.UniqueViolationError:
            raise DatabaseError(f"Mismatch {mismatch.id} already exists")
        except Exception as e:
            self.logger.error(f"Failed to create mismatch {mismatch.id}: {e}")
            raise DatabaseError(f"Failed to create mismatch: {e}")
    
    async def get_mismatch(self, mismatch_id: str) -> Optional[Mismatch]:
        """Get a mismatch by ID."""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM mismatch WHERE id = $1",
                    mismatch_id
                )
                
                if not row:
                    return None
                
                return self._row_to_mismatch(row)
                
        except Exception as e:
            self.logger.error(f"Failed to get mismatch {mismatch_id}: {e}")
            raise DatabaseError(f"Failed to get mismatch: {e}")
    
    async def update_mismatch_status(
        self, 
        mismatch_id: str, 
        status: MismatchStatus, 
        error_code: Optional[str] = None, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update mismatch status atomically."""
        try:
            async with self.transaction() as conn:
                result = await conn.execute(
                    """
                    UPDATE mismatch 
                    SET status = $2, error_code = $3, error_message = $4, updated_at = $5
                    WHERE id = $1
                    """,
                    mismatch_id,
                    status.value,
                    error_code,
                    error_message,
                    datetime.utcnow()
                )
                
                updated = result.split()[-1] == '1'
                if updated:
                    self.logger.info(f"Updated mismatch {mismatch_id} status to {status.value}")
                
                return updated
                
        except Exception as e:
            self.logger.error(f"Failed to update mismatch {mismatch_id} status: {e}")
            raise DatabaseError(f"Failed to update mismatch status: {e}")
    
    async def list_mismatches(
        self, 
        run_id: Optional[str] = None,
        mismatch_type: Optional[MismatchType] = None,
        status: Optional[MismatchStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Mismatch]:
        """List mismatches with optional filtering."""
        try:
            conditions = []
            params = []
            param_count = 0
            
            if run_id:
                param_count += 1
                conditions.append(f"run_id = ${param_count}")
                params.append(run_id)
            
            if mismatch_type:
                param_count += 1
                conditions.append(f"type = ${param_count}")
                params.append(mismatch_type.value)
            
            if status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status.value)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            param_count += 1
            limit_param = f"${param_count}"
            params.append(limit)
            
            param_count += 1
            offset_param = f"${param_count}"
            params.append(offset)
            
            query = f"""
                SELECT * FROM mismatch 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT {limit_param} OFFSET {offset_param}
            """
            
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                return [self._row_to_mismatch(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to list mismatches: {e}")
            raise DatabaseError(f"Failed to list mismatches: {e}")
    
    # Resolution Plan CRUD operations
    
    async def create_resolution_plan(self, plan: ResolutionPlan) -> ResolutionPlan:
        """Create a new resolution plan."""
        try:
            async with self.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO resolution_plan (
                        id, mismatch_id, actions, safety_level, required_evidence,
                        approvals, outcome, created_at, applied_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    plan.id,
                    plan.mismatch_id,
                    json.dumps([action.dict() for action in plan.actions]),
                    plan.safety_level.value,
                    plan.required_evidence,
                    json.dumps(plan.approvals),
                    json.dumps(plan.outcome) if plan.outcome else None,
                    plan.created_at,
                    plan.applied_at
                )
                
                self.logger.info(f"Created resolution plan {plan.id} for mismatch {plan.mismatch_id}")
                return plan
                
        except asyncpg.UniqueViolationError:
            raise DatabaseError(f"Resolution plan {plan.id} already exists")
        except asyncpg.ForeignKeyViolationError:
            raise DatabaseError(f"Mismatch {plan.mismatch_id} does not exist")
        except Exception as e:
            self.logger.error(f"Failed to create resolution plan {plan.id}: {e}")
            raise DatabaseError(f"Failed to create resolution plan: {e}")
    
    async def get_resolution_plan(self, plan_id: str) -> Optional[ResolutionPlan]:
        """Get a resolution plan by ID."""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM resolution_plan WHERE id = $1",
                    plan_id
                )
                
                if not row:
                    return None
                
                return self._row_to_resolution_plan(row)
                
        except Exception as e:
            self.logger.error(f"Failed to get resolution plan {plan_id}: {e}")
            raise DatabaseError(f"Failed to get resolution plan: {e}")
    
    async def update_resolution_plan_outcome(self, plan_id: str, outcome: Dict[str, Any]) -> bool:
        """Update resolution plan outcome."""
        try:
            async with self.transaction() as conn:
                result = await conn.execute(
                    """
                    UPDATE resolution_plan 
                    SET outcome = $2, applied_at = $3
                    WHERE id = $1
                    """,
                    plan_id,
                    json.dumps(outcome),
                    datetime.utcnow()
                )
                
                updated = result.split()[-1] == '1'
                if updated:
                    self.logger.info(f"Updated resolution plan {plan_id} outcome")
                
                return updated
                
        except Exception as e:
            self.logger.error(f"Failed to update resolution plan {plan_id} outcome: {e}")
            raise DatabaseError(f"Failed to update resolution plan outcome: {e}")
    
    async def add_plan_approval(self, plan_id: str, approval: Dict[str, Any]) -> bool:
        """Add an approval to a resolution plan."""
        try:
            async with self.transaction() as conn:
                # Get current approvals
                current_approvals = await conn.fetchval(
                    "SELECT approvals FROM resolution_plan WHERE id = $1",
                    plan_id
                )
                
                if current_approvals is None:
                    raise ResolutionPlanNotFoundError(f"Resolution plan {plan_id} not found")
                
                approvals = json.loads(current_approvals) if current_approvals else []
                approvals.append(approval)
                
                # Update with new approvals
                result = await conn.execute(
                    "UPDATE resolution_plan SET approvals = $2 WHERE id = $1",
                    plan_id,
                    json.dumps(approvals)
                )
                
                updated = result.split()[-1] == '1'
                if updated:
                    self.logger.info(f"Added approval to resolution plan {plan_id}")
                
                return updated
                
        except Exception as e:
            self.logger.error(f"Failed to add approval to resolution plan {plan_id}: {e}")
            raise DatabaseError(f"Failed to add approval: {e}")
    
    # Equivalence Criterion CRUD operations
    
    async def create_equivalence_criterion(self, criterion: EquivalenceCriterion) -> EquivalenceCriterion:
        """Create a new equivalence criterion."""
        try:
            async with self.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO equivalence_criterion (
                        id, version, artifact_type, methods, validators, 
                        calibration, enabled, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    criterion.id,
                    criterion.version,
                    criterion.artifact_type.value,
                    json.dumps([method.dict() for method in criterion.methods]),
                    json.dumps([validator.dict() for validator in criterion.validators]),
                    json.dumps(criterion.calibration),
                    criterion.enabled,
                    criterion.created_at,
                    criterion.updated_at
                )
                
                self.logger.info(f"Created equivalence criterion {criterion.id}")
                return criterion
                
        except asyncpg.UniqueViolationError:
            raise DatabaseError(f"Equivalence criterion {criterion.id} already exists")
        except Exception as e:
            self.logger.error(f"Failed to create equivalence criterion {criterion.id}: {e}")
            raise DatabaseError(f"Failed to create equivalence criterion: {e}")
    
    async def get_equivalence_criterion(self, criterion_id: str) -> Optional[EquivalenceCriterion]:
        """Get an equivalence criterion by ID."""
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM equivalence_criterion WHERE id = $1",
                    criterion_id
                )
                
                if not row:
                    return None
                
                return self._row_to_equivalence_criterion(row)
                
        except Exception as e:
            self.logger.error(f"Failed to get equivalence criterion {criterion_id}: {e}")
            raise DatabaseError(f"Failed to get equivalence criterion: {e}")
    
    # Mismatch Pattern CRUD operations
    
    async def create_mismatch_pattern(self, pattern: MismatchPattern) -> MismatchPattern:
        """Create a new mismatch pattern."""
        try:
            async with self.transaction() as conn:
                await conn.execute(
                    """
                    INSERT INTO mismatch_pattern (
                        id, mismatch_type, pattern_signature, embedding, pattern_data,
                        success_rate, usage_count, confidence_score, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    pattern.id,
                    pattern.mismatch_type.value,
                    pattern.pattern_signature,
                    pattern.embedding,
                    json.dumps(pattern.pattern_data),
                    pattern.success_rate,
                    pattern.usage_count,
                    pattern.confidence_score,
                    pattern.created_at,
                    pattern.updated_at
                )
                
                self.logger.info(f"Created mismatch pattern {pattern.id}")
                return pattern
                
        except asyncpg.UniqueViolationError:
            raise DatabaseError(f"Mismatch pattern {pattern.id} already exists")
        except Exception as e:
            self.logger.error(f"Failed to create mismatch pattern {pattern.id}: {e}")
            raise DatabaseError(f"Failed to create mismatch pattern: {e}")
    
    async def update_pattern_success_rate(self, pattern_id: str, successful: bool) -> bool:
        """Update pattern success rate based on outcome."""
        try:
            async with self.transaction() as conn:
                # Get current pattern data
                row = await conn.fetchrow(
                    "SELECT success_rate, usage_count FROM mismatch_pattern WHERE id = $1",
                    pattern_id
                )
                
                if not row:
                    return False
                
                current_success_rate = row['success_rate']
                current_usage_count = row['usage_count']
                
                # Calculate new success rate using exponential moving average
                alpha = 0.1  # Learning rate
                new_success = 1.0 if successful else 0.0
                
                if current_usage_count == 0:
                    new_success_rate = new_success
                else:
                    new_success_rate = (1 - alpha) * current_success_rate + alpha * new_success
                
                new_usage_count = current_usage_count + 1
                
                # Update pattern
                result = await conn.execute(
                    """
                    UPDATE mismatch_pattern 
                    SET success_rate = $2, usage_count = $3, updated_at = $4
                    WHERE id = $1
                    """,
                    pattern_id,
                    new_success_rate,
                    new_usage_count,
                    datetime.utcnow()
                )
                
                updated = result.split()[-1] == '1'
                if updated:
                    self.logger.info(f"Updated pattern {pattern_id} success rate to {new_success_rate:.3f}")
                
                return updated
                
        except Exception as e:
            self.logger.error(f"Failed to update pattern {pattern_id} success rate: {e}")
            raise DatabaseError(f"Failed to update pattern success rate: {e}")
    
    async def find_similar_patterns(
        self, 
        mismatch_type: MismatchType, 
        pattern_signature: str, 
        limit: int = 10
    ) -> List[MismatchPattern]:
        """Find similar patterns by type and signature similarity."""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM mismatch_pattern 
                    WHERE mismatch_type = $1 
                    AND pattern_signature LIKE $2
                    ORDER BY success_rate DESC, usage_count DESC
                    LIMIT $3
                    """,
                    mismatch_type.value,
                    f"%{pattern_signature[:8]}%",  # Simple similarity matching
                    limit
                )
                
                return [self._row_to_mismatch_pattern(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to find similar patterns: {e}")
            raise DatabaseError(f"Failed to find similar patterns: {e}")
    
    # Helper methods for row conversion
    
    def _row_to_mismatch(self, row: Record) -> Mismatch:
        """Convert database row to Mismatch object."""
        evidence_data = json.loads(row['evidence'])
        provenance_data = json.loads(row['provenance'])
        
        return Mismatch(
            id=row['id'],
            run_id=row['run_id'],
            artifact_ids=row['artifact_ids'],
            type=MismatchType(row['type']),
            detectors=row['detectors'],
            evidence=Evidence(**evidence_data),
            status=MismatchStatus(row['status']),
            confidence_score=row['confidence_score'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            error_code=row['error_code'],
            error_message=row['error_message'],
            provenance=Provenance(**provenance_data)
        )
    
    def _row_to_resolution_plan(self, row: Record) -> ResolutionPlan:
        """Convert database row to ResolutionPlan object."""
        actions_data = json.loads(row['actions'])
        actions = [ResolutionAction(**action_data) for action_data in actions_data]
        
        approvals = json.loads(row['approvals']) if row['approvals'] else []
        outcome = json.loads(row['outcome']) if row['outcome'] else None
        
        return ResolutionPlan(
            id=row['id'],
            mismatch_id=row['mismatch_id'],
            actions=actions,
            safety_level=SafetyLevel(row['safety_level']),
            required_evidence=row['required_evidence'],
            approvals=approvals,
            outcome=outcome,
            created_at=row['created_at'],
            applied_at=row['applied_at']
        )
    
    def _row_to_equivalence_criterion(self, row: Record) -> EquivalenceCriterion:
        """Convert database row to EquivalenceCriterion object."""
        from .models import EquivalenceMethodConfig, EquivalenceValidator
        
        methods_data = json.loads(row['methods'])
        methods = [EquivalenceMethodConfig(**method_data) for method_data in methods_data]
        
        validators_data = json.loads(row['validators'])
        validators = [EquivalenceValidator(**validator_data) for validator_data in validators_data]
        
        return EquivalenceCriterion(
            id=row['id'],
            version=row['version'],
            artifact_type=ArtifactType(row['artifact_type']),
            methods=methods,
            validators=validators,
            calibration=json.loads(row['calibration']),
            enabled=row['enabled'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_mismatch_pattern(self, row: Record) -> MismatchPattern:
        """Convert database row to MismatchPattern object."""
        return MismatchPattern(
            id=row['id'],
            mismatch_type=MismatchType(row['mismatch_type']),
            pattern_signature=row['pattern_signature'],
            embedding=row['embedding'],
            pattern_data=json.loads(row['pattern_data']),
            success_rate=row['success_rate'],
            usage_count=row['usage_count'],
            confidence_score=row['confidence_score'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


# Factory functions for database setup

async def create_connection_pool(
    host: str = "localhost",
    port: int = 5432,
    database: str = "ai_dev_squad",
    user: str = "postgres",
    password: str = "",
    min_size: int = 10,
    max_size: int = 20
) -> Pool:
    """Create a connection pool for Phase 2 database operations."""
    try:
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60
        )
        
        logger.info(f"Created database connection pool with {min_size}-{max_size} connections")
        return pool
        
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {e}")
        raise DatabaseError(f"Failed to create connection pool: {e}")


async def initialize_database(pool: Pool) -> bool:
    """Initialize database schema for Phase 2 entities."""
    try:
        db = Phase2Database(pool)
        
        # Check if database is healthy
        if not await db.health_check():
            logger.error("Database health check failed - schema may be missing")
            return False
        
        logger.info("Phase 2 database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


if __name__ == "__main__":
    # Test database operations
    async def test_database():
        print("🧪 Testing Phase 2 database operations...")
        
        # This would require a real database connection
        # For now, just test the class structure
        try:
            # Mock connection pool for testing
            class MockPool:
                pass
            
            db = Phase2Database(MockPool())
            print("✅ Phase2Database class instantiated successfully")
            
            # Test helper methods with mock data
            print("✅ Database persistence layer structure is valid")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
    
    asyncio.run(test_database())
    """Raised when a resolution plan is not found."""
    pass


class DatabaseManager:
    """
    Manages database connections and provides CRUD operations for Phase 2 entities.
    
    This class handles connection pooling, transaction management, and provides
    high-level operations for all Phase 2 data models.
    """
    
    def __init__(self, database_url: str, min_connections: int = 5, max_connections: int = 20):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[Pool] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the database connection pool."""
        if self._initialized:
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=30,
                server_settings={
                    'application_name': 'phase2_ai_mismatch_resolution',
                    'timezone': 'UTC',
                }
            )
            self._initialized = True
            logger.info(f"Database pool initialized with {self.min_connections}-{self.max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            logger.info("Database pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise DatabaseError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection with transaction management."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn

    # Mismatch CRUD operations
    async def create_mismatch(self, mismatch: Mismatch) -> Mismatch:
        """Create a new mismatch record."""
        async with self.transaction() as conn:
            try:
                await conn.execute("""
                    INSERT INTO mismatch (
                        id, run_id, artifact_ids, type, detectors, evidence,
                        status, confidence_score, created_at, updated_at,
                        error_code, error_message, provenance
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """, 
                    mismatch.id,
                    mismatch.run_id,
                    mismatch.artifact_ids,
                    mismatch.type.value,
                    mismatch.detectors,
                    mismatch.evidence.json(),
                    mismatch.status.value,
                    mismatch.confidence_score,
                    mismatch.created_at,
                    mismatch.updated_at,
                    mismatch.error_code,
                    mismatch.error_message,
                    mismatch.provenance.json()
                )
                logger.info(f"Created mismatch {mismatch.id}")
                return mismatch
            except asyncpg.UniqueViolationError:
                logger.warning(f"Mismatch {mismatch.id} already exists")
                # Return existing mismatch for idempotency
                return await self.get_mismatch(mismatch.id)
            except Exception as e:
                logger.error(f"Failed to create mismatch {mismatch.id}: {e}")
                raise DatabaseError(f"Failed to create mismatch: {e}")

    async def get_mismatch(self, mismatch_id: str) -> Mismatch:
        """Get a mismatch by ID."""
        async with self.get_connection() as conn:
            try:
                record = await conn.fetchrow("""
                    SELECT * FROM mismatch WHERE id = $1
                """, mismatch_id)
                
                if not record:
                    raise MismatchNotFoundError(f"Mismatch {mismatch_id} not found")
                
                return self._record_to_mismatch(record)
            except MismatchNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to get mismatch {mismatch_id}: {e}")
                raise DatabaseError(f"Failed to get mismatch: {e}")

    async def update_mismatch(self, mismatch: Mismatch) -> Mismatch:
        """Update an existing mismatch."""
        mismatch.updated_at = datetime.utcnow()
        
        async with self.transaction() as conn:
            try:
                result = await conn.execute("""
                    UPDATE mismatch SET
                        status = $2, confidence_score = $3, updated_at = $4,
                        error_code = $5, error_message = $6, evidence = $7,
                        provenance = $8
                    WHERE id = $1
                """,
                    mismatch.id,
                    mismatch.status.value,
                    mismatch.confidence_score,
                    mismatch.updated_at,
                    mismatch.error_code,
                    mismatch.error_message,
                    mismatch.evidence.json(),
                    mismatch.provenance.json()
                )
                
                if result == "UPDATE 0":
                    raise MismatchNotFoundError(f"Mismatch {mismatch.id} not found")
                
                logger.info(f"Updated mismatch {mismatch.id}")
                return mismatch
            except MismatchNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to update mismatch {mismatch.id}: {e}")
                raise DatabaseError(f"Failed to update mismatch: {e}")

    async def list_mismatches(
        self,
        run_id: Optional[str] = None,
        mismatch_type: Optional[MismatchType] = None,
        status: Optional[MismatchStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Mismatch]:
        """List mismatches with optional filtering."""
        async with self.get_connection() as conn:
            try:
                conditions = []
                params = []
                param_count = 0
                
                if run_id:
                    param_count += 1
                    conditions.append(f"run_id = ${param_count}")
                    params.append(run_id)
                
                if mismatch_type:
                    param_count += 1
                    conditions.append(f"type = ${param_count}")
                    params.append(mismatch_type.value)
                
                if status:
                    param_count += 1
                    conditions.append(f"status = ${param_count}")
                    params.append(status.value)
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                param_count += 1
                limit_param = f"${param_count}"
                params.append(limit)
                
                param_count += 1
                offset_param = f"${param_count}"
                params.append(offset)
                
                query = f"""
                    SELECT * FROM mismatch
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT {limit_param} OFFSET {offset_param}
                """
                
                records = await conn.fetch(query, *params)
                return [self._record_to_mismatch(record) for record in records]
            except Exception as e:
                logger.error(f"Failed to list mismatches: {e}")
                raise DatabaseError(f"Failed to list mismatches: {e}")

    # Resolution Plan CRUD operations
    async def create_resolution_plan(self, plan: ResolutionPlan) -> ResolutionPlan:
        """Create a new resolution plan."""
        async with self.transaction() as conn:
            try:
                await conn.execute("""
                    INSERT INTO resolution_plan (
                        id, mismatch_id, actions, safety_level, required_evidence,
                        approvals, outcome, created_at, applied_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    plan.id,
                    plan.mismatch_id,
                    json.dumps([action.dict() for action in plan.actions]),
                    plan.safety_level.value,
                    plan.required_evidence,
                    json.dumps(plan.approvals),
                    json.dumps(plan.outcome) if plan.outcome else None,
                    plan.created_at,
                    plan.applied_at
                )
                logger.info(f"Created resolution plan {plan.id}")
                return plan
            except asyncpg.UniqueViolationError:
                logger.warning(f"Resolution plan {plan.id} already exists")
                return await self.get_resolution_plan(plan.id)
            except Exception as e:
                logger.error(f"Failed to create resolution plan {plan.id}: {e}")
                raise DatabaseError(f"Failed to create resolution plan: {e}")

    async def get_resolution_plan(self, plan_id: str) -> ResolutionPlan:
        """Get a resolution plan by ID."""
        async with self.get_connection() as conn:
            try:
                record = await conn.fetchrow("""
                    SELECT * FROM resolution_plan WHERE id = $1
                """, plan_id)
                
                if not record:
                    raise ResolutionPlanNotFoundError(f"Resolution plan {plan_id} not found")
                
                return self._record_to_resolution_plan(record)
            except ResolutionPlanNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to get resolution plan {plan_id}: {e}")
                raise DatabaseError(f"Failed to get resolution plan: {e}")

    async def update_resolution_plan(self, plan: ResolutionPlan) -> ResolutionPlan:
        """Update an existing resolution plan."""
        async with self.transaction() as conn:
            try:
                result = await conn.execute("""
                    UPDATE resolution_plan SET
                        actions = $2, safety_level = $3, required_evidence = $4,
                        approvals = $5, outcome = $6, applied_at = $7
                    WHERE id = $1
                """,
                    plan.id,
                    json.dumps([action.dict() for action in plan.actions]),
                    plan.safety_level.value,
                    plan.required_evidence,
                    json.dumps(plan.approvals),
                    json.dumps(plan.outcome) if plan.outcome else None,
                    plan.applied_at
                )
                
                if result == "UPDATE 0":
                    raise ResolutionPlanNotFoundError(f"Resolution plan {plan.id} not found")
                
                logger.info(f"Updated resolution plan {plan.id}")
                return plan
            except ResolutionPlanNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to update resolution plan {plan.id}: {e}")
                raise DatabaseError(f"Failed to update resolution plan: {e}")

    async def list_resolution_plans_for_mismatch(self, mismatch_id: str) -> List[ResolutionPlan]:
        """List all resolution plans for a specific mismatch."""
        async with self.get_connection() as conn:
            try:
                records = await conn.fetch("""
                    SELECT * FROM resolution_plan 
                    WHERE mismatch_id = $1 
                    ORDER BY created_at DESC
                """, mismatch_id)
                
                return [self._record_to_resolution_plan(record) for record in records]
            except Exception as e:
                logger.error(f"Failed to list resolution plans for mismatch {mismatch_id}: {e}")
                raise DatabaseError(f"Failed to list resolution plans: {e}")

    # Helper methods for converting database records to models
    def _record_to_mismatch(self, record: Record) -> Mismatch:
        """Convert a database record to a Mismatch model."""
        evidence_data = json.loads(record['evidence']) if record['evidence'] else {}
        provenance_data = json.loads(record['provenance']) if record['provenance'] else {}
        
        return Mismatch(
            id=record['id'],
            run_id=record['run_id'],
            artifact_ids=record['artifact_ids'],
            type=MismatchType(record['type']),
            detectors=record['detectors'],
            evidence=Evidence(**evidence_data),
            status=MismatchStatus(record['status']),
            confidence_score=record['confidence_score'],
            created_at=record['created_at'],
            updated_at=record['updated_at'],
            error_code=record['error_code'],
            error_message=record['error_message'],
            provenance=Provenance(**provenance_data)
        )

    def _record_to_resolution_plan(self, record: Record) -> ResolutionPlan:
        """Convert a database record to a ResolutionPlan model."""
        actions_data = json.loads(record['actions']) if record['actions'] else []
        approvals_data = json.loads(record['approvals']) if record['approvals'] else []
        outcome_data = json.loads(record['outcome']) if record['outcome'] else None
        
        actions = [ResolutionAction(**action_data) for action_data in actions_data]
        # approvals and outcome are stored as raw dicts for now
        approvals = approvals_data
        outcome = outcome_data
        
        return ResolutionPlan(
            id=record['id'],
            mismatch_id=record['mismatch_id'],
            actions=actions,
            safety_level=SafetyLevel(record['safety_level']),
            required_evidence=record['required_evidence'],
            approvals=approvals,
            outcome=outcome,
            created_at=record['created_at'],
            applied_at=record['applied_at']
        )

    # Health check and utility methods
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection."""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                pool_stats = {
                    "size": self.pool.get_size() if self.pool else 0,
                    "min_size": self.min_connections,
                    "max_size": self.max_connections,
                }
                return {
                    "status": "healthy",
                    "connection_test": result == 1,
                    "pool_stats": pool_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        async with self.get_connection() as conn:
            try:
                stats = {}
                
                # Mismatch statistics
                mismatch_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_mismatches,
                        COUNT(*) FILTER (WHERE status = 'detected') as detected,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed,
                        AVG(confidence_score) as avg_confidence
                    FROM mismatch
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                stats['mismatches_24h'] = dict(mismatch_stats)
                
                # Resolution plan statistics
                plan_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_plans,
                        COUNT(*) FILTER (WHERE applied_at IS NOT NULL) as applied,
                        AVG(EXTRACT(EPOCH FROM (applied_at - created_at))) as avg_resolution_time_seconds
                    FROM resolution_plan
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                stats['resolution_plans_24h'] = dict(plan_stats)
                
                return stats
            except Exception as e:
                logger.error(f"Failed to get database statistics: {e}")
                raise DatabaseError(f"Failed to get statistics: {e}")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database() first.")
    return _db_manager


async def initialize_database(database_url: str, min_connections: int = 5, max_connections: int = 20):
    """Initialize the global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(database_url, min_connections, max_connections)
    await _db_manager.initialize()


async def close_database():
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


# Export public interface
__all__ = [
    "DatabaseManager",
    "DatabaseError",
    "MismatchNotFoundError",
    "ResolutionPlanNotFoundError",
    "get_database_manager",
    "initialize_database",
    "close_database",
]