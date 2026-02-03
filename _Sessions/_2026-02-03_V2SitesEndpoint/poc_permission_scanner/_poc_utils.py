"""
Shared utilities for Permission Scanner POC scripts.
"""
import os
import sys
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Add src to path for imports from middleware
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from office365.sharepoint.client_context import ClientContext
from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate


def get_poc_config() -> dict:
    """
    Load environment variables and build config dict.
    Raises ValueError if required vars are missing.
    """
    load_dotenv()
    
    required_vars = [
        'CRAWLER_SELFTEST_SHAREPOINT_SITE',
        'CRAWLER_CLIENT_ID',
        'CRAWLER_TENANT_ID',
        'CRAWLER_CLIENT_CERTIFICATE_PFX_FILE',
        'CRAWLER_CLIENT_CERTIFICATE_PASSWORD',
        'LOCAL_PERSISTENT_STORAGE_PATH'
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    persistent_storage = os.environ.get('LOCAL_PERSISTENT_STORAGE_PATH')
    cert_filename = os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PFX_FILE')
    cert_path = os.path.join(persistent_storage, cert_filename)
    
    if not os.path.exists(cert_path):
        raise ValueError(f"Certificate file not found: {cert_path}")
    
    return {
        'site_url': os.environ.get('CRAWLER_SELFTEST_SHAREPOINT_SITE'),
        'client_id': os.environ.get('CRAWLER_CLIENT_ID'),
        'tenant_id': os.environ.get('CRAWLER_TENANT_ID'),
        'cert_path': cert_path,
        'cert_password': os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PASSWORD')
    }


def get_sharepoint_context(config: dict) -> ClientContext:
    """Create authenticated SharePoint context using certificate."""
    return connect_to_site_using_client_id_and_certificate(
        site_url=config['site_url'],
        client_id=config['client_id'],
        tenant_id=config['tenant_id'],
        cert_path=config['cert_path'],
        cert_password=config['cert_password']
    )


def print_header(script_name: str, config: dict) -> None:
    """Print formatted script header."""
    print("=" * 60)
    print(f"  {script_name}")
    print("=" * 60)
    print(f"  Site: {config['site_url']}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    """Print formatted test result."""
    status = "PASS" if passed else "FAIL"
    dots = "." * (45 - len(test_name))
    print(f"{test_name} {dots} {status}")
    if message:
        print(f"  - {message}")


def print_skip(test_name: str, reason: str) -> None:
    """Print skipped test."""
    dots = "." * (45 - len(test_name))
    print(f"{test_name} {dots} SKIP")
    print(f"  - {reason}")


def print_summary(passed: int, failed: int, skipped: int) -> None:
    """Print final summary."""
    print()
    print("=" * 60)
    print(f"SUMMARY: {passed} PASS, {failed} FAIL, {skipped} SKIP")
    print("=" * 60)
