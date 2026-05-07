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

print("Finished generating API Documentation pages.")
