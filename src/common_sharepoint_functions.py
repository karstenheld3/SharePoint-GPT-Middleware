# Common functions for SharePoint operations using Office365-REST-Python-Client
# https://pypi.org/project/Office365-REST-Python-Client/#Working-with-SharePoint-API
from office365.sharepoint.client_context import ClientContext


def connect_to_site_using_client_id(site_url: str, client_id: str, client_secret: str) -> ClientContext:
  """
  Connect to a SharePoint site using client credentials (App-Only authentication).
  This method uses the client credentials flow (OAuth 2.0) to authenticate with SharePoint Online or SharePoint on-premises.
  
  Args:
    site_url: The SharePoint site URL (e.g., 'https://contoso.sharepoint.com/sites/mysite')
    client_id: The OAuth client ID of the registered application
    client_secret: The client secret associated with the application
    
  Returns:
    ClientContext: An authenticated SharePoint client context object
  """
  ctx = ClientContext(site_url).with_credentials(client_id=client_id, client_secret=client_secret)
  return ctx