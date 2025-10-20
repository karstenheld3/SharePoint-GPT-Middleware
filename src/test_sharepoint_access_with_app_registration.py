import logging, os
from dotenv import load_dotenv
from office365.sharepoint.client_context import ClientContext
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography import x509
from cryptography.hazmat.backends import default_backend

load_dotenv()

###
# Simple test script to connect to SharePoint using Office365-REST-Python-Client
# with client credentials (App Registration).
#
# Required Azure AD permissions:
#    - SharePoint: Sites.Read.All or Sites.ReadWrite.All or Sites.Selected (Application permission)
#
# Required .env variables:
#    CRAWLER_CLIENT_ID=<your_app_registration_client_id>
#    CRAWLER_TENANT_ID=<your_azure_tenant_id>
#    CRAWLER_CLIENT_CERTIFICATE_PFX_FILE=<filename_of_pfx_file>
#    CRAWLER_CLIENT_CERTIFICATE_PASSWORD=<certificate_password>
#    LOCAL_PERSISTENT_STORAGE_PATH=<path_to_storage_directory>
###

# Load credentials from .env file
client_id = os.environ.get('CRAWLER_CLIENT_ID')
tenant_id = os.environ.get('CRAWLER_TENANT_ID')
cert_filename = os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PFX_FILE')
cert_password = os.environ.get('CRAWLER_CLIENT_CERTIFICATE_PASSWORD')
persistent_storage_path = os.environ.get('LOCAL_PERSISTENT_STORAGE_PATH')

# Target SharePoint site and document library
sharepoint_root_url = "https://whizzyapps.sharepoint.com/sites/AiSearchTest01"
document_library_url_part = "/Shared Documents"

# Validate required credentials
if not client_id:
    raise ValueError("CRAWLER_CLIENT_ID is not set in the .env file")
if not tenant_id:
    raise ValueError("CRAWLER_TENANT_ID is not set in the .env file")
if not cert_filename:
    raise ValueError("CRAWLER_CLIENT_CERTIFICATE_PFX_FILE is not set in the .env file")
if not cert_password:
    raise ValueError("CRAWLER_CLIENT_CERTIFICATE_PASSWORD is not set in the .env file")
if not persistent_storage_path:
    raise ValueError("LOCAL_PERSISTENT_STORAGE_PATH is not set in the .env file")

# Build full certificate path
cert_file = os.path.join(persistent_storage_path, cert_filename)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"\n{'='*80}")
print(f"Testing SharePoint Access with Client Credentials")
print(f"{'='*80}")
print(f"SharePoint URL: {sharepoint_root_url}")
print(f"Document Library: {document_library_url_part}")
print(f"{'='*80}\n")

# Step 1: Connect to SharePoint using certificate credentials
print("Step 1: Connecting to SharePoint...")
try:
    # Load and convert PFX to PEM format (required by with_client_certificate)
    with open(cert_file, 'rb') as f:
        pfx_data = f.read()
    
    # Extract private key and certificate from PFX
    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data,
        cert_password.encode() if cert_password else None,
        backend=default_backend()
    )
    
    # Create temporary PEM file
    pem_file = cert_file.replace('.pfx', '_temp.pem')
    with open(pem_file, 'wb') as f:
        # Write private key
        f.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ))
        # Write certificate
        f.write(certificate.public_bytes(Encoding.PEM))
    
    # Get certificate thumbprint
    thumbprint = certificate.fingerprint(certificate.signature_hash_algorithm).hex().upper()
    
    # Connect using certificate-based authentication
    # The library handles MSAL token acquisition internally
    ctx = ClientContext(sharepoint_root_url).with_client_certificate(
        tenant=tenant_id,
        client_id=client_id,
        thumbprint=thumbprint,
        cert_path=pem_file
    )
    
    # Test connection by getting web properties
    web = ctx.web.get().execute_query()
    
    print(f"✅ Connected successfully!")
    print(f"  Site Title: {web.properties.get('Title', 'N/A')}")
    print(f"  Site URL: {web.properties.get('Url', 'N/A')}")
    print(f"  Description: {web.properties.get('Description', 'N/A')}")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    exit(1)

# Step 2: Access the document library
print(f"\nStep 2: Accessing document library '{document_library_url_part}'...")
try:
    # Construct the server-relative URL for the document library
    from urllib.parse import urlparse
    parsed_url = urlparse(sharepoint_root_url)
    site_path = parsed_url.path.rstrip('/')
    library_server_relative_url = site_path + document_library_url_part
    
    # Get the document library
    document_library = ctx.web.get_list(library_server_relative_url).get().execute_query()
    
    print(f"✅ Document library accessed successfully!")
    print(f"  Title: {document_library.properties.get('Title', 'N/A')}")
    print(f"  Item Count: {document_library.properties.get('ItemCount', 'N/A')}")
except Exception as e:
    print(f"❌ Failed to access document library: {str(e)}")
    exit(1)

# Step 3: Get files from the document library
print(f"\nStep 3: Retrieving files from the library...")
try:
    # Query for files only (FSObjType = 0 means file, 1 means folder)
    items = document_library.items.select([
        "Id",
        "FileLeafRef",
        "FileRef",
        "File/Length",
        "Modified"
    ]).expand(["File"]).filter("FSObjType eq 0").top(10).get().execute_query()
    
    print(f"✅ Retrieved {len(items)} file(s)")
    
    if items:
        print(f"\nFiles in '{document_library_url_part}':")
        for i, item in enumerate(items, 1):
            filename = item.properties.get('FileLeafRef', 'N/A')
            # Access File object's length property
            file_obj = item.properties.get('File')
            file_size = file_obj.properties.get('Length', 0) if file_obj and hasattr(file_obj, 'properties') else 0
            modified = item.properties.get('Modified', 'N/A')
            file_ref = item.properties.get('FileRef', 'N/A')
            
            print(f"\n  {i}. {filename}")
            print(f"     Size: {int(file_size):,} bytes")
            print(f"     Modified: {modified}")
            print(f"     Path: {file_ref}")
    else:
        print("\n⚠ No files found in the library")
        
except Exception as e:
    print(f"❌ Failed to retrieve files: {str(e)}")
    exit(1)

print(f"\n{'='*80}")
print(f"Test completed successfully!")
print(f"{'='*80}\n")
