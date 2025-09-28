"""
Network Access Controls for AI Dev Squad Comparison
This module provides secure network operations with domain allowlists,
request filtering, and comprehensive network policy enforcement.
"""
import os
import re
import socket
import urllib.parse
import urllib.request
import urllib.error
import ssl
import json
import time
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import logging
import threading
from datetime import datetime
import ipaddress

logger = logging.getLogger(__name__)

class NetworkAccessType(str, Enum):
    """Network access type enumeration."""
    HTTP_GET = "http_get"
    HTTP_POST = "http_post"
    HTTP_PUT = "http_put"
    HTTP_DELETE = "http_delete"
    HTTPS_GET = "https_get"
    HTTPS_POST = "https_post"
    HTTPS_PUT = "https_put"
    HTTPS_DELETE = "https_delete"
    DNS_LOOKUP = "dns_lookup"
    SOCKET_CONNECT = "socket_connect"
    FTP = "ftp"
    SMTP = "smtp"

class NetworkResult(str, Enum):
    """Network access result enumeration."""
    ALLOWED = "allowed"
    DENIED = "denied"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"
    ERROR = "error"

@dataclass
class NetworkOperation:
    """Record of a network operation for audit logging."""
    timestamp: datetime
    operation: str
    access_type: NetworkAccessType
    url: Optional[str] = None
    host: str = ""
    port: Optional[int] = None
    method: str = ""
    result: NetworkResult = NetworkResult.DENIED
    response_code: Optional[int] = None
    response_size: Optional[int] = None
    duration_ms: Optional[float] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NetworkPolicy:
    """Network access policy configuration."""
    # Default policy (deny all by default)
    default_deny: bool = True
    
    # Allowed domains (exact matches and wildcards)
    allowed_domains: Set[str] = field(default_factory=set)
    
    # Allowed IP addresses and CIDR blocks
    allowed_ips: Set[str] = field(default_factory=set)
    
    # Denied domains (takes precedence over allowed)
    denied_domains: Set[str] = field(default_factory=set)
    
    # Denied IP addresses and CIDR blocks
    denied_ips: Set[str] = field(default_factory=set)
    
    # Allowed ports
    allowed_ports: Set[int] = field(default_factory=lambda: {80, 443, 8080, 8443})
    
    # Denied ports
    denied_ports: Set[int] = field(default_factory=lambda: {22, 23, 25, 53, 135, 139, 445})
    
    # Allowed protocols
    allowed_protocols: Set[str] = field(default_factory=lambda: {"http", "https"})
    
    # Request timeout in seconds
    request_timeout: int = 30
    
    # Maximum response size in bytes
    max_response_size: int = 10 * 1024 * 1024  # 10MB
    
    # Maximum redirects to follow
    max_redirects: int = 5
    
    # User agent string
    user_agent: str = "AI-Dev-Squad-Agent/1.0"
    
    # Whether to verify SSL certificates
    verify_ssl: bool = True
    
    # Whether to enable audit logging
    audit_enabled: bool = True
    
    # Audit log file path
    audit_log_path: Optional[str] = None
    
    # Rate limiting (requests per minute)
    rate_limit: int = 60
    
    # Rate limiting window in seconds
    rate_window: int = 60

