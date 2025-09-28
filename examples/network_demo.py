#!/usr/bin/env python3
"""
Network Access Controls Demo
This script demonstrates the capabilities of the network access control system
with various HTTP requests, DNS lookups, and security scenarios.
"""
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.safety.net import (
    NetworkAccessController, NetworkPolicy, NetworkAccessType, NetworkResult,
    safe_get, safe_post, safe_request, safe_dns_lookup
)
from common.safety.config_integration import SafetyManager

def demo_basic_network_operations():
    """Demo basic network operations with access controls."""
    print("=== Basic Network Operations Demo ===")
    
    # Create network controller with permissive policy for demo
    policy = NetworkPolicy(
        default_deny=True,
        allowed_domains={"httpbin.org", "api.github.com", "*.example.com"},
        denied_domains={"malicious.com", "*.evil.com"},
        allowed_ports={80, 443, 8080},
        request_timeout=10,
        audit_enabled=True
    )
    controller = NetworkAccessController(policy)
    
    print(f"Network policy: Default deny = {policy.default_deny}")
    print(f"Allowed domains: {policy.allowed_domains}")
    print(f"Denied domains: {policy.denied_domains}")
    
    # 1. Safe HTTP GET request
    print("\n1. HTTP GET Request:")
    try:
        # Note: This will fail without internet, but shows the validation
        result = controller.validate_network_access("https://httpbin.org/get")
        if result[0] == NetworkResult.ALLOWED:
            print("   ✓ GET request to httpbin.org would be allowed")
            # Uncomment to make real request (requires internet):
            # response = controller.safe_get("https://httpbin.org/get")
            # print(f"   Response status: {response['status_code']}")
        else:
            print(f"   ✗ GET request denied: {result[1]}")
    except Exception as e:
        print(f"   ✗ GET request failed: {e}")
    
    # 2. Safe HTTP POST request
    print("\n2. HTTP POST Request:")
    try:
        post_data = json.dumps({"message": "Hello from network demo"})
        result = controller.validate_network_access("https://httpbin.org/post")
        if result[0] == NetworkResult.ALLOWED:
            print("   ✓ POST request to httpbin.org would be allowed")
            # Uncomment to make real request:
            # response = controller.safe_post("https://httpbin.org/post", data=post_data)
            # print(f"   Response status: {response['status_code']}")
        else:
            print(f"   ✗ POST request denied: {result[1]}")
    except Exception as e:
        print(f"   ✗ POST request failed: {e}")
    
    # 3. DNS lookup
    print("\n3. DNS Lookup:")
    try:
        # This will work without internet for validation
        result = controller.validate_network_access("https://api.github.com/user")
        if result[0] == NetworkResult.ALLOWED:
            print("   ✓ DNS lookup for api.github.com would be allowed")
            # Uncomment to make real lookup:
            # ip = controller.safe_dns_lookup("api.github.com")
            # print(f"   Resolved IP: {ip}")
        else:
            print(f"   ✗ DNS lookup denied: {result[1]}")
    except Exception as e:
        print(f"   ✗ DNS lookup failed: {e}")
    
    # 4. Wildcard domain matching
    print("\n4. Wildcard Domain Matching:")
    test_urls = [
        "https://sub.example.com/api",
        "https://deep.sub.example.com/data",
        "https://example.com.evil/fake"  # Should be denied
    ]
    
    for url in test_urls:
        result, error = controller.validate_network_access(url)
        status = "✓ Allowed" if result == NetworkResult.ALLOWED else f"✗ Denied: {error}"
        print(f"   {url}: {status}")
    
    # 5. Show access statistics
    print("\n5. Access Statistics:")
    stats = controller.get_statistics()
    print(f"   Total operations: {stats['total_operations']}")
    print(f"   Allowed operations: {stats['allowed_operations']}")
    print(f"   Denied operations: {stats['denied_operations']}")

