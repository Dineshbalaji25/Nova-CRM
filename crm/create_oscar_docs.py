import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from wagtail.models import Page
from docs.models import APIDocumentationPage
from apps.users.models import OAUTH_SCOPE_CHOICES

def create_or_update_doc_page(title, slug, intro, endpoint, method, req_format, res_format):
    root_page = Page.get_first_root_node()
    home_page = root_page.get_children().first()
    parent_page = home_page if home_page else root_page

    existing_page = APIDocumentationPage.objects.filter(slug=slug).first()
    if existing_page:
        existing_page.title = title
        existing_page.intro = intro
        existing_page.endpoint = endpoint
        existing_page.method = method
        existing_page.request_format = req_format
        existing_page.response_format = res_format
        existing_page.save_revision().publish()
        print(f"Updated: {title}")
    else:
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

scopes_list = "".join([f"<li><code>{s}</code></li>" for s in OAUTH_SCOPE_CHOICES])

create_or_update_doc_page(
    title="Django Oscar OAuth Integration Guide",
    slug="django-oscar-oauth-integration",
    intro=f"""
    <h2>Integrating Nova CRM OAuth with Django Oscar</h2>
    <p>This document explains how to integrate Django Oscar with Nova CRM using our OAuth provider. You will be able to synchronize customers, products, and orders between Oscar and Nova CRM securely.</p>
    
    <h3>How it works</h3>
    <p>The integration utilizes the OAuth 2.0 Client Credentials and Authorization Code grants. Django Oscar acts as the OAuth Client. Nova CRM acts as the OAuth Provider (Authorization Server). Oscar uses the Access Token to securely call Nova CRM's REST API.</p>
    
    <h3>Available Scopes</h3>
    <p>Scopes restrict the level of access Oscar has over Nova CRM data. Available scopes include:</p>
    <ul>
      {scopes_list}
    </ul>
    
    <h3>Step 1: Create an OAuth App in Nova CRM</h3>
    <ol>
      <li>Go to Settings → OAuth Apps in Nova CRM.</li>
      <li>Click "Register App".</li>
      <li>Set Application Name to "Django Oscar Integration".</li>
      <li>Set Redirect URI to your Oscar callback endpoint (e.g., <code>https://your-oscar-store.com/oauth/callback/</code>).</li>
      <li>Select the required scopes (e.g., <code>NovaCRM.modules.contacts.WRITE</code> for syncing users to CRM contacts, <code>NovaCRM.modules.deals.WRITE</code> for orders).</li>
      <li>Save and securely store your <strong>Client ID</strong> and <strong>Client Secret</strong>.</li>
    </ol>
    """,
    endpoint="/api/v1/oauth/token/",
    method="POST",
    req_format="""
    <h3>Step 2: Configure Django Oscar</h3>
    <p>In your Django Oscar project's <code>settings.py</code>, configure the OAuth credentials and endpoints.</p>
    <pre><code># Oscar settings.py
NOVA_CRM_CLIENT_ID = 'client_xxxxxxxxxxxxxxxx'
NOVA_CRM_CLIENT_SECRET = 'secret_xxxxxxxxxxxxxxxxxxxxxxxxx'
NOVA_CRM_TOKEN_URL = 'https://your-novacrm.com/api/v1/oauth/token/'
NOVA_CRM_API_BASE = 'https://your-novacrm.com/api/v1/'
NOVA_CRM_SCOPES = 'NovaCRM.modules.contacts.WRITE NovaCRM.modules.deals.WRITE'
</code></pre>
    
    <h3>Step 3: Implement Token Exchange in Oscar</h3>
    <p>Write a utility to fetch and manage the access token. You can use <code>requests</code> or `Authlib`.</p>
    <pre><code>import requests
from django.conf import settings

def get_nova_crm_token():
    # Typically, you'd cache this token until it expires
    response = requests.post(settings.NOVA_CRM_TOKEN_URL, json={
        "grant_type": "client_credentials", # Or authorization_code if user-specific
        "client_id": settings.NOVA_CRM_CLIENT_ID,
        "client_secret": settings.NOVA_CRM_CLIENT_SECRET,
        "scope": settings.NOVA_CRM_SCOPES
    })
    return response.json().get('access_token')
</code></pre>

    <h3>Step 4: Syncing an Order from Oscar to Nova CRM</h3>
    <p>Hook into Oscar's order placement signal to push data to Nova CRM.</p>
    <pre><code>from oscar.apps.order.signals import order_placed
from django.dispatch import receiver

@receiver(order_placed)
def sync_order_to_crm(sender, order, user, **kwargs):
    token = get_nova_crm_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 1. Ensure Contact exists
    contact_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }
    # POST to /api/v1/crm/contacts/ ...
    
    # 2. Create Deal for the Order
    deal_data = {
        "name": f"Oscar Order #{order.number}",
        "amount": str(order.total_incl_tax),
        "stage": "Closed Won"
    }
    # POST to /api/v1/crm/deals/ ...
</code></pre>
    """,
    res_format="""
    <h3>Summary of Integration Flow</h3>
    <ol>
        <li><strong>Event:</strong> A customer places an order in Django Oscar.</li>
        <li><strong>Trigger:</strong> Oscar's <code>order_placed</code> signal fires.</li>
        <li><strong>Auth:</strong> Oscar requests a valid OAuth Access Token using the Client ID and Secret generated in Nova CRM.</li>
        <li><strong>Sync:</strong> Oscar calls Nova CRM's <code>/contacts/</code> API to ensure the user is registered as a CRM Contact.</li>
        <li><strong>Record:</strong> Oscar calls Nova CRM's <code>/deals/</code> API to record the e-commerce transaction as a Won Deal.</li>
    </ol>
    <p>By using the correct scopes, you ensure Oscar only has permission to perform these specific actions, maintaining high security across your ecosystem.</p>
    """
)
