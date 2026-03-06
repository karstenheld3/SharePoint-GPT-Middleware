"""Test SharePoint connectivity for list access."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from routers_v2.common_sharepoint_functions_v2 import connect_to_site_using_client_id_and_certificate

# Configuration
SITE_URL = "https://whizzyapps.sharepoint.com/sites/AiSearchTest01"
LIST_NAME = "Security training catalog"

def test_sharepoint_connection():
    """Test basic SharePoint connectivity using certificate auth."""
    print(f"Testing SharePoint connection to: {SITE_URL}")
    
    # Get crawler credentials from environment
    client_id = os.getenv("CRAWLER_CLIENT_ID")
    cert_file = os.getenv("CRAWLER_CLIENT_CERTIFICATE_PFX_FILE")
    cert_password = os.getenv("CRAWLER_CLIENT_CERTIFICATE_PASSWORD") or ""
    tenant = os.getenv("CRAWLER_TENANT_ID") or os.getenv("AZURE_TENANT_ID")
    storage_path = os.getenv("LOCAL_PERSISTENT_STORAGE_PATH")
    
    if not all([client_id, cert_file, tenant]):
        print("ERROR: Missing CRAWLER_CLIENT_ID, CRAWLER_CLIENT_CERTIFICATE_PFX_FILE, or CRAWLER_SHAREPOINT_TENANT_NAME")
        return False
    
    # Build full cert path
    cert_path = os.path.join(storage_path, cert_file) if storage_path else cert_file
    print(f"Using client_id: {client_id[:8]}...")
    print(f"Certificate: {cert_path}")
    print(f"Tenant: {tenant}")
    
    if not os.path.exists(cert_path):
        print(f"ERROR: Certificate file not found: {cert_path}")
        return False
    
    try:
        # Create context using the same function as the crawler
        ctx = connect_to_site_using_client_id_and_certificate(
            site_url=SITE_URL,
            client_id=client_id,
            tenant_id=tenant,
            cert_path=cert_path,
            cert_password=cert_password
        )
        
        # Test 1: Get web info
        print("\n1. Testing web access...")
        web = ctx.web
        ctx.load(web)
        ctx.execute_query()
        print(f"   OK - Web title: '{web.properties['Title']}'")
        
        # Test 2: Get lists
        print("\n2. Testing lists access...")
        lists = ctx.web.lists
        ctx.load(lists)
        ctx.execute_query()
        list_titles = [lst.properties['Title'] for lst in lists]
        print(f"   OK - Found {len(list_titles)} lists")
        
        # Test 3: Check if target list exists
        print(f"\n3. Looking for list '{LIST_NAME}'...")
        if LIST_NAME in list_titles:
            print(f"   OK - List '{LIST_NAME}' found")
        else:
            print(f"   WARNING - List '{LIST_NAME}' not found")
            print(f"   Available lists: {list_titles}")
            return False
        
        # Test 4: Get list items
        print(f"\n4. Getting items from '{LIST_NAME}'...")
        target_list = ctx.web.lists.get_by_title(LIST_NAME)
        items = target_list.items.get().top(10).execute_query()
        print(f"   OK - Retrieved {len(items)} items")
        
        # Test 5: Get list fields
        print(f"\n5. Getting fields from '{LIST_NAME}'...")
        fields = target_list.fields.get().filter("Hidden eq false").execute_query()
        field_names = [f.properties.get('InternalName', 'N/A') for f in fields]
        print(f"   OK - Found {len(field_names)} visible fields")
        print(f"   Fields: {field_names[:10]}...")
        
        print("\n" + "="*50)
        print("All tests PASSED!")
        return True
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_sharepoint_connection()
    sys.exit(0 if success else 1)