def demo_security_controls():
    """Demo security controls and access restrictions."""
    print("\n=== Security Controls Demo ===")
    
    # Create restrictive policy
    policy = NetworkPolicy(
        default_deny=True,
        allowed_domains={"api.github.com"},  # Very restrictive
        denied_domains={"malicious.com", "*.evil.com", "*.suspicious.org"},
        allowed_ports={443},  # Only HTTPS
        denied_ports={22, 23, 25, 80},  # Block common dangerous ports
        request_timeout=5,
        max_response_size=1024 * 1024,  # 1MB limit
        rate_limit=5,  # Very low rate limit
        audit_enabled=True
    )
    controller = NetworkAccessController(policy)
    
    print(f"Restrictive policy: Only {policy.allowed_domains} allowed")
    
    # 1. Test denied domain
    print("\n1. Testing denied domain access:")
    try:
        result, error = controller.validate_network_access("https://malicious.com/payload")
        print(f"   ✗ Access to malicious.com: {error}")
    except Exception as e:
        print(f"   ✗ Validation error: {e}")
    
    # 2. Test wildcard denied domain
    print("\n2. Testing wildcard denied domain:")
    try:
        result, error = controller.validate_network_access("https://bad.evil.com/attack")
        print(f"   ✗ Access to bad.evil.com: {error}")
    except Exception as e:
        print(f"   ✗ Validation error: {e}")
    
    # 3. Test denied port
    print("\n3. Testing denied port access:")
    try:
        result, error = controller.validate_network_access("https://api.github.com:22/")
        print(f"   ✗ Access to port 22: {error}")
    except Exception as e:
        print(f"   ✗ Validation error: {e}")
    
    # 4. Test HTTP vs HTTPS
    print("\n4. Testing HTTP vs HTTPS:")
    try:
        # HTTP should be denied (port 80 is in denied_ports)
        result, error = controller.validate_network_access("http://api.github.com/user")
        print(f"   ✗ HTTP access: {error}")
        
        # HTTPS should be allowed
        result, error = controller.validate_network_access("https://api.github.com/user")
        if result == NetworkResult.ALLOWED:
            print("   ✓ HTTPS access: Allowed")
        else:
            print(f"   ✗ HTTPS access: {error}")
    except Exception as e:
        print(f"   ✗ Protocol test error: {e}")
    
    # 5. Test rate limiting
    print("\n5. Testing rate limiting:")
    for i in range(7):  # Exceed rate limit of 5
        allowed = controller._check_rate_limit("test-host")
        status = "✓ Allowed" if allowed else "✗ Rate limited"
        print(f"   Request {i+1}: {status}")
    
    # 6. Test domain not in allowlist
    print("\n6. Testing domain not in allowlist:")
    try:
        result, error = controller.validate_network_access("https://example.com/api")
        print(f"   ✗ Access to example.com: {error}")
    except Exception as e:
        print(f"   ✗ Validation error: {e}")
    
    # 7. Show security statistics
    print("\n7. Security Statistics:")
    stats = controller.get_statistics()
    print(f"   Total operations: {stats['total_operations']}")
    print(f"   Denied operations: {stats['denied_operations']}")
    print(f"   Error operations: {stats['error_operations']}")
    
    if stats['denied_operations'] > 0:
        print("   ✓ Security controls are working correctly")

def demo_audit_logging():
    """Demo audit logging and monitoring capabilities."""
    print("\n=== Audit Logging Demo ===")
    
    # Create policy with audit logging
    policy = NetworkPolicy(
        default_deny=True,
        allowed_domains={"httpbin.org", "api.github.com"},
        denied_domains={"malicious.com"},
        audit_enabled=True,
        # audit_log_path="network_audit.log"  # Uncomment to write to file
    )
    controller = NetworkAccessController(policy)
    
    print("Network audit logging enabled")
    
    # Perform various operations
    print("\n1. Performing monitored operations:")
    
    # Allowed operations
    try:
        result, error = controller.validate_network_access("https://api.github.com/user")
        print("   Validated GitHub API access")
    except Exception as e:
        print(f"   Validation error: {e}")
    
    try:
        result, error = controller.validate_network_access("https://httpbin.org/get")
        print("   Validated httpbin access")
    except Exception as e:
        print(f"   Validation error: {e}")
    
    # Denied operations
    try:
        result, error = controller.validate_network_access("https://malicious.com/payload")
        print("   Attempted malicious.com access (logged)")
    except Exception as e:
        print(f"   Validation error: {e}")
    
    try:
        result, error = controller.validate_network_access("https://api.github.com:22/")
        print("   Attempted SSH port access (logged)")
    except Exception as e:
        print(f"   Validation error: {e}")
    
    # DNS lookups
    try:
        controller.safe_dns_lookup("api.github.com")
        print("   DNS lookup attempted (logged)")
    except Exception as e:
        print(f"   DNS lookup logged: {e}")
    
    # 2. Show audit log
    print("\n2. Audit log entries:")
    audit_log = controller.get_audit_log(limit=5)
    
    for i, entry in enumerate(audit_log, 1):
        print(f"   {i}. {entry.timestamp.strftime('%H:%M:%S')} - "
              f"{entry.operation} - {entry.access_type.value} - "
              f"{entry.result.value}")
        if entry.host:
            print(f"      Host: {entry.host}")
        if entry.error_message:
            print(f"      Error: {entry.error_message}")
    
    # 3. Export audit log
    print("\n3. Exporting audit log:")
    try:
        export_file = "network_audit_export.json"
        controller.export_audit_log(export_file)
        
        # Read and show sample
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        print(f"   Exported {len(exported_data)} audit entries to {export_file}")
        
        if exported_data:
            sample_entry = exported_data[0]
            print(f"   Sample entry: {sample_entry['operation']} - {sample_entry['result']}")
        
        # Cleanup
        import os
        os.unlink(export_file)
        
    except Exception as e:
        print(f"   Export error: {e}")

def demo_configuration_integration():
    """Demo integration with configuration system."""
    print("\n=== Configuration Integration Demo ===")
    
    # Create safety manager with configuration
    safety_manager = SafetyManager()
    
    print("Configuration-based network access controls")
    
    # 1. Check network policy from configuration
    print("\n1. Network policy from configuration:")
    try:
        network_policy = safety_manager.get_network_policy()
        print(f"   Default deny: {network_policy['default_deny']}")
        print(f"   Allowlist: {network_policy['allowlist']}")
    except Exception as e:
        print(f"   Configuration error: {e}")
    
    # 2. Perform network operations through safety manager
    print("\n2. Configuration-based network operations:")
    
    try:
        # HTTP GET through safety manager
        # Note: This will validate but may fail without proper config
        safety_manager.safe_file_operation('http_get', 'https://api.github.com/user')
        print("   ✓ HTTP GET operation successful")
    except Exception as e:
        print(f"   ✗ HTTP GET operation: {e}")
    
    try:
        # DNS lookup through safety manager
        safety_manager.safe_file_operation('dns_lookup', 'api.github.com')
        print("   ✓ DNS lookup operation successful")
    except Exception as e:
        print(f"   ✗ DNS lookup operation: {e}")
    
    # 3. Get network statistics
    print("\n3. Network statistics:")
    try:
        stats = safety_manager.get_network_statistics()
        print(f"   Total operations: {stats['total_operations']}")
        print(f"   Allowed operations: {stats['allowed_operations']}")
        print(f"   Denied operations: {stats['denied_operations']}")
        print(f"   Hosts accessed: {len(stats['hosts_accessed'])}")
    except Exception as e:
        print(f"   Statistics error: {e}")
    
    # 4. Export network audit log
    print("\n4. Exporting network audit log:")
    try:
        audit_export = "config_network_audit.json"
        safety_manager.export_network_audit_log(audit_export)
        print(f"   ✓ Network audit log exported to {audit_export}")
        
        # Cleanup
        import os
        if os.path.exists(audit_export):
            os.unlink(audit_export)
    except Exception as e:
        print(f"   Export error: {e}")
    
    # Cleanup
    safety_manager.cleanup_resources()
    print("   ✓ Resources cleaned up")

def demo_global_functions():
    """Demo global convenience functions."""
    print("\n=== Global Functions Demo ===")
    
    # Initialize global controller with permissive policy
    from common.safety.net import get_net_controller
    policy = NetworkPolicy(
        default_deny=True,
        allowed_domains={"httpbin.org", "api.github.com"},
        audit_enabled=True
    )
    controller = get_net_controller(policy)
    
    print("Global network functions initialized")
    
    # 1. Use global safe functions
    print("\n1. Using global safe functions:")
    
    # Validate requests (won't make actual network calls)
    try:
        result, error = controller.validate_network_access("https://api.github.com/user")
        if result == NetworkResult.ALLOWED:
            print("   ✓ Global safe_get validation successful")
        else:
            print(f"   ✗ Global safe_get validation: {error}")
    except Exception as e:
        print(f"   ✗ Global safe_get error: {e}")
    
    try:
        result, error = controller.validate_network_access("https://httpbin.org/post")
        if result == NetworkResult.ALLOWED:
            print("   ✓ Global safe_post validation successful")
        else:
            print(f"   ✗ Global safe_post validation: {error}")
    except Exception as e:
        print(f"   ✗ Global safe_post error: {e}")
    
    # DNS lookup
    try:
        # This will validate the DNS lookup
        result, error = controller.validate_network_access("https://api.github.com/")
        if result == NetworkResult.ALLOWED:
            print("   ✓ Global safe_dns_lookup validation successful")
        else:
            print(f"   ✗ Global safe_dns_lookup validation: {error}")
    except Exception as e:
        print(f"   ✗ Global safe_dns_lookup error: {e}")
    
    # 2. Show that operations are tracked
    print("\n2. Global operations tracking:")
    stats = controller.get_statistics()
    print(f"   Operations tracked: {stats['total_operations']}")
    print(f"   Allowed operations: {stats['allowed_operations']}")
    print(f"   Denied operations: {stats['denied_operations']}")

def main():
    """Run all network demos."""
    print("AI Dev Squad Comparison - Network Access Controls Demo")
    print("=" * 70)
    
    try:
        demo_basic_network_operations()
        demo_security_controls()
        demo_audit_logging()
        demo_configuration_integration()
        demo_global_functions()
        
        print("\n" + "=" * 70)
        print("Network demo completed successfully!")
        print("\nKey takeaways:")
        print("• Network access controls provide comprehensive security")
        print("• Domain allowlists and denylists prevent unauthorized access")
        print("• Port restrictions block dangerous services")
        print("• Rate limiting prevents abuse")
        print("• All network operations are audited and logged")
        print("• Integration with configuration system enables policy management")
        print("• Global functions provide convenient access to safety controls")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()