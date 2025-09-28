"""
Prompt Injection Guards for AI Dev Squad Comparison
This module provides comprehensive protection against prompt injection attacks
with pattern detection, input sanitization, output filtering, and LLM judge evaluation.
"""
import re
import json
import yaml
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InjectionType(str, Enum):
    """Prompt injection attack type enumeration."""
    DIRECT_INJECTION = "direct_injection"
    ROLE_HIJACKING = "role_hijacking"
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    INSTRUCTION_OVERRIDE = "instruction_override"
    CONTEXT_MANIPULATION = "context_manipulation"
    CODE_INJECTION = "code_injection"
    CREDENTIAL_EXTRACTION = "credential_extraction"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    OUTPUT_MANIPULATION = "output_manipulation"

class ThreatLevel(str, Enum):
    """Threat level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FilterAction(str, Enum):
    """Filter action enumeration."""
    ALLOW = "allow"
    SANITIZE = "sanitize"
    BLOCK = "block"
    FLAG = "flag"
    JUDGE = "judge"

@dataclass
class InjectionPattern:
    """Prompt injection pattern definition."""
    name: str
    pattern: str
    injection_type: InjectionType
    threat_level: ThreatLevel
    description: str
    action: FilterAction = FilterAction.BLOCK
    case_sensitive: bool = False
    regex_flags: int = 0
    compiled_pattern: Optional[re.Pattern] = field(default=None, init=False)
    
    def __post_init__(self):
        """Compile the regex pattern."""
        flags = self.regex_flags
        if not self.case_sensitive:
            flags |= re.IGNORECASE
        
        try:
            self.compiled_pattern = re.compile(self.pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{self.pattern}': {e}")
            self.compiled_pattern = None

@dataclass
class InjectionDetection:
    """Result of injection detection."""
    detected: bool
    patterns_matched: List[InjectionPattern] = field(default_factory=list)
    threat_level: ThreatLevel = ThreatLevel.LOW
    confidence: float = 0.0
    sanitized_input: Optional[str] = None
    blocked_content: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InjectionEvent:
    """Injection detection event for audit logging."""
    timestamp: datetime
    input_text: str
    detection_result: InjectionDetection
    action_taken: FilterAction
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    input_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class PromptInjectionGuard:
    """
    Comprehensive prompt injection detection and prevention system.
    """
    
    def __init__(self, patterns_file: Optional[str] = None, 
                 llm_judge: Optional[Callable] = None):
        self.patterns: List[InjectionPattern] = []
        self.llm_judge = llm_judge
        self.audit_log: List[InjectionEvent] = []
        self.enabled = True
        
        # Load default patterns
        self._load_default_patterns()
        
        # Load custom patterns if provided
        if patterns_file:
            self.load_patterns_from_file(patterns_file)
        
        logger.info(f"Prompt injection guard initialized with {len(self.patterns)} patterns")
    
    def _load_default_patterns(self):
        """Load default injection detection patterns."""
        default_patterns = [
            # Direct injection attempts
            InjectionPattern(
                name="ignore_instructions",
                pattern=r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|commands?)",
                injection_type=InjectionType.DIRECT_INJECTION,
                threat_level=ThreatLevel.HIGH,
                description="Attempts to ignore previous instructions",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="forget_context",
                pattern=r"forget\s+(everything|all|what)\s+(above|before|previously)",
                injection_type=InjectionType.CONTEXT_MANIPULATION,
                threat_level=ThreatLevel.HIGH,
                description="Attempts to clear context or memory",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="new_instructions",
                pattern=r"(new|different|updated)\s+(instructions?|rules?|guidelines?|prompts?)",
                injection_type=InjectionType.INSTRUCTION_OVERRIDE,
                threat_level=ThreatLevel.MEDIUM,
                description="Attempts to provide new instructions",
                action=FilterAction.FLAG
            ),
            
            # Role hijacking
            InjectionPattern(
                name="role_change",
                pattern=r"you\s+are\s+now\s+(a\s+)?(different|new|another)",
                injection_type=InjectionType.ROLE_HIJACKING,
                threat_level=ThreatLevel.HIGH,
                description="Attempts to change AI role or identity",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="pretend_to_be",
                pattern=r"pretend\s+(to\s+be|you\s+are)\s+",
                injection_type=InjectionType.ROLE_HIJACKING,
                threat_level=ThreatLevel.MEDIUM,
                description="Attempts to make AI pretend to be something else",
                action=FilterAction.FLAG
            ),
            
            # System prompt extraction
            InjectionPattern(
                name="system_prompt_query",
                pattern=r"(what\s+(is|are)\s+your|show\s+me\s+your|tell\s+me\s+your)\s+(system\s+)?(prompt|instructions?|guidelines?)",
                injection_type=InjectionType.SYSTEM_PROMPT_EXTRACTION,
                threat_level=ThreatLevel.MEDIUM,
                description="Attempts to extract system prompt",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="initial_instructions",
                pattern=r"(initial|original|first)\s+(instructions?|prompt|message)",
                injection_type=InjectionType.SYSTEM_PROMPT_EXTRACTION,
                threat_level=ThreatLevel.MEDIUM,
                description="Attempts to access initial instructions",
                action=FilterAction.FLAG
            ),
            
            # Code injection
            InjectionPattern(
                name="code_execution",
                pattern=r"(execute|run|eval)\s+(this\s+)?(code|script|command)",
                injection_type=InjectionType.CODE_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                description="Attempts to execute arbitrary code",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="system_commands",
                pattern=r"(import\s+os|subprocess\.|os\.system|exec\(|eval\()",
                injection_type=InjectionType.CODE_INJECTION,
                threat_level=ThreatLevel.CRITICAL,
                description="Dangerous system command patterns",
                action=FilterAction.BLOCK
            ),
            
            # Credential extraction
            InjectionPattern(
                name="password_extraction",
                pattern=r"(what\s+is\s+the|tell\s+me\s+the|show\s+me\s+the)\s+(password|api\s+key|secret|token)",
                injection_type=InjectionType.CREDENTIAL_EXTRACTION,
                threat_level=ThreatLevel.CRITICAL,
                description="Attempts to extract credentials",
                action=FilterAction.BLOCK
            ),
            
            # Jailbreak attempts
            InjectionPattern(
                name="jailbreak_phrases",
                pattern=r"(jailbreak|bypass\s+safety|ignore\s+safety|disable\s+filters?)",
                injection_type=InjectionType.JAILBREAK_ATTEMPT,
                threat_level=ThreatLevel.HIGH,
                description="Common jailbreak attempt phrases",
                action=FilterAction.BLOCK
            ),
            InjectionPattern(
                name="hypothetical_scenario",
                pattern=r"(hypothetically|imagine\s+if|what\s+if|suppose\s+that).*?(ignore|bypass|disable)",
                injection_type=InjectionType.JAILBREAK_ATTEMPT,
                threat_level=ThreatLevel.MEDIUM,
                description="Hypothetical scenario jailbreak attempts",
                action=FilterAction.FLAG
            ),
            
            # Output manipulation
            InjectionPattern(
                name="output_format_override",
                pattern=r"(output|respond|answer)\s+(only|just)\s+(with|in)\s+",
                injection_type=InjectionType.OUTPUT_MANIPULATION,
                threat_level=ThreatLevel.LOW,
                description="Attempts to override output format",
                action=FilterAction.SANITIZE
            ),
            
            # Context manipulation
            InjectionPattern(
                name="conversation_reset",
                pattern=r"(reset|restart|clear)\s+(conversation|chat|context)",
                injection_type=InjectionType.CONTEXT_MANIPULATION,
                threat_level=ThreatLevel.MEDIUM,
                description="Attempts to reset conversation context",
                action=FilterAction.FLAG
            )
        ]
        
        self.patterns.extend(default_patterns)
    
    def load_patterns_from_file(self, patterns_file: str):
        """
        Load injection patterns from YAML file.
        
        Args:
            patterns_file: Path to patterns configuration file
        """
        try:
            patterns_path = Path(patterns_file)
            if not patterns_path.exists():
                logger.warning(f"Patterns file not found: {patterns_file}")
                return
            
            with open(patterns_path, 'r') as f:
                patterns_data = yaml.safe_load(f)
            
            if not patterns_data:
                return
            
            # Load patterns from different categories
            for category, patterns_list in patterns_data.items():
                if not isinstance(patterns_list, list):
                    continue
                
                for pattern_data in patterns_list:
                    try:
                        pattern = InjectionPattern(
                            name=pattern_data['name'],
                            pattern=pattern_data['pattern'],
                            injection_type=InjectionType(pattern_data['injection_type']),
                            threat_level=ThreatLevel(pattern_data['threat_level']),
                            description=pattern_data['description'],
                            action=FilterAction(pattern_data.get('action', 'block')),
                            case_sensitive=pattern_data.get('case_sensitive', False)
                        )
                        self.patterns.append(pattern)
                    except Exception as e:
                        logger.error(f"Error loading pattern {pattern_data.get('name', 'unknown')}: {e}")
            
            logger.info(f"Loaded {len(patterns_data)} pattern categories from {patterns_file}")
            
        except Exception as e:
            logger.error(f"Error loading patterns from {patterns_file}: {e}")
    
    def _calculate_input_hash(self, text: str) -> str:
        """Calculate hash of input text for tracking."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def detect_injection(self, text: str) -> InjectionDetection:
        """
        Detect prompt injection attempts in input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            InjectionDetection result with matched patterns and threat assessment
        """
        if not self.enabled or not text:
            return InjectionDetection(detected=False)
        
        matched_patterns = []
        blocked_content = []
        max_threat_level = ThreatLevel.LOW
        total_confidence = 0.0
        
        # Check against all patterns
        for pattern in self.patterns:
            if not pattern.compiled_pattern:
                continue
            
            matches = pattern.compiled_pattern.findall(text)
            if matches:
                matched_patterns.append(pattern)
                
                # Track blocked content for sanitization
                if pattern.action in [FilterAction.BLOCK, FilterAction.SANITIZE]:
                    blocked_content.extend(matches if isinstance(matches[0], str) else [match[0] for match in matches])
                
                # Update threat level (take highest)
                if self._threat_level_value(pattern.threat_level) > self._threat_level_value(max_threat_level):
                    max_threat_level = pattern.threat_level
                
                # Add to confidence score
                confidence_boost = {
                    ThreatLevel.LOW: 0.2,
                    ThreatLevel.MEDIUM: 0.4,
                    ThreatLevel.HIGH: 0.7,
                    ThreatLevel.CRITICAL: 1.0
                }[pattern.threat_level]
                total_confidence += confidence_boost
        
        # Cap confidence at 1.0
        total_confidence = min(total_confidence, 1.0)
        
        # Determine if injection was detected
        detected = len(matched_patterns) > 0
        
        # Create sanitized version if needed
        sanitized_input = None
        if detected and any(p.action == FilterAction.SANITIZE for p in matched_patterns):
            sanitized_input = self._sanitize_input(text, matched_patterns)
        
        return InjectionDetection(
            detected=detected,
            patterns_matched=matched_patterns,
            threat_level=max_threat_level,
            confidence=total_confidence,
            sanitized_input=sanitized_input,
            blocked_content=blocked_content,
            metadata={
                'pattern_count': len(matched_patterns),
                'injection_types': list(set(p.injection_type.value for p in matched_patterns))
            }
        )
    
    def _threat_level_value(self, threat_level: ThreatLevel) -> int:
        """Convert threat level to numeric value for comparison."""
        return {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }[threat_level]
    
    def _sanitize_input(self, text: str, matched_patterns: List[InjectionPattern]) -> str:
        """
        Sanitize input by removing or replacing detected injection patterns.
        
        Args:
            text: Original input text
            matched_patterns: List of matched injection patterns
            
        Returns:
            Sanitized text with injection patterns removed/replaced
        """
        sanitized = text
        
        for pattern in matched_patterns:
            if pattern.action == FilterAction.SANITIZE and pattern.compiled_pattern:
                # Replace matched content with placeholder
                sanitized = pattern.compiled_pattern.sub("[FILTERED]", sanitized)
        
        return sanitized
    
    def filter_input(self, text: str, user_id: Optional[str] = None, 
                    session_id: Optional[str] = None) -> Tuple[str, InjectionDetection]:
        """
        Filter input text and apply appropriate actions based on detection results.
        
        Args:
            text: Input text to filter
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            Tuple of (filtered_text, detection_result)
            
        Raises:
            ValueError: If input is blocked due to injection detection
        """
        detection = self.detect_injection(text)
        
        # Log the detection event
        self._log_injection_event(text, detection, user_id, session_id)
        
        if not detection.detected:
            return text, detection
        
        # Determine action based on highest threat pattern
        highest_threat_pattern = max(
            detection.patterns_matched,
            key=lambda p: self._threat_level_value(p.threat_level)
        )
        
        action = highest_threat_pattern.action
        
        if action == FilterAction.BLOCK:
            raise ValueError(f"Input blocked due to {highest_threat_pattern.injection_type.value} detection: {highest_threat_pattern.description}")
        
        elif action == FilterAction.SANITIZE:
            if detection.sanitized_input:
                return detection.sanitized_input, detection
            else:
                # Fallback sanitization
                return self._sanitize_input(text, detection.patterns_matched), detection
        
        elif action == FilterAction.JUDGE and self.llm_judge:
            # Use LLM judge for nuanced evaluation
            judge_result = self._llm_judge_evaluation(text, detection)
            if judge_result['block']:
                raise ValueError(f"Input blocked by LLM judge: {judge_result['reason']}")
            elif judge_result['sanitize']:
                return judge_result['sanitized_text'], detection
        
        # FLAG or ALLOW - return original text with detection info
        return text, detection
    
    def _llm_judge_evaluation(self, text: str, detection: InjectionDetection) -> Dict[str, Any]:
        """
        Use LLM judge to evaluate potentially malicious input.
        
        Args:
            text: Input text to evaluate
            detection: Initial detection results
            
        Returns:
            Dictionary with judge decision and reasoning
        """
        if not self.llm_judge:
            return {'block': False, 'sanitize': False, 'reason': 'No LLM judge available'}
        
        try:
            # Prepare context for LLM judge
            context = {
                'input_text': text,
                'detected_patterns': [p.name for p in detection.patterns_matched],
                'threat_level': detection.threat_level.value,
                'confidence': detection.confidence
            }
            
            # Call LLM judge
            result = self.llm_judge(context)
            
            return {
                'block': result.get('block', False),
                'sanitize': result.get('sanitize', False),
                'sanitized_text': result.get('sanitized_text', text),
                'reason': result.get('reason', 'LLM judge evaluation'),
                'confidence': result.get('confidence', 0.5)
            }
            
        except Exception as e:
            logger.error(f"LLM judge evaluation failed: {e}")
            # Fail safe - block on high/critical threats
            should_block = detection.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
            return {
                'block': should_block,
                'sanitize': False,
                'reason': f'LLM judge error: {e}',
                'confidence': 0.0
            }
    
    def filter_output(self, text: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, bool]:
        """
        Filter output text to prevent information leakage or harmful content.
        
        Args:
            text: Output text to filter
            context: Optional context information
            
        Returns:
            Tuple of (filtered_text, was_filtered)
        """
        if not self.enabled or not text:
            return text, False
        
        filtered_text = text
        was_filtered = False
        
        # Define output filtering patterns
        output_patterns = [
            # Credential patterns
            (r'(password|api[_\s]?key|secret|token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{8,})["\']?', 
             r'\1: [REDACTED]', "Credential redaction"),
            
            # System path disclosure
            (r'(/etc/|/root/|C:\\Windows\\|C:\\Users\\)', 
             '[SYSTEM_PATH]', "System path redaction"),
            
            # IP address patterns (private ranges)
            (r'\b(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)[\d\.]+\b', 
             '[PRIVATE_IP]', "Private IP redaction"),
            
            # Error stack traces with paths
            (r'File\s+"([^"]*[/\\][^"]*)"', 
             'File "[REDACTED_PATH]"', "File path redaction"),
        ]
        
        for pattern, replacement, description in output_patterns:
            if re.search(pattern, filtered_text, re.IGNORECASE):
                filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
                was_filtered = True
                logger.info(f"Output filtered: {description}")
        
        return filtered_text, was_filtered
    
    def _log_injection_event(self, input_text: str, detection: InjectionDetection,
                           user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Log injection detection event for audit purposes."""
        action_taken = FilterAction.ALLOW
        
        if detection.detected and detection.patterns_matched:
            # Determine action from highest threat pattern
            highest_threat_pattern = max(
                detection.patterns_matched,
                key=lambda p: self._threat_level_value(p.threat_level)
            )
            action_taken = highest_threat_pattern.action
        
        event = InjectionEvent(
            timestamp=datetime.utcnow(),
            input_text=input_text[:500],  # Truncate for logging
            detection_result=detection,
            action_taken=action_taken,
            user_id=user_id,
            session_id=session_id,
            input_hash=self._calculate_input_hash(input_text)
        )
        
        self.audit_log.append(event)
        
        # Log to system logger based on threat level
        if detection.detected:
            log_level = {
                ThreatLevel.LOW: logging.INFO,
                ThreatLevel.MEDIUM: logging.WARNING,
                ThreatLevel.HIGH: logging.ERROR,
                ThreatLevel.CRITICAL: logging.CRITICAL
            }[detection.threat_level]
            
            logger.log(log_level, 
                      f"Injection detected: {detection.threat_level.value} threat, "
                      f"patterns: {[p.name for p in detection.patterns_matched]}")
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[InjectionEvent]:
        """
        Get injection detection audit log.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of injection events
        """
        if limit:
            return self.audit_log[-limit:]
        return self.audit_log.copy()
    
    def export_audit_log(self, output_path: str):
        """
        Export injection audit log to JSON file.
        
        Args:
            output_path: Path to output file
        """
        audit_data = []
        
        for event in self.audit_log:
            audit_data.append({
                'timestamp': event.timestamp.isoformat(),
                'input_hash': event.input_hash,
                'detected': event.detection_result.detected,
                'threat_level': event.detection_result.threat_level.value,
                'confidence': event.detection_result.confidence,
                'patterns_matched': [p.name for p in event.detection_result.patterns_matched],
                'injection_types': event.detection_result.metadata.get('injection_types', []),
                'action_taken': event.action_taken.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'metadata': event.metadata
            })
        
        with open(output_path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Exported injection audit log to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get injection detection statistics.
        
        Returns:
            Dictionary with detection statistics
        """
        total_events = len(self.audit_log)
        detected_events = sum(1 for event in self.audit_log if event.detection_result.detected)
        
        stats = {
            'total_events': total_events,
            'detected_events': detected_events,
            'detection_rate': detected_events / total_events if total_events > 0 else 0.0,
            'threat_levels': {},
            'injection_types': {},
            'actions_taken': {},
            'patterns_loaded': len(self.patterns)
        }
        
        # Count by threat level, injection type, and action
        for event in self.audit_log:
            if event.detection_result.detected:
                threat_level = event.detection_result.threat_level.value
                stats['threat_levels'][threat_level] = stats['threat_levels'].get(threat_level, 0) + 1
                
                for injection_type in event.detection_result.metadata.get('injection_types', []):
                    stats['injection_types'][injection_type] = stats['injection_types'].get(injection_type, 0) + 1
            
            action = event.action_taken.value
            stats['actions_taken'][action] = stats['actions_taken'].get(action, 0) + 1
        
        return stats
    
    def add_custom_pattern(self, pattern: InjectionPattern):
        """
        Add a custom injection detection pattern.
        
        Args:
            pattern: Custom injection pattern to add
        """
        self.patterns.append(pattern)
        logger.info(f"Added custom pattern: {pattern.name}")
    
    def enable(self):
        """Enable injection detection."""
        self.enabled = True
        logger.info("Prompt injection guard enabled")
    
    def disable(self):
        """Disable injection detection."""
        self.enabled = False
        logger.warning("Prompt injection guard disabled")

# Global prompt injection guard
_injection_guard: Optional[PromptInjectionGuard] = None

def get_injection_guard(patterns_file: Optional[str] = None, 
                       llm_judge: Optional[Callable] = None) -> PromptInjectionGuard:
    """Get the global prompt injection guard."""
    global _injection_guard
    if _injection_guard is None:
        _injection_guard = PromptInjectionGuard(patterns_file, llm_judge)
    return _injection_guard

def filter_input(text: str, **kwargs) -> Tuple[str, InjectionDetection]:
    """Convenience function for input filtering."""
    guard = get_injection_guard()
    return guard.filter_input(text, **kwargs)

def filter_output(text: str, **kwargs) -> Tuple[str, bool]:
    """Convenience function for output filtering."""
    guard = get_injection_guard()
    return guard.filter_output(text, **kwargs)

def detect_injection(text: str) -> InjectionDetection:
    """Convenience function for injection detection."""
    guard = get_injection_guard()
    return guard.detect_injection(text)