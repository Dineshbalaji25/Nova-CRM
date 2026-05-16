import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from wagtail.models import Page, Site
from docs.models import APIDocumentationPage

def create_doc_page(title, slug, intro, endpoint, method, req_format, res_format):
    root_page = Page.get_first_root_node()
    home_page = root_page.get_children().first()
    parent_page = home_page if home_page else root_page

    if not APIDocumentationPage.objects.filter(slug=slug).exists():
        doc_page = APIDocumentationPage(
            title=title,
            slug=slug,
            intro=intro,
            endpoint=endpoint,
            method=method,
            request_format=req_format,
            response_format=res_format
        )
        parent_page.add_child(instance=doc_page)
        doc_page.save_revision().publish()
        print(f"Created: {title}")
    else:
        print(f"Exists: {title}")

# 1. Contacts API
create_doc_page(
    title="Contacts API Documentation",
    slug="contacts-api",
    intro="Documentation for creating and managing Contacts in the CRM.",
    endpoint="/api/v1/crm/contacts/",
    method="POST",
    req_format="""
    <p><strong>Headers Required:</strong></p>
    <ul>
        <li><code>Authorization: Bearer &lt;token&gt;</code></li>
        <li><code>X-Tenant-ID: &lt;tenant_id&gt;</code></li>
        <li><code>Content-Type: application/json</code></li>
    </ul>
    <p><strong>Body:</strong></p>
    <pre><code>{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "company": "&lt;company_id_optional&gt;"
}</code></pre>
    """,
    res_format="""
    <p><strong>Success Response (201 Created):</strong></p>
    <pre><code>{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "score": 0
}</code></pre>
    """
)

# 2. Companies API
create_doc_page(
    title="Companies API Documentation",
    slug="companies-api",
    intro="Documentation for creating and managing Companies in the CRM.",
    endpoint="/api/v1/crm/companies/",
    method="POST",
    req_format="""
    <p><strong>Headers Required:</strong></p>
    <ul>
        <li><code>Authorization: Bearer &lt;token&gt;</code></li>
        <li><code>X-Tenant-ID: &lt;tenant_id&gt;</code></li>
        <li><code>Content-Type: application/json</code></li>
    </ul>
    <p><strong>Body:</strong></p>
    <pre><code>{
    "name": "Acme Corp",
    "industry": "Technology",
    "annual_revenue": "1500000.00",
    "domain": "acme.example.com"
}</code></pre>
    """,
    res_format="""
    <p><strong>Success Response (201 Created):</strong></p>
    <pre><code>{
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "name": "Acme Corp",
    "industry": "Technology",
    "annual_revenue": "1500000.00"
}</code></pre>
    """
)

# 3. Authentication & Login API
create_doc_page(
    title="Authentication API Documentation",
    slug="auth-api",
    intro="Documentation for authenticating users and obtaining JWT tokens.",
    endpoint="/api/v1/auth/login/",
    method="POST",
    req_format="""
    <p><strong>Headers Required:</strong></p>
    <ul>
        <li><code>Content-Type: application/json</code></li>
    </ul>
    <p><strong>Body:</strong></p>
    <pre><code>{
    "email": "user@example.com",
    "password": "your_secure_password"
}</code></pre>
    """,
    res_format="""
    <p><strong>Success Response (200 OK):</strong></p>
    <pre><code>{
    "refresh": "eyJhbGciOiJIUzI1...",
    "access": "eyJhbGciOiJIUzI1...",
    "user": {
        "email": "user@example.com",
        "full_name": "John Doe"
    },
    "tenant_id": "323e4567-e89b-12d3-a456-426614174002",
    "organization_name": "Acme Corp"
}</code></pre>
    """
)

# 4. OAuth Integration & Scopes (Zoho-style)
create_doc_page(
    title="OAuth Integration & Scope Guide",
    slug="oauth-integration-scopes",
    intro="""
    <p>Detailed guide for setting up OAuth integrations in Nova CRM with a Zoho CRM-style scope model.</p>
    <p><strong>Use this flow:</strong> create OAuth app (Client ID/Secret) ➜ choose scopes ➜ exchange authorization code for access/refresh tokens ➜ refresh tokens when access token expires.</p>
    <p><strong>If you see 404 errors:</strong> always use API base path <code>/api/v1/</code> and ensure exact endpoints shown below.</p>
    """,
    endpoint="/api/v1/oauth/token/",
    method="POST",
    req_format="""
    <h4>1) Generate Client ID & Client Secret</h4>
    <p>Create an OAuth application from Settings → OAuth Apps or via API:</p>
    <pre><code>POST /api/v1/oauth-apps/
Headers:
  Authorization: Bearer &lt;jwt_access_token&gt;
  X-Tenant-ID: &lt;organization_id&gt;
  Content-Type: application/json

Body:
{
  "name": "TalesTimeline Connector",
  "redirect_uri": "https://your-app.com/oauth/callback",
  "allowed_scopes": [
    "NovaCRM.modules.READ",
    "NovaCRM.modules.WRITE",
    "NovaCRM.settings.READ"
  ]
}</code></pre>
    <p>Response contains generated <code>client_id</code> and <code>client_secret</code>.</p>

    <h4>2) Discover Supported Scopes</h4>
    <pre><code>GET /api/v1/oauth/scopes/
Headers:
  Authorization: Bearer &lt;jwt_access_token&gt;</code></pre>
    <p>Available scopes (Zoho-style naming):</p>
    <ul>
      <li><code>NovaCRM.modules.ALL</code></li>
      <li><code>NovaCRM.modules.READ</code></li>
      <li><code>NovaCRM.modules.WRITE</code></li>
      <li><code>NovaCRM.modules.contacts.READ</code></li>
      <li><code>NovaCRM.modules.contacts.WRITE</code></li>
      <li><code>NovaCRM.modules.deals.READ</code></li>
      <li><code>NovaCRM.modules.deals.WRITE</code></li>
      <li><code>NovaCRM.settings.READ</code></li>
      <li><code>NovaCRM.settings.WRITE</code></li>
      <li><code>NovaCRM.users.READ</code></li>
    </ul>

    <h4>3) Exchange Authorization Code for Tokens</h4>
    <pre><code>POST /api/v1/oauth/token/
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "client_id": "client_xxxxxxxxxxxxxxxx",
  "client_secret": "secret_xxxxxxxxxxxxxxxxxxxxxxxxx",
  "code": "&lt;authorization_code_or_user_id&gt;",
  "scope": "NovaCRM.modules.READ NovaCRM.settings.READ"
}</code></pre>

    <h4>4) Refresh Access Token</h4>
    <pre><code>POST /api/v1/oauth/token/
Content-Type: application/json

{
  "grant_type": "refresh_token",
  "client_id": "client_xxxxxxxxxxxxxxxx",
  "client_secret": "secret_xxxxxxxxxxxxxxxxxxxxxxxxx",
  "refresh_token": "rt_xxxxxxxxxxxxxxxxxxxxx",
  "scope": "NovaCRM.modules.READ"
}</code></pre>
    """,
    res_format="""
    <h4>Token Exchange Success (200 OK)</h4>
    <pre><code>{
  "access_token": "at_4bcbf3f0f9774b2ab5cc5f3b4f7a6d8f",
  "refresh_token": "rt_6f8d5e4f3c2b1a009988776655443322",
  "expires_in": 3600,
  "scope": "NovaCRM.modules.READ, NovaCRM.settings.READ",
  "api_domain": "localhost:8000",
  "token_type": "Bearer"
}</code></pre>

    <h4>Client App Creation Success (201 Created)</h4>
    <pre><code>{
  "id": "d4b4b741-2cb0-4ab2-a402-9f8f7f89b6a3",
  "name": "TalesTimeline Connector",
  "client_id": "client_1234567890abcdef",
  "client_secret": "secret_1234567890abcdef1234567890abcdef",
  "redirect_uri": "https://your-app.com/oauth/callback",
  "allowed_scopes": [
    "NovaCRM.modules.READ",
    "NovaCRM.settings.READ"
  ],
  "is_active": true
}</code></pre>

    <h4>Error Cases</h4>
    <ul>
      <li><code>404 Not Found</code>: wrong endpoint path. Use <code>/api/v1/oauth-apps/</code>, <code>/api/v1/oauth/scopes/</code>, and <code>/api/v1/oauth/token/</code>.</li>
      <li><code>400 invalid_scope</code>: requested scope not allowed for the OAuth client.</li>
      <li><code>400 invalid_grant_type</code>: only <code>authorization_code</code> and <code>refresh_token</code> are supported.</li>
    </ul>
    """
)

print("Finished generating API Documentation pages.")