class NetworkAccessController:
    """
    Network access controller with domain allowlists and request filtering.
    """
    
    def __init__(self, policy: Optional[NetworkPolicy] = None):
        self.policy = policy or NetworkPolicy()
        self.audit_log: List[NetworkOperation] = []
        self._lock = threading.Lock()
        self._rate_limiter: Dict[str, List[float]] = {}
        
        # Compile domain patterns for efficient matching
        self._allowed_domain_patterns = self._compile_domain_patterns(self.policy.allowed_domains)
        self._denied_domain_patterns = self._compile_domain_patterns(self.policy.denied_domains)
        
        # Parse IP networks
        self._allowed_networks = self._parse_ip_networks(self.policy.allowed_ips)
        self._denied_networks = self._parse_ip_networks(self.policy.denied_ips)
        
        logger.info("Network access controller initialized")
    
    def _compile_domain_patterns(self, domains: Set[str]) -> List[re.Pattern]:
        """Compile domain patterns for efficient matching."""
        patterns = []
        for domain in domains:
            # Convert wildcard patterns to regex
            if '*' in domain:
                # Escape special regex characters except *
                escaped = re.escape(domain).replace('\\*', '.*')
                pattern = re.compile(f'^{escaped}$', re.IGNORECASE)
            else:
                # Exact match
                pattern = re.compile(f'^{re.escape(domain)}$', re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def _parse_ip_networks(self, ip_strings: Set[str]) -> List[ipaddress.IPv4Network]:
        """Parse IP addresses and CIDR blocks."""
        networks = []
        for ip_str in ip_strings:
            try:
                if '/' in ip_str:
                    # CIDR block
                    network = ipaddress.IPv4Network(ip_str, strict=False)
                else:
                    # Single IP
                    network = ipaddress.IPv4Network(f"{ip_str}/32")
                networks.append(network)
            except ValueError as e:
                logger.warning(f"Invalid IP/CIDR format: {ip_str} - {e}")
        return networks
    
    def _match_domain(self, domain: str, patterns: List[re.Pattern]) -> bool:
        """Check if domain matches any of the patterns."""
        return any(pattern.match(domain) for pattern in patterns)
    
    def _match_ip(self, ip_str: str, networks: List[ipaddress.IPv4Network]) -> bool:
        """Check if IP address matches any of the networks."""
        try:
            ip = ipaddress.IPv4Address(ip_str)
            return any(ip in network for network in networks)
        except ValueError:
            return False
    
    def _resolve_hostname(self, hostname: str) -> Optional[str]:
        """Resolve hostname to IP address."""
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        
        with self._lock:
            if identifier not in self._rate_limiter:
                self._rate_limiter[identifier] = []
            
            # Clean old entries
            window_start = current_time - self.policy.rate_window
            self._rate_limiter[identifier] = [
                timestamp for timestamp in self._rate_limiter[identifier]
                if timestamp > window_start
            ]
            
            # Check rate limit
            if len(self._rate_limiter[identifier]) >= self.policy.rate_limit:
                return False
            
            # Add current request
            self._rate_limiter[identifier].append(current_time)
            return True
    
    def validate_network_access(self, url: str, method: str = "GET") -> Tuple[NetworkResult, Optional[str]]:
        """
        Validate if network access is allowed for the given URL.
        
        Args:
            url: URL to validate
            method: HTTP method
            
        Returns:
            Tuple of (NetworkResult, error_message)
        """
        try:
            # Parse URL
            parsed = urllib.parse.urlparse(url)
            
            if not parsed.scheme or not parsed.netloc:
                return NetworkResult.DENIED, "Invalid URL format"
            
            # Check protocol
            if parsed.scheme.lower() not in self.policy.allowed_protocols:
                return NetworkResult.DENIED, f"Protocol not allowed: {parsed.scheme}"
            
            # Extract hostname and port
            hostname = parsed.hostname
            port = parsed.port
            
            if not hostname:
                return NetworkResult.DENIED, "No hostname in URL"
            
            # Use default ports if not specified
            if port is None:
                if parsed.scheme.lower() == 'https':
                    port = 443
                elif parsed.scheme.lower() == 'http':
                    port = 80
                else:
                    return NetworkResult.DENIED, f"Unknown default port for scheme: {parsed.scheme}"
            
            # Check port restrictions
            if port in self.policy.denied_ports:
                return NetworkResult.DENIED, f"Port is denied: {port}"
            
            if self.policy.allowed_ports and port not in self.policy.allowed_ports:
                return NetworkResult.DENIED, f"Port not in allowlist: {port}"
            
            # Check domain restrictions (denied takes precedence)
            if self._match_domain(hostname, self._denied_domain_patterns):
                return NetworkResult.DENIED, f"Domain is denied: {hostname}"
            
            # Resolve IP address
            ip_address = self._resolve_hostname(hostname)
            if ip_address:
                # Check IP restrictions (denied takes precedence)
                if self._match_ip(ip_address, self._denied_networks):
                    return NetworkResult.DENIED, f"IP address is denied: {ip_address}"
                
                # Check private/local IP addresses
                try:
                    ip_obj = ipaddress.IPv4Address(ip_address)
                    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                        if not self._match_ip(ip_address, self._allowed_networks):
                            return NetworkResult.DENIED, f"Private/local IP not explicitly allowed: {ip_address}"
                except ValueError:
                    pass
            
            # Check allowlists if default deny is enabled
            if self.policy.default_deny:
                domain_allowed = self._match_domain(hostname, self._allowed_domain_patterns)
                ip_allowed = ip_address and self._match_ip(ip_address, self._allowed_networks)
                
                if not domain_allowed and not ip_allowed:
                    return NetworkResult.DENIED, f"Domain/IP not in allowlist: {hostname}"
            
            # Check rate limiting
            rate_limit_key = f"{hostname}:{port}"
            if not self._check_rate_limit(rate_limit_key):
                return NetworkResult.DENIED, f"Rate limit exceeded for {hostname}"
            
            return NetworkResult.ALLOWED, None
            
        except Exception as e:
            logger.error(f"Network validation error: {e}")
            return NetworkResult.ERROR, f"Validation error: {e}"
    
    def _log_operation(self, operation: str, access_type: NetworkAccessType, 
                      result: NetworkResult, **kwargs):
        """Log network operation for audit trail."""
        if not self.policy.audit_enabled:
            return
        
        with self._lock:
            net_op = NetworkOperation(
                timestamp=datetime.utcnow(),
                operation=operation,
                access_type=access_type,
                result=result,
                **kwargs
            )
            
            self.audit_log.append(net_op)
            
            # Write to audit log file if configured
            if self.policy.audit_log_path:
                self._write_audit_log(net_op)
    
    def _write_audit_log(self, net_op: NetworkOperation):
        """Write audit log entry to file."""
        try:
            log_entry = {
                'timestamp': net_op.timestamp.isoformat(),
                'operation': net_op.operation,
                'access_type': net_op.access_type.value,
                'url': net_op.url,
                'host': net_op.host,
                'port': net_op.port,
                'method': net_op.method,
                'result': net_op.result.value,
                'response_code': net_op.response_code,
                'response_size': net_op.response_size,
                'duration_ms': net_op.duration_ms,
                'user_agent': net_op.user_agent,
                'error_message': net_op.error_message,
                'metadata': net_op.metadata
            }
            
            with open(self.policy.audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write network audit log: {e}")
    
    def safe_request(self, url: str, method: str = "GET", data: Optional[bytes] = None,
                    headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Perform safe HTTP request with access control validation.
        
        Args:
            url: URL to request
            method: HTTP method
            data: Request body data
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            Dictionary with response data and metadata
            
        Raises:
            PermissionError: If access is denied
            urllib.error.URLError: If request fails
        """
        start_time = time.time()
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.hostname or "unknown"
        
        # Determine access type
        scheme = parsed_url.scheme.lower()
        access_type_map = {
            ('http', 'GET'): NetworkAccessType.HTTP_GET,
            ('http', 'POST'): NetworkAccessType.HTTP_POST,
            ('http', 'PUT'): NetworkAccessType.HTTP_PUT,
            ('http', 'DELETE'): NetworkAccessType.HTTP_DELETE,
            ('https', 'GET'): NetworkAccessType.HTTPS_GET,
            ('https', 'POST'): NetworkAccessType.HTTPS_POST,
            ('https', 'PUT'): NetworkAccessType.HTTPS_PUT,
            ('https', 'DELETE'): NetworkAccessType.HTTPS_DELETE,
        }
        access_type = access_type_map.get((scheme, method.upper()), NetworkAccessType.HTTP_GET)
        
        # Validate access
        result, error_msg = self.validate_network_access(url, method)
        
        if result != NetworkResult.ALLOWED:
            self._log_operation(
                'http_request', access_type, result,
                url=url, host=hostname, method=method, error_message=error_msg
            )
            raise PermissionError(f"Network access denied: {error_msg}")
        
        try:
            # Prepare request
            request_headers = headers or {}
            request_headers.setdefault('User-Agent', self.policy.user_agent)
            
            # Create request object
            req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
            
            # Configure SSL context if needed
            if scheme == 'https':
                if self.policy.verify_ssl:
                    ssl_context = ssl.create_default_context()
                else:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                
                kwargs['context'] = ssl_context
            
            # Perform request with timeout
            with urllib.request.urlopen(req, timeout=self.policy.request_timeout) as response:
                # Check response size
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.policy.max_response_size:
                    raise urllib.error.URLError(f"Response too large: {content_length} bytes")
                
                # Read response with size limit
                response_data = response.read(self.policy.max_response_size + 1)
                if len(response_data) > self.policy.max_response_size:
                    raise urllib.error.URLError(f"Response exceeds size limit: {len(response_data)} bytes")
                
                # Prepare response
                response_info = {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'data': response_data,
                    'url': response.url,
                    'size': len(response_data)
                }
                
                # Log successful operation
                duration_ms = (time.time() - start_time) * 1000
                self._log_operation(
                    'http_request', access_type, NetworkResult.ALLOWED,
                    url=url, host=hostname, method=method,
                    response_code=response.status, response_size=len(response_data),
                    duration_ms=duration_ms, user_agent=self.policy.user_agent
                )
                
                return response_info
        
        except urllib.error.URLError as e:
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation(
                'http_request', access_type, NetworkResult.ERROR,
                url=url, host=hostname, method=method,
                duration_ms=duration_ms, error_message=str(e)
            )
            raise
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._log_operation(
                'http_request', access_type, NetworkResult.ERROR,
                url=url, host=hostname, method=method,
                duration_ms=duration_ms, error_message=str(e)
            )
            raise
    
    def safe_get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Perform safe HTTP GET request."""
        return self.safe_request(url, "GET", headers=headers, **kwargs)
    
    def safe_post(self, url: str, data: Optional[Union[bytes, str]] = None,
                  headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Perform safe HTTP POST request."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.safe_request(url, "POST", data=data, headers=headers, **kwargs)
    
    def safe_put(self, url: str, data: Optional[Union[bytes, str]] = None,
                 headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Perform safe HTTP PUT request."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.safe_request(url, "PUT", data=data, headers=headers, **kwargs)
    
    def safe_delete(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Perform safe HTTP DELETE request."""
        return self.safe_request(url, "DELETE", headers=headers, **kwargs)
    
    def safe_dns_lookup(self, hostname: str) -> Optional[str]:
        """
        Perform safe DNS lookup with validation.
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            IP address if allowed, None if denied
            
        Raises:
            PermissionError: If DNS lookup is denied
        """
        # Check if hostname is in denied domains
        if self._match_domain(hostname, self._denied_domain_patterns):
            self._log_operation(
                'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.DENIED,
                host=hostname, error_message="Domain is denied"
            )
            raise PermissionError(f"DNS lookup denied for domain: {hostname}")
        
        # Check allowlist if default deny is enabled
        if self.policy.default_deny:
            if not self._match_domain(hostname, self._allowed_domain_patterns):
                self._log_operation(
                    'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.DENIED,
                    host=hostname, error_message="Domain not in allowlist"
                )
                raise PermissionError(f"DNS lookup denied - domain not in allowlist: {hostname}")
        
        try:
            ip_address = self._resolve_hostname(hostname)
            
            if ip_address:
                # Check if resolved IP is denied
                if self._match_ip(ip_address, self._denied_networks):
                    self._log_operation(
                        'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.DENIED,
                        host=hostname, error_message=f"Resolved IP is denied: {ip_address}"
                    )
                    raise PermissionError(f"DNS lookup denied - resolved IP is denied: {ip_address}")
                
                self._log_operation(
                    'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.ALLOWED,
                    host=hostname, metadata={'resolved_ip': ip_address}
                )
            else:
                self._log_operation(
                    'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.ERROR,
                    host=hostname, error_message="DNS resolution failed"
                )
            
            return ip_address
            
        except Exception as e:
            self._log_operation(
                'dns_lookup', NetworkAccessType.DNS_LOOKUP, NetworkResult.ERROR,
                host=hostname, error_message=str(e)
            )
            raise
    
    @contextmanager
    def safe_socket(self, host: str, port: int, timeout: Optional[float] = None):
        """
        Create safe socket connection with access control validation.
        
        Args:
            host: Target hostname or IP
            port: Target port
            timeout: Connection timeout
            
        Yields:
            Socket object if access is allowed
            
        Raises:
            PermissionError: If access is denied
        """
        # Validate socket access
        fake_url = f"tcp://{host}:{port}"
        result, error_msg = self.validate_network_access(fake_url)
        
        if result != NetworkResult.ALLOWED:
            self._log_operation(
                'socket_connect', NetworkAccessType.SOCKET_CONNECT, result,
                host=host, port=port, error_message=error_msg
            )
            raise PermissionError(f"Socket access denied: {error_msg}")
        
        sock = None
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if timeout:
                sock.settimeout(timeout)
            
            # Connect
            sock.connect((host, port))
            
            self._log_operation(
                'socket_connect', NetworkAccessType.SOCKET_CONNECT, NetworkResult.ALLOWED,
                host=host, port=port
            )
            
            yield sock
            
        except Exception as e:
            self._log_operation(
                'socket_connect', NetworkAccessType.SOCKET_CONNECT, NetworkResult.ERROR,
                host=host, port=port, error_message=str(e)
            )
            raise
        
        finally:
            if sock:
                sock.close()
    
    def get_audit_log(self, limit: Optional[int] = None) -> List[NetworkOperation]:
        """
        Get network audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of network operations
        """
        with self._lock:
            if limit:
                return self.audit_log[-limit:]
            return self.audit_log.copy()
    
    def export_audit_log(self, output_path: str) -> None:
        """
        Export network audit log to JSON file.
        
        Args:
            output_path: Path to output file
        """
        audit_data = []
        
        for net_op in self.audit_log:
            audit_data.append({
                'timestamp': net_op.timestamp.isoformat(),
                'operation': net_op.operation,
                'access_type': net_op.access_type.value,
                'url': net_op.url,
                'host': net_op.host,
                'port': net_op.port,
                'method': net_op.method,
                'result': net_op.result.value,
                'response_code': net_op.response_code,
                'response_size': net_op.response_size,
                'duration_ms': net_op.duration_ms,
                'user_agent': net_op.user_agent,
                'error_message': net_op.error_message,
                'metadata': net_op.metadata
            })
        
        with open(output_path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        logger.info(f"Exported network audit log to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get network access statistics.
        
        Returns:
            Dictionary with access statistics
        """
        stats = {
            'total_operations': len(self.audit_log),
            'allowed_operations': sum(1 for op in self.audit_log if op.result == NetworkResult.ALLOWED),
            'denied_operations': sum(1 for op in self.audit_log if op.result == NetworkResult.DENIED),
            'blocked_operations': sum(1 for op in self.audit_log if op.result == NetworkResult.BLOCKED),
            'error_operations': sum(1 for op in self.audit_log if op.result == NetworkResult.ERROR),
            'operations_by_type': {},
            'operations_by_access_type': {},
            'hosts_accessed': set(),
            'domains_accessed': set(),
            'total_data_transferred': 0
        }
        
        # Count operations by type and collect host information
        for op in self.audit_log:
            stats['operations_by_type'][op.operation] = stats['operations_by_type'].get(op.operation, 0) + 1
            stats['operations_by_access_type'][op.access_type.value] = stats['operations_by_access_type'].get(op.access_type.value, 0) + 1
            
            if op.host:
                stats['hosts_accessed'].add(op.host)
                # Extract domain from host
                domain_parts = op.host.split('.')
                if len(domain_parts) >= 2:
                    domain = '.'.join(domain_parts[-2:])
                    stats['domains_accessed'].add(domain)
            
            if op.response_size:
                stats['total_data_transferred'] += op.response_size
        
        # Convert sets to lists for JSON serialization
        stats['hosts_accessed'] = list(stats['hosts_accessed'])
        stats['domains_accessed'] = list(stats['domains_accessed'])
        
        return stats
    
    def clear_rate_limits(self) -> None:
        """Clear all rate limiting counters."""
        with self._lock:
            self._rate_limiter.clear()
        logger.info("Rate limiting counters cleared")

# Global network access controller
_net_controller: Optional[NetworkAccessController] = None

def get_net_controller(policy: Optional[NetworkPolicy] = None) -> NetworkAccessController:
    """Get the global network access controller."""
    global _net_controller
    if _net_controller is None:
        _net_controller = NetworkAccessController(policy)
    return _net_controller

def safe_get(url: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for safe HTTP GET request."""
    controller = get_net_controller()
    return controller.safe_get(url, **kwargs)

def safe_post(url: str, data: Optional[Union[bytes, str]] = None, **kwargs) -> Dict[str, Any]:
    """Convenience function for safe HTTP POST request."""
    controller = get_net_controller()
    return controller.safe_post(url, data, **kwargs)

def safe_request(url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Convenience function for safe HTTP request."""
    controller = get_net_controller()
    return controller.safe_request(url, method, **kwargs)

def safe_dns_lookup(hostname: str) -> Optional[str]:
    """Convenience function for safe DNS lookup."""
    controller = get_net_controller()
    return controller.safe_dns_lookup(hostname)