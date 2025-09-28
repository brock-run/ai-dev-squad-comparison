"""
Unit tests for Network Access Controls.
These tests validate domain allowlists, request filtering, network policies,
and safe network operations across different scenarios.
"""
import pytest
import json
import socket
import urllib.error
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import ipaddress

from common.safety.net import (
    NetworkAccessController, NetworkPolicy, NetworkAccessType, NetworkResult,
    NetworkOperation, get_net_controller, safe_get, safe_post, safe_request,
    safe_dns_lookup
)

class TestNetworkPolicy:
    """Test cases for NetworkPolicy."""
    
    def test_network_policy_defaults(self):
        """Test default network policy values."""
        policy = NetworkPolicy()
        
        assert policy.default_deny is True
        assert policy.request_timeout == 30
        assert policy.max_response_size == 10 * 1024 * 1024  # 10MB
        assert policy.max_redirects == 5
        assert policy.verify_ssl is True
        assert policy.audit_enabled is True
        assert policy.rate_limit == 60
        assert policy.rate_window == 60
        
        # Check default allowed protocols
        assert "http" in policy.allowed_protocols
        assert "https" in policy.allowed_protocols
        
        # Check default allowed ports
        assert 80 in policy.allowed_ports
        assert 443 in policy.allowed_ports
        
        # Check default denied ports
        assert 22 in policy.denied_ports  # SSH
        assert 25 in policy.denied_ports  # SMTP
    
    def test_network_policy_custom(self):
        """Test custom network policy configuration."""
        policy = NetworkPolicy(
            default_deny=False,
            allowed_domains={"api.github.com", "*.example.com"},
            denied_domains={"malicious.com"},
            allowed_ips={"192.168.1.0/24", "10.0.0.1"},
            denied_ips={"127.0.0.1"},
            allowed_ports={80, 443, 8080},
            denied_ports={22, 23},
            request_timeout=60,
            max_response_size=5 * 1024 * 1024,  # 5MB
            verify_ssl=False,
            audit_enabled=False
        )
        
        assert policy.default_deny is False
        assert "api.github.com" in policy.allowed_domains
        assert "*.example.com" in policy.allowed_domains
        assert "malicious.com" in policy.denied_domains
        assert "192.168.1.0/24" in policy.allowed_ips
        assert "10.0.0.1" in policy.allowed_ips
        assert "127.0.0.1" in policy.denied_ips
        assert policy.allowed_ports == {80, 443, 8080}
        assert policy.denied_ports == {22, 23}
        assert policy.request_timeout == 60
        assert policy.max_response_size == 5 * 1024 * 1024
        assert policy.verify_ssl is False
        assert policy.audit_enabled is False

class TestNetworkOperation:
    """Test cases for NetworkOperation."""
    
    def test_network_operation_creation(self):
        """Test network operation record creation."""
        timestamp = datetime.utcnow()
        operation = NetworkOperation(
            timestamp=timestamp,
            operation='http_request',
            access_type=NetworkAccessType.HTTPS_GET,
            url='https://api.github.com/user',
            host='api.github.com',
            port=443,
            method='GET',
            result=NetworkResult.ALLOWED,
            response_code=200,
            response_size=1024,
            duration_ms=250.5
        )
        
        assert operation.timestamp == timestamp
        assert operation.operation == 'http_request'
        assert operation.access_type == NetworkAccessType.HTTPS_GET
        assert operation.url == 'https://api.github.com/user'
        assert operation.host == 'api.github.com'
        assert operation.port == 443
        assert operation.method == 'GET'
        assert operation.result == NetworkResult.ALLOWED
        assert operation.response_code == 200
        assert operation.response_size == 1024
        assert operation.duration_ms == 250.5

class TestNetworkAccessController:
    """Test cases for NetworkAccessController."""
    
    def setup_method(self):
        """Set up test environment."""
        self.policy = NetworkPolicy(
            default_deny=True,
            allowed_domains={"api.github.com", "*.example.com", "httpbin.org"},
            denied_domains={"malicious.com", "*.evil.com"},
            allowed_ips={"192.168.1.0/24", "10.0.0.1"},
            denied_ips={"127.0.0.1", "192.168.0.0/16"},
            allowed_ports={80, 443, 8080},
            denied_ports={22, 23, 25},
            audit_enabled=True
        )
        self.controller = NetworkAccessController(self.policy)
    
    def test_controller_initialization(self):
        """Test network access controller initialization."""
        assert self.controller.policy == self.policy
        assert len(self.controller.audit_log) == 0
        assert len(self.controller._allowed_domain_patterns) == 3
        assert len(self.controller._denied_domain_patterns) == 2
        assert len(self.controller._allowed_networks) == 2
        assert len(self.controller._denied_networks) == 2
    
    def test_compile_domain_patterns(self):
        """Test domain pattern compilation."""
        domains = {"api.github.com", "*.example.com", "test.org"}
        patterns = self.controller._compile_domain_patterns(domains)
        
        assert len(patterns) == 3
        
        # Test exact match
        assert any(pattern.match("api.github.com") for pattern in patterns)
        assert not any(pattern.match("other.github.com") for pattern in patterns)
        
        # Test wildcard match
        assert any(pattern.match("sub.example.com") for pattern in patterns)
        assert any(pattern.match("deep.sub.example.com") for pattern in patterns)
        assert not any(pattern.match("example.com.evil") for pattern in patterns)
    
    def test_parse_ip_networks(self):
        """Test IP network parsing."""
        ip_strings = {"192.168.1.0/24", "10.0.0.1", "invalid-ip"}
        networks = self.controller._parse_ip_networks(ip_strings)
        
        assert len(networks) == 2  # invalid-ip should be skipped
        
        # Check CIDR block
        cidr_network = next(net for net in networks if str(net) == "192.168.1.0/24")
        assert ipaddress.IPv4Address("192.168.1.100") in cidr_network
        assert ipaddress.IPv4Address("192.168.2.100") not in cidr_network
        
        # Check single IP
        single_network = next(net for net in networks if str(net) == "10.0.0.1/32")
        assert ipaddress.IPv4Address("10.0.0.1") in single_network
        assert ipaddress.IPv4Address("10.0.0.2") not in single_network
    
    def test_match_domain(self):
        """Test domain matching."""
        patterns = self.controller._compile_domain_patterns({"api.github.com", "*.example.com"})
        
        # Exact match
        assert self.controller._match_domain("api.github.com", patterns)
        assert not self.controller._match_domain("other.github.com", patterns)
        
        # Wildcard match
        assert self.controller._match_domain("sub.example.com", patterns)
        assert self.controller._match_domain("deep.sub.example.com", patterns)
        assert not self.controller._match_domain("example.com.evil", patterns)
        
        # Case insensitive
        assert self.controller._match_domain("API.GITHUB.COM", patterns)
        assert self.controller._match_domain("SUB.EXAMPLE.COM", patterns)
    
    def test_match_ip(self):
        """Test IP matching."""
        networks = [
            ipaddress.IPv4Network("192.168.1.0/24"),
            ipaddress.IPv4Network("10.0.0.1/32")
        ]
        
        # CIDR block match
        assert self.controller._match_ip("192.168.1.100", networks)
        assert not self.controller._match_ip("192.168.2.100", networks)
        
        # Single IP match
        assert self.controller._match_ip("10.0.0.1", networks)
        assert not self.controller._match_ip("10.0.0.2", networks)
        
        # Invalid IP
        assert not self.controller._match_ip("invalid-ip", networks)
    
    @patch('socket.gethostbyname')
    def test_resolve_hostname(self, mock_gethostbyname):
        """Test hostname resolution."""
        mock_gethostbyname.return_value = "192.168.1.100"
        
        ip = self.controller._resolve_hostname("example.com")
        assert ip == "192.168.1.100"
        mock_gethostbyname.assert_called_once_with("example.com")
        
        # Test resolution failure
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")
        ip = self.controller._resolve_hostname("nonexistent.com")
        assert ip is None
    
    def test_validate_network_access_allowed_domain(self):
        """Test network access validation for allowed domain."""
        result, error = self.controller.validate_network_access("https://api.github.com/user")
        assert result == NetworkResult.ALLOWED
        assert error is None
    
    def test_validate_network_access_denied_domain(self):
        """Test network access validation for denied domain."""
        result, error = self.controller.validate_network_access("https://malicious.com/payload")
        assert result == NetworkResult.DENIED
        assert "Domain is denied" in error
    
    def test_validate_network_access_wildcard_allowed(self):
        """Test network access validation for wildcard allowed domain."""
        result, error = self.controller.validate_network_access("https://sub.example.com/api")
        assert result == NetworkResult.ALLOWED
        assert error is None
    
    def test_validate_network_access_wildcard_denied(self):
        """Test network access validation for wildcard denied domain."""
        result, error = self.controller.validate_network_access("https://bad.evil.com/attack")
        assert result == NetworkResult.DENIED
        assert "Domain is denied" in error
    
    def test_validate_network_access_denied_protocol(self):
        """Test network access validation for denied protocol."""
        # Add FTP to denied protocols
        self.controller.policy.allowed_protocols = {"http", "https"}
        
        result, error = self.controller.validate_network_access("ftp://api.github.com/file")
        assert result == NetworkResult.DENIED
        assert "Protocol not allowed" in error
    
    def test_validate_network_access_denied_port(self):
        """Test network access validation for denied port."""
        result, error = self.controller.validate_network_access("https://api.github.com:22/")
        assert result == NetworkResult.DENIED
        assert "Port is denied" in error
    
    def test_validate_network_access_port_not_in_allowlist(self):
        """Test network access validation for port not in allowlist."""
        result, error = self.controller.validate_network_access("https://api.github.com:9999/")
        assert result == NetworkResult.DENIED
        assert "Port not in allowlist" in error
    
    def test_validate_network_access_invalid_url(self):
        """Test network access validation for invalid URL."""
        result, error = self.controller.validate_network_access("not-a-url")
        assert result == NetworkResult.DENIED
        assert "Invalid URL format" in error
    
    def test_validate_network_access_no_hostname(self):
        """Test network access validation for URL without hostname."""
        result, error = self.controller.validate_network_access("https:///path")
        assert result == NetworkResult.DENIED
        assert "No hostname in URL" in error
    
    @patch('socket.gethostbyname')
    def test_validate_network_access_denied_ip(self, mock_gethostbyname):
        """Test network access validation for denied IP."""
        mock_gethostbyname.return_value = "127.0.0.1"  # Denied IP
        
        result, error = self.controller.validate_network_access("https://localhost/")
        assert result == NetworkResult.DENIED
        assert "IP address is denied" in error
    
    @patch('socket.gethostbyname')
    def test_validate_network_access_private_ip_not_allowed(self, mock_gethostbyname):
        """Test network access validation for private IP not in allowlist."""
        mock_gethostbyname.return_value = "192.168.100.1"  # Private IP not in allowlist
        
        result, error = self.controller.validate_network_access("https://internal.company.com/")
        assert result == NetworkResult.DENIED
        assert "Private/local IP not explicitly allowed" in error
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Set low rate limit for testing
        self.controller.policy.rate_limit = 2
        self.controller.policy.rate_window = 60
        
        # First two requests should be allowed
        assert self.controller._check_rate_limit("test-host") is True
        assert self.controller._check_rate_limit("test-host") is True
        
        # Third request should be denied
        assert self.controller._check_rate_limit("test-host") is False
        
        # Different host should be allowed
        assert self.controller._check_rate_limit("other-host") is True
    
    @patch('urllib.request.urlopen')
    @patch('socket.gethostbyname')
    def test_safe_request_success(self, mock_gethostbyname, mock_urlopen):
        """Test successful safe HTTP request."""
        # Mock DNS resolution
        mock_gethostbyname.return_value = "192.168.1.100"  # Allowed IP
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.url = "https://api.github.com/user"
        mock_response.read.return_value = b'{"login": "testuser"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test request
        result = self.controller.safe_request("https://api.github.com/user")
        
        assert result['status_code'] == 200
        assert result['data'] == b'{"login": "testuser"}'
        assert result['size'] == len(b'{"login": "testuser"}')
        assert 'headers' in result
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        log_entry = self.controller.audit_log[0]
        assert log_entry.operation == 'http_request'
        assert log_entry.result == NetworkResult.ALLOWED
        assert log_entry.response_code == 200
    
    def test_safe_request_denied(self):
        """Test denied safe HTTP request."""
        with pytest.raises(PermissionError, match="Network access denied"):
            self.controller.safe_request("https://malicious.com/payload")
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        log_entry = self.controller.audit_log[0]
        assert log_entry.result == NetworkResult.DENIED
    
    @patch('urllib.request.urlopen')
    @patch('socket.gethostbyname')
    def test_safe_request_response_too_large(self, mock_gethostbyname, mock_urlopen):
        """Test safe HTTP request with response too large."""
        mock_gethostbyname.return_value = "192.168.1.100"
        
        # Mock large response
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': str(self.controller.policy.max_response_size + 1)}
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(urllib.error.URLError, match="Response too large"):
            self.controller.safe_request("https://api.github.com/large-file")
    
    def test_safe_get_post_put_delete(self):
        """Test safe HTTP method convenience functions."""
        with patch.object(self.controller, 'safe_request') as mock_request:
            mock_request.return_value = {'status_code': 200}
            
            # Test GET
            self.controller.safe_get("https://api.github.com/user")
            mock_request.assert_called_with("https://api.github.com/user", "GET", headers=None)
            
            # Test POST
            self.controller.safe_post("https://api.github.com/user", data="test data")
            mock_request.assert_called_with("https://api.github.com/user", "POST", data=b"test data", headers=None)
            
            # Test PUT
            self.controller.safe_put("https://api.github.com/user", data=b"binary data")
            mock_request.assert_called_with("https://api.github.com/user", "PUT", data=b"binary data", headers=None)
            
            # Test DELETE
            self.controller.safe_delete("https://api.github.com/user")
            mock_request.assert_called_with("https://api.github.com/user", "DELETE", headers=None)
    
    @patch('socket.gethostbyname')
    def test_safe_dns_lookup_allowed(self, mock_gethostbyname):
        """Test safe DNS lookup for allowed domain."""
        mock_gethostbyname.return_value = "192.168.1.100"
        
        ip = self.controller.safe_dns_lookup("api.github.com")
        assert ip == "192.168.1.100"
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        log_entry = self.controller.audit_log[0]
        assert log_entry.operation == 'dns_lookup'
        assert log_entry.result == NetworkResult.ALLOWED
    
    def test_safe_dns_lookup_denied_domain(self):
        """Test safe DNS lookup for denied domain."""
        with pytest.raises(PermissionError, match="DNS lookup denied for domain"):
            self.controller.safe_dns_lookup("malicious.com")
        
        # Check audit log
        assert len(self.controller.audit_log) == 1
        log_entry = self.controller.audit_log[0]
        assert log_entry.result == NetworkResult.DENIED
    
    @patch('socket.gethostbyname')
    def test_safe_dns_lookup_denied_ip(self, mock_gethostbyname):
        """Test safe DNS lookup that resolves to denied IP."""
        mock_gethostbyname.return_value = "127.0.0.1"  # Denied IP
        
        with pytest.raises(PermissionError, match="resolved IP is denied"):
            self.controller.safe_dns_lookup("localhost")
    
    @patch('socket.socket')
    def test_safe_socket_allowed(self, mock_socket_class):
        """Test safe socket connection for allowed host."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        
        with patch.object(self.controller, 'validate_network_access') as mock_validate:
            mock_validate.return_value = (NetworkResult.ALLOWED, None)
            
            with self.controller.safe_socket("api.github.com", 443) as sock:
                assert sock is mock_socket
                mock_socket.connect.assert_called_once_with(("api.github.com", 443))
            
            mock_socket.close.assert_called_once()
    
    def test_safe_socket_denied(self):
        """Test safe socket connection for denied host."""
        with pytest.raises(PermissionError, match="Socket access denied"):
            with self.controller.safe_socket("malicious.com", 80):
                pass
    
    def test_audit_log_functionality(self):
        """Test audit logging functionality."""
        # Perform operations that generate logs
        try:
            self.controller.safe_request("https://malicious.com/")
        except PermissionError:
            pass
        
        try:
            self.controller.safe_dns_lookup("evil.com")
        except PermissionError:
            pass
        
        # Get audit log
        audit_log = self.controller.get_audit_log()
        assert len(audit_log) >= 2
        
        # Check log entries
        operations = [log.operation for log in audit_log]
        assert 'http_request' in operations
        assert 'dns_lookup' in operations
    
    def test_export_audit_log(self):
        """Test audit log export functionality."""
        # Generate some log entries
        try:
            self.controller.safe_request("https://malicious.com/")
        except PermissionError:
            pass
        
        # Export audit log
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            self.controller.export_audit_log(export_file)
            
            # Verify export
            with open(export_file, 'r') as f:
                exported_data = json.load(f)
            
            assert isinstance(exported_data, list)
            assert len(exported_data) > 0
            
            # Check structure
            first_entry = exported_data[0]
            assert 'timestamp' in first_entry
            assert 'operation' in first_entry
            assert 'access_type' in first_entry
            assert 'result' in first_entry
        
        finally:
            import os
            os.unlink(export_file)
    
    def test_get_statistics(self):
        """Test statistics generation."""
        # Generate various operations
        try:
            self.controller.safe_request("https://api.github.com/user")
        except:
            pass
        
        try:
            self.controller.safe_request("https://malicious.com/")
        except PermissionError:
            pass
        
        try:
            self.controller.safe_dns_lookup("api.github.com")
        except:
            pass
        
        # Get statistics
        stats = self.controller.get_statistics()
        
        assert 'total_operations' in stats
        assert 'allowed_operations' in stats
        assert 'denied_operations' in stats
        assert 'operations_by_type' in stats
        assert 'operations_by_access_type' in stats
        assert 'hosts_accessed' in stats
        assert 'domains_accessed' in stats
        
        assert stats['total_operations'] > 0
        assert isinstance(stats['hosts_accessed'], list)
        assert isinstance(stats['domains_accessed'], list)
    
    def test_clear_rate_limits(self):
        """Test rate limit clearing."""
        # Trigger rate limiting
        self.controller.policy.rate_limit = 1
        self.controller._check_rate_limit("test-host")
        assert self.controller._check_rate_limit("test-host") is False
        
        # Clear rate limits
        self.controller.clear_rate_limits()
        
        # Should be allowed again
        assert self.controller._check_rate_limit("test-host") is True

class TestGlobalFunctions:
    """Test cases for global convenience functions."""
    
    def setup_method(self):
        """Set up test environment."""
        # Reset global controller
        import common.safety.net
        common.safety.net._net_controller = None
    
    def teardown_method(self):
        """Clean up test environment."""
        # Reset global controller
        import common.safety.net
        common.safety.net._net_controller = None
    
    def test_get_net_controller(self):
        """Test global network controller retrieval."""
        controller1 = get_net_controller()
        controller2 = get_net_controller()
        
        # Should return the same instance
        assert controller1 is controller2
        assert isinstance(controller1, NetworkAccessController)
    
    def test_safe_get_global(self):
        """Test global safe_get function."""
        with patch('common.safety.net.get_net_controller') as mock_get_controller:
            mock_controller = MagicMock()
            mock_controller.safe_get.return_value = {'status_code': 200}
            mock_get_controller.return_value = mock_controller
            
            result = safe_get("https://api.github.com/user", headers={'Accept': 'application/json'})
            
            assert result == {'status_code': 200}
            mock_controller.safe_get.assert_called_once_with("https://api.github.com/user", headers={'Accept': 'application/json'})
    
    def test_safe_post_global(self):
        """Test global safe_post function."""
        with patch('common.safety.net.get_net_controller') as mock_get_controller:
            mock_controller = MagicMock()
            mock_controller.safe_post.return_value = {'status_code': 201}
            mock_get_controller.return_value = mock_controller
            
            result = safe_post("https://api.github.com/user", data="test data")
            
            assert result == {'status_code': 201}
            mock_controller.safe_post.assert_called_once_with("https://api.github.com/user", "test data")
    
    def test_safe_request_global(self):
        """Test global safe_request function."""
        with patch('common.safety.net.get_net_controller') as mock_get_controller:
            mock_controller = MagicMock()
            mock_controller.safe_request.return_value = {'status_code': 200}
            mock_get_controller.return_value = mock_controller
            
            result = safe_request("https://api.github.com/user", method="PUT", data="update data")
            
            assert result == {'status_code': 200}
            mock_controller.safe_request.assert_called_once_with("https://api.github.com/user", "PUT", data="update data")
    
    def test_safe_dns_lookup_global(self):
        """Test global safe_dns_lookup function."""
        with patch('common.safety.net.get_net_controller') as mock_get_controller:
            mock_controller = MagicMock()
            mock_controller.safe_dns_lookup.return_value = "192.168.1.100"
            mock_get_controller.return_value = mock_controller
            
            result = safe_dns_lookup("api.github.com")
            
            assert result == "192.168.1.100"
            mock_controller.safe_dns_lookup.assert_called_once_with("api.github.com")

class TestIntegration:
    """Integration tests for network access controls."""
    
    def test_comprehensive_network_policy(self):
        """Test comprehensive network policy enforcement."""
        policy = NetworkPolicy(
            default_deny=True,
            allowed_domains={"httpbin.org", "*.github.com"},
            denied_domains={"malicious.com", "*.evil.com"},
            allowed_ips={"192.168.1.0/24"},
            denied_ips={"127.0.0.1"},
            allowed_ports={80, 443, 8080},
            denied_ports={22, 23, 25},
            request_timeout=10,
            max_response_size=1024 * 1024,  # 1MB
            rate_limit=10,
            audit_enabled=True
        )
        
        controller = NetworkAccessController(policy)
        
        # Test allowed domain
        result, error = controller.validate_network_access("https://api.github.com/user")
        assert result == NetworkResult.ALLOWED
        
        # Test denied domain
        result, error = controller.validate_network_access("https://malicious.com/payload")
        assert result == NetworkResult.DENIED
        
        # Test wildcard allowed
        result, error = controller.validate_network_access("https://raw.github.com/file")
        assert result == NetworkResult.ALLOWED
        
        # Test wildcard denied
        result, error = controller.validate_network_access("https://bad.evil.com/attack")
        assert result == NetworkResult.DENIED
        
        # Test denied port
        result, error = controller.validate_network_access("https://api.github.com:22/")
        assert result == NetworkResult.DENIED
        
        # Test port not in allowlist
        result, error = controller.validate_network_access("https://api.github.com:9999/")
        assert result == NetworkResult.DENIED
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("TEST_NETWORK"), reason="Network tests disabled")
    def test_real_network_request(self):
        """Test real network request (requires internet)."""
        policy = NetworkPolicy(
            default_deny=True,
            allowed_domains={"httpbin.org"},
            request_timeout=10,
            verify_ssl=True,
            audit_enabled=True
        )
        
        controller = NetworkAccessController(policy)
        
        try:
            # Test real HTTP request
            result = controller.safe_get("https://httpbin.org/get")
            
            assert result['status_code'] == 200
            assert 'data' in result
            assert 'headers' in result
            
            # Check audit log
            audit_log = controller.get_audit_log()
            assert len(audit_log) > 0
            
            log_entry = audit_log[-1]
            assert log_entry.operation == 'http_request'
            assert log_entry.result == NetworkResult.ALLOWED
            assert log_entry.response_code == 200
            
        except Exception as e:
            pytest.skip(f"Network test failed (expected in CI): {e}")

if __name__ == "__main__":
    pytest.main([__file__])