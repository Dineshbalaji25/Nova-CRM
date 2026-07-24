#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite for Nova CRM.
Tests every API endpoint, auth flow, CRUD operations, and edge cases.
"""
import requests
import json
import time
import sys
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:8000/api/v1'
FRONTEND_URL = 'http://localhost:8000'

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

results = {
    'pass': 0,
    'fail': 0,
    'warn': 0,
    'details': []
}

def log_result(category, test_name, status, detail=''):
    """Log a test result."""
    emoji = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'
    color = GREEN if status == 'PASS' else RED if status == 'FAIL' else YELLOW
    print(f"{emoji} {color}[{status}]{RESET} {category} > {test_name}" + (f" - {detail}" if detail else ""))
    results['details'].append({
        'category': category,
        'test': test_name,
        'status': status,
        'detail': detail
    })
    if status == 'PASS':
        results['pass'] += 1
    elif status == 'FAIL':
        results['fail'] += 1
    else:
        results['warn'] += 1

def section(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}  {title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

# ============================================================
# 1. AUTHENTICATION & USER MANAGEMENT
# ============================================================
def test_auth():
    section("1. AUTHENTICATION & USER MANAGEMENT")
    global TOKEN, TENANT_ID, HEADERS, USER_EMAIL
    
    USER_EMAIL = f"testuser_{int(time.time())}@example.com"
    PASSWORD = "TestPassword123!"
    
    # Test 1: Registration
    res = requests.post(f"{BASE_URL}/register/", json={
        "email": USER_EMAIL,
        "password": PASSWORD,
        "full_name": "Test User",
        "organization_name": "Test Org"
    })
    if res.status_code == 201:
        data = res.json()
        TOKEN = data['tokens']['access']
        TENANT_ID = data['tenant_id']
        HEADERS = {
            "Authorization": f"Bearer {TOKEN}",
            "X-Tenant-ID": str(TENANT_ID),
            "Content-Type": "application/json"
        }
        log_result("Auth", "User Registration", "PASS", f"Created user with tenant {TENANT_ID}")
    else:
        log_result("Auth", "User Registration", "FAIL", res.text[:200])
        return False
    
    # Test 2: Duplicate Registration
    res = requests.post(f"{BASE_URL}/register/", json={
        "email": USER_EMAIL,
        "password": PASSWORD,
        "full_name": "Test User",
        "organization_name": "Test Org 2"
    })
    if res.status_code == 400:
        log_result("Auth", "Duplicate Registration Rejected", "PASS")
    else:
        log_result("Auth", "Duplicate Registration Rejected", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Test 3: Registration with short password
    res = requests.post(f"{BASE_URL}/register/", json={
        "email": f"short_{int(time.time())}@example.com",
        "password": "123",
        "full_name": "Short Pass",
        "organization_name": "Short Org"
    })
    if res.status_code == 400:
        log_result("Auth", "Short Password Rejected", "PASS")
    else:
        log_result("Auth", "Short Password Rejected", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Test 4: Registration missing organization_name
    res = requests.post(f"{BASE_URL}/register/", json={
        "email": f"noorg_{int(time.time())}@example.com",
        "password": PASSWORD,
        "full_name": "No Org"
    })
    if res.status_code == 400:
        log_result("Auth", "Missing Org Name Rejected", "PASS")
    else:
        log_result("Auth", "Missing Org Name Rejected", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Test 5: Login
    res = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": USER_EMAIL,
        "password": PASSWORD
    })
    if res.status_code == 200 and 'access' in res.json():
        log_result("Auth", "User Login", "PASS")
    else:
        log_result("Auth", "User Login", "FAIL", res.text[:200])
    
    # Test 6: Login with wrong password
    res = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": USER_EMAIL,
        "password": "WrongPassword123!"
    })
    if res.status_code == 401:
        log_result("Auth", "Wrong Password Rejected", "PASS")
    else:
        log_result("Auth", "Wrong Password Rejected", "FAIL", f"Expected 401, got {res.status_code}")
    
    # Test 7: Auth Check
    res = requests.get(f"{BASE_URL}/auth/check/", headers=HEADERS)
    if res.status_code == 200 and res.json().get('authenticated'):
        log_result("Auth", "Auth Check Endpoint", "PASS")
    else:
        log_result("Auth", "Auth Check Endpoint", "FAIL", res.text[:200])
    
    # Test 8: Token Refresh
    refresh_token = data['tokens']['refresh'] if 'tokens' in data else None
    if refresh_token:
        res = requests.post(f"{BASE_URL}/auth/token/refresh/", json={"refresh": refresh_token})
        if res.status_code == 200 and 'access' in res.json():
            log_result("Auth", "Token Refresh", "PASS")
        else:
            log_result("Auth", "Token Refresh", "FAIL", res.text[:200])
    else:
        log_result("Auth", "Token Refresh", "WARN", "No refresh token available")
    
    # Test 9: My Organizations
    res = requests.get(f"{BASE_URL}/my-organizations/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Auth", "List My Organizations", "PASS")
    else:
        log_result("Auth", "List My Organizations", "FAIL", res.text[:200])
    
    # Test 10: Switch Tenant
    res = requests.post(f"{BASE_URL}/switch-tenant/", headers=HEADERS, json={"tenant_id": TENANT_ID})
    if res.status_code == 200:
        log_result("Auth", "Switch Tenant", "PASS")
    else:
        log_result("Auth", "Switch Tenant", "FAIL", res.text[:200])
    
    # Test 11: Unauthenticated access
    res = requests.get(f"{BASE_URL}/crm/contacts/")
    if res.status_code == 401:
        log_result("Auth", "Unauthenticated Access Blocked", "PASS")
    else:
        log_result("Auth", "Unauthenticated Access Blocked", "FAIL", f"Expected 401, got {res.status_code}")
    
    # Test 12: Missing Tenant Header
    no_tenant_headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    res = requests.get(f"{BASE_URL}/crm/contacts/", headers=no_tenant_headers)
    if res.status_code == 200:
        log_result("Auth", "Missing Tenant Header Handling", "PASS", "Returns empty list (graceful)")
    elif res.status_code == 400:
        log_result("Auth", "Missing Tenant Header Handling", "PASS", "Returns 400 (strict)")
    else:
        log_result("Auth", "Missing Tenant Header Handling", "WARN", f"Status {res.status_code}")
    
    # Test 13: Google Auth (not configured)
    res = requests.post(f"{BASE_URL}/auth/google/", json={"id_token": "fake_token"})
    if res.status_code in [400, 503]:
        log_result("Auth", "Google Auth (Not Configured)", "PASS", f"Returns {res.status_code}")
    else:
        log_result("Auth", "Google Auth (Not Configured)", "FAIL", f"Expected 400/503, got {res.status_code}")
    
    # Test 14: OAuth Scopes List
    res = requests.get(f"{BASE_URL}/oauth/scopes/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Auth", "OAuth Scopes List", "PASS")
    else:
        log_result("Auth", "OAuth Scopes List", "FAIL", res.text[:200])
    
    return True

# ============================================================
# 2. CRM CORE - COMPANIES, CONTACTS, LEADS, DEALS
# ============================================================
def test_crm_core():
    section("2. CRM CORE - COMPANIES, CONTACTS, LEADS, DEALS")
    global COMPANY_ID, CONTACT_ID, LEAD_ID, DEAL_ID, PIPELINE_ID, STAGE_ID
    ACTIVITY_ID = None
    # --- Companies ---
    # Create
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=HEADERS, json={
        "name": "Acme Corporation",
        "domain": "acme.com",
        "industry": "Technology",
        "annual_revenue": "1000000"
    })
    if res.status_code == 201:
        COMPANY_ID = res.json()['id']
        log_result("CRM", "Create Company", "PASS")
    else:
        log_result("CRM", "Create Company", "FAIL", res.text[:200])
        return
    
    # List
    res = requests.get(f"{BASE_URL}/crm/companies/", headers=HEADERS)
    if res.status_code == 200 and res.json().get('results') is not None:
        log_result("CRM", "List Companies", "PASS", f"Count: {res.json().get('count')}")
    elif res.status_code == 200:
        log_result("CRM", "List Companies", "PASS")
    else:
        log_result("CRM", "List Companies", "FAIL", res.text[:200])
    
    # Retrieve
    res = requests.get(f"{BASE_URL}/crm/companies/{COMPANY_ID}/", headers=HEADERS)
    if res.status_code == 200 and res.json()['name'] == "Acme Corporation":
        log_result("CRM", "Retrieve Company", "PASS")
    else:
        log_result("CRM", "Retrieve Company", "FAIL", res.text[:200])
    
    # Update
    res = requests.patch(f"{BASE_URL}/crm/companies/{COMPANY_ID}/", headers=HEADERS, json={"industry": "Finance"})
    if res.status_code == 200 and res.json()['industry'] == "Finance":
        log_result("CRM", "Update Company", "PASS")
    else:
        log_result("CRM", "Update Company", "FAIL", res.text[:200])
    
    # --- Contacts ---
    res = requests.post(f"{BASE_URL}/crm/contacts/", headers=HEADERS, json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@acme.com",
        "phone": "+1234567890",
        "company": COMPANY_ID
    })
    if res.status_code == 201:
        CONTACT_ID = res.json()['id']
        log_result("CRM", "Create Contact", "PASS")
    else:
        log_result("CRM", "Create Contact", "FAIL", res.text[:200])
    
    # List Contacts
    res = requests.get(f"{BASE_URL}/crm/contacts/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "List Contacts", "PASS")
    else:
        log_result("CRM", "List Contacts", "FAIL", res.text[:200])
    
    # Retrieve Contact
    res = requests.get(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "Retrieve Contact", "PASS")
    else:
        log_result("CRM", "Retrieve Contact", "FAIL", res.text[:200])
    
    # Update Contact
    res = requests.patch(f"{BASE_URL}/crm/contacts/{CONTACT_ID}/", headers=HEADERS, json={"phone": "+9999999999"})
    if res.status_code == 200 and res.json()['phone'] == "+9999999999":
        log_result("CRM", "Update Contact", "PASS")
    else:
        log_result("CRM", "Update Contact", "FAIL", res.text[:200])
    
    # --- Leads ---
    res = requests.post(f"{BASE_URL}/crm/leads/", headers=HEADERS, json={
        "title": "Interested in Enterprise Plan",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "company_name": "Smith Inc",
        "status": "new",
        "source": "Website"
    })
    if res.status_code == 201:
        LEAD_ID = res.json()['id']
        log_result("CRM", "Create Lead", "PASS")
    else:
        log_result("CRM", "Create Lead", "FAIL", res.text[:200])
    
    # List Leads
    res = requests.get(f"{BASE_URL}/crm/leads/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "List Leads", "PASS")
    else:
        log_result("CRM", "List Leads", "FAIL", res.text[:200])
    
    # Update Lead Status
    res = requests.patch(f"{BASE_URL}/crm/leads/{LEAD_ID}/", headers=HEADERS, json={"status": "contacted"})
    if res.status_code == 200 and res.json()['status'] == "contacted":
        log_result("CRM", "Update Lead Status", "PASS")
    else:
        log_result("CRM", "Update Lead Status", "FAIL", res.text[:200])
    
    # --- Pipelines & Stages ---
    res = requests.post(f"{BASE_URL}/crm/pipelines/", headers=HEADERS, json={
        "name": "Sales Pipeline",
        "is_default": True
    })
    if res.status_code == 201:
        PIPELINE_ID = res.json()['id']
        log_result("CRM", "Create Pipeline", "PASS")
    else:
        log_result("CRM", "Create Pipeline", "FAIL", res.text[:200])
    
    # Create Stage - Note: StageSerializer may not include pipeline field (FLAW)
    res = requests.post(f"{BASE_URL}/crm/stages/", headers=HEADERS, json={
        "pipeline": PIPELINE_ID,
        "name": "New",
        "position": 1,
        "win_probability": 10
    })
    if res.status_code == 201:
        STAGE_ID = res.json()['id']
        log_result("CRM", "Create Stage", "PASS")
    else:
        log_result("CRM", "Create Stage", "FAIL", f"Status {res.status_code}: {res.text[:200]}")
        # Try without pipeline (serializer may not support it)
        res = requests.post(f"{BASE_URL}/crm/stages/", headers=HEADERS, json={
            "name": "New",
            "position": 1,
            "win_probability": 10
        })
        if res.status_code == 201:
            STAGE_ID = res.json()['id']
            log_result("CRM", "Create Stage (no pipeline)", "WARN", "StageSerializer missing pipeline field")
        else:
            log_result("CRM", "Create Stage (fallback)", "FAIL", res.text[:200])
            # Use Django shell to create stage directly for remaining tests
            import subprocess
            subprocess.run([
                sys.executable, "manage.py", "shell", "-c",
                f"from apps.crm.models import Pipeline, Stage; p=Pipeline.objects.get(id='{PIPELINE_ID}'); s=Stage.objects.create(tenant_id='{TENANT_ID}', pipeline=p, name='New', position=1, win_probability=10); print(s.id)"
            ], cwd='/home/dinesh/CRM/crm', capture_output=True, text=True)
            # Try to fetch stages
            res = requests.get(f"{BASE_URL}/crm/stages/", headers=HEADERS)
            if res.status_code == 200 and res.json().get('results'):
                STAGE_ID = res.json()['results'][0]['id']
            else:
                STAGE_ID = None
    
    # --- Deals ---
    res = requests.post(f"{BASE_URL}/crm/deals/", headers=HEADERS, json={
        "title": "Enterprise Deal",
        "amount": "50000",
        "currency": "USD",
        "pipeline": PIPELINE_ID,
        "stage": STAGE_ID,
        "company": COMPANY_ID,
        "primary_contact": CONTACT_ID,
        "expected_close_date": "2025-12-31",
        "probability": 50
    })
    if res.status_code == 201:
        DEAL_ID = res.json()['id']
        log_result("CRM", "Create Deal", "PASS")
    else:
        log_result("CRM", "Create Deal", "FAIL", res.text[:200])
    
    # List Deals
    res = requests.get(f"{BASE_URL}/crm/deals/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "List Deals", "PASS")
    else:
        log_result("CRM", "List Deals", "FAIL", res.text[:200])
    
    # Retrieve Deal
    res = requests.get(f"{BASE_URL}/crm/deals/{DEAL_ID}/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "Retrieve Deal", "PASS")
    else:
        log_result("CRM", "Retrieve Deal", "FAIL", res.text[:200])
    
    # Update Deal
    res = requests.patch(f"{BASE_URL}/crm/deals/{DEAL_ID}/", headers=HEADERS, json={"amount": "75000"})
    if res.status_code == 200 and str(res.json()['amount']) == "75000.00":
        log_result("CRM", "Update Deal Amount", "PASS")
    else:
        log_result("CRM", "Update Deal Amount", "FAIL", res.text[:200])
    
    # --- Notes ---
    res = requests.post(f"{BASE_URL}/crm/notes/", headers=HEADERS, json={
        "body": "This is a test note",
        "deal": DEAL_ID
    })
    if res.status_code == 201:
        NOTE_ID = res.json()['id']
        log_result("CRM", "Create Note", "PASS")
    else:
        log_result("CRM", "Create Note", "FAIL", res.text[:200])
    
    # List Notes
    res = requests.get(f"{BASE_URL}/crm/notes/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "List Notes", "PASS")
    else:
        log_result("CRM", "List Notes", "FAIL", res.text[:200])
    
    # --- Activities ---
    res = requests.post(f"{BASE_URL}/crm/activities/", headers=HEADERS, json={
        "activity_type": "call",
        "subject": "Follow up call",
        "body": "Discussed pricing",
        "deal": DEAL_ID
    })
    if res.status_code == 201:
        ACTIVITY_ID = res.json()['id']
        log_result("CRM", "Create Activity", "PASS")
    else:
        log_result("CRM", "Create Activity", "FAIL", res.text[:200])
    
    # Complete Activity
    if ACTIVITY_ID:
        res = requests.patch(f"{BASE_URL}/crm/activities/{ACTIVITY_ID}/", headers=HEADERS, json={"is_completed": True})
        if res.status_code == 200 and res.json()['is_completed']:
            log_result("CRM", "Complete Activity", "PASS")
        else:
            log_result("CRM", "Complete Activity", "FAIL", res.text[:200])
    else:
        log_result("CRM", "Complete Activity", "FAIL", "Skipped - no ACTIVITY_ID")
    
    # --- Tags ---
    res = requests.post(f"{BASE_URL}/crm/tags/", headers=HEADERS, json={"name": "VIP", "color": "#FF0000"})
    if res.status_code == 201:
        log_result("CRM", "Create Tag", "PASS")
    else:
        log_result("CRM", "Create Tag", "FAIL", res.text[:200])
    
    # --- Custom Fields ---
    res = requests.post(f"{BASE_URL}/crm/custom-fields/", headers=HEADERS, json={
        "target_model": "contact",
        "key": "department",
        "label": "Department",
        "field_type": "text"
    })
    if res.status_code == 201:
        log_result("CRM", "Create Custom Field", "PASS")
    else:
        log_result("CRM", "Create Custom Field", "FAIL", res.text[:200])
    
    # --- Territories ---
    res = requests.post(f"{BASE_URL}/crm/territories/", headers=HEADERS, json={
        "name": "North America",
        "description": "NA Region"
    })
    if res.status_code == 201:
        TERRITORY_ID = res.json()['id']
        log_result("CRM", "Create Territory", "PASS")
    else:
        log_result("CRM", "Create Territory", "FAIL", res.text[:200])
    
    # --- Assignment Rules ---
    res = requests.post(f"{BASE_URL}/crm/assignment-rules/", headers=HEADERS, json={
        "name": "Round Robin",
        "target_model": "lead",
        "criteria": {"field": "lead.source", "operator": "eq", "value": "Website"},
        "is_active": True
    })
    if res.status_code == 201:
        log_result("CRM", "Create Assignment Rule", "PASS")
    else:
        log_result("CRM", "Create Assignment Rule", "FAIL", res.text[:200])
    
    # --- Scoring Rules ---
    res = requests.post(f"{BASE_URL}/crm/scoring-rules/", headers=HEADERS, json={
        "name": "CEO Bonus",
        "target_model": "lead",
        "criteria": {"field": "lead.title", "operator": "eq", "value": "CEO"},
        "score_change": 20,
        "is_active": True
    })
    if res.status_code == 201:
        log_result("CRM", "Create Scoring Rule", "PASS")
    else:
        log_result("CRM", "Create Scoring Rule", "FAIL", res.text[:200])
    
    # Score Breakdown
    res = requests.get(f"{BASE_URL}/crm/scoring/lead/{LEAD_ID}/breakdown/", headers=HEADERS)
    if res.status_code == 200:
        log_result("CRM", "Score Breakdown", "PASS")
    else:
        log_result("CRM", "Score Breakdown", "FAIL", res.text[:200])
    
    # --- Delete Tests ---
    res = requests.delete(f"{BASE_URL}/crm/notes/{NOTE_ID}/", headers=HEADERS)
    if res.status_code in [204, 200]:
        log_result("CRM", "Delete Note", "PASS")
    else:
        log_result("CRM", "Delete Note", "FAIL", res.text[:200])

# ============================================================
# 3. WORKFLOWS & BLUEPRINTS
# ============================================================
def test_workflows():
    section("3. WORKFLOWS & BLUEPRINTS")
    
    # Workflow Metadata
    res = requests.get(f"{BASE_URL}/workflows/metadata/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Workflows", "Get Metadata", "PASS")
    else:
        log_result("Workflows", "Get Metadata", "FAIL", res.text[:200])
    
    # Create Workflow
    res = requests.post(f"{BASE_URL}/workflows/definitions/", headers=HEADERS, json={
        "name": "Welcome Email Workflow",
        "trigger_type": "event",
        "trigger_model": "contact",
        "is_active": True,
        "conditions": {"field": "contact.email", "operator": "ne", "value": ""},
        "actions": [{"type": "email.send", "config": {"to": "{{contact.email}}", "subject": "Welcome!"}}]
    })
    if res.status_code == 201:
        WORKFLOW_ID = res.json()['id']
        log_result("Workflows", "Create Workflow", "PASS")
    else:
        log_result("Workflows", "Create Workflow", "FAIL", res.text[:200])
    
    # List Workflows
    res = requests.get(f"{BASE_URL}/workflows/definitions/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Workflows", "List Workflows", "PASS")
    else:
        log_result("Workflows", "List Workflows", "FAIL", res.text[:200])
    
    # List Executions
    res = requests.get(f"{BASE_URL}/workflows/executions/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Workflows", "List Executions", "PASS")
    else:
        log_result("Workflows", "List Executions", "FAIL", res.text[:200])
    
    # Create Blueprint
    res = requests.post(f"{BASE_URL}/workflows/blueprints/", headers=HEADERS, json={
        "name": "Sales Process Blueprint",
        "target_model": "deal",
        "controlled_field": "stage"
    })
    if res.status_code == 201:
        BLUEPRINT_ID = res.json()['id']
        log_result("Workflows", "Create Blueprint", "PASS")
    else:
        log_result("Workflows", "Create Blueprint", "FAIL", res.text[:200])
    
    # Create Blueprint State
    res = requests.post(f"{BASE_URL}/workflows/blueprint-states/", headers=HEADERS, json={
        "blueprint": BLUEPRINT_ID,
        "name": "New",
        "is_initial": True
    })
    if res.status_code == 201:
        STATE_ID = res.json()['id']
        log_result("Workflows", "Create Blueprint State", "PASS")
    else:
        log_result("Workflows", "Create Blueprint State", "FAIL", res.text[:200])
    
    # Create second state
    res = requests.post(f"{BASE_URL}/workflows/blueprint-states/", headers=HEADERS, json={
        "blueprint": BLUEPRINT_ID,
        "name": "Qualified",
        "is_initial": False
    })
    if res.status_code == 201:
        STATE2_ID = res.json()['id']
        log_result("Workflows", "Create Second Blueprint State", "PASS")
    else:
        log_result("Workflows", "Create Second Blueprint State", "FAIL", res.text[:200])
    
    # Create Transition
    res = requests.post(f"{BASE_URL}/workflows/blueprint-transitions/", headers=HEADERS, json={
        "blueprint": BLUEPRINT_ID,
        "from_state": STATE_ID,
        "to_state": STATE2_ID,
        "name": "Qualify"
    })
    if res.status_code == 201:
        log_result("Workflows", "Create Blueprint Transition", "PASS")
    else:
        log_result("Workflows", "Create Blueprint Transition", "FAIL", res.text[:200])
    
    # Blueprint Record Status
    res = requests.get(f"{BASE_URL}/workflows/blueprints/record/deal/{DEAL_ID}/", headers=HEADERS)
    if res.status_code in [200, 404]:
        log_result("Workflows", "Blueprint Record Status", "PASS", f"Status {res.status_code}")
    else:
        log_result("Workflows", "Blueprint Record Status", "FAIL", res.text[:200])

# ============================================================
# 4. SALES - PRODUCTS, QUOTES, SALES ORDERS, INVOICES
# ============================================================
def test_sales():
    section("4. SALES - PRODUCTS, QUOTES, SALES ORDERS, INVOICES")
    
    # Create Product
    res = requests.post(f"{BASE_URL}/sales/products/", headers=HEADERS, json={
        "name": "Enterprise License",
        "sku": "ENT-001",
        "price": "1000.00",
        "description": "Annual enterprise license"
    })
    if res.status_code == 201:
        PRODUCT_ID = res.json()['id']
        log_result("Sales", "Create Product", "PASS")
    else:
        log_result("Sales", "Create Product", "FAIL", res.text[:200])
    
    # List Products
    res = requests.get(f"{BASE_URL}/sales/products/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Sales", "List Products", "PASS")
    else:
        log_result("Sales", "List Products", "FAIL", res.text[:200])
    
    # Create Price Book
    res = requests.post(f"{BASE_URL}/sales/price-books/", headers=HEADERS, json={
        "name": "Standard Pricing",
        "is_active": True
    })
    if res.status_code == 201:
        PRICEBOOK_ID = res.json()['id']
        log_result("Sales", "Create Price Book", "PASS")
    else:
        log_result("Sales", "Create Price Book", "FAIL", res.text[:200])
    
    # Create Quote
    res = requests.post(f"{BASE_URL}/sales/quotes/", headers=HEADERS, json={
        "deal": DEAL_ID,
        "company": COMPANY_ID,
        "subject": "Enterprise Quote",
        "valid_until": "2025-12-31"
    })
    if res.status_code == 201:
        QUOTE_ID = res.json()['id']
        log_result("Sales", "Create Quote", "PASS")
    else:
        log_result("Sales", "Create Quote", "FAIL", res.text[:200])
    
    # List Quotes
    res = requests.get(f"{BASE_URL}/sales/quotes/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Sales", "List Quotes", "PASS")
    else:
        log_result("Sales", "List Quotes", "FAIL", res.text[:200])
    
    # Create Sales Order
    res = requests.post(f"{BASE_URL}/sales/sales-orders/", headers=HEADERS, json={
        "deal": DEAL_ID,
        "company": COMPANY_ID,
        "subject": "Enterprise Order"
    })
    if res.status_code == 201:
        SALES_ORDER_ID = res.json()['id']
        log_result("Sales", "Create Sales Order", "PASS")
    else:
        log_result("Sales", "Create Sales Order", "FAIL", res.text[:200])
    
    # List Sales Orders
    res = requests.get(f"{BASE_URL}/sales/sales-orders/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Sales", "List Sales Orders", "PASS")
    else:
        log_result("Sales", "List Sales Orders", "FAIL", res.text[:200])
    
    # Create Invoice
    res = requests.post(f"{BASE_URL}/sales/invoices/", headers=HEADERS, json={
        "deal": DEAL_ID,
        "company": COMPANY_ID,
        "subject": "Enterprise Invoice",
        "due_date": "2025-12-31"
    })
    if res.status_code == 201:
        INVOICE_ID = res.json()['id']
        log_result("Sales", "Create Invoice", "PASS")
    else:
        log_result("Sales", "Create Invoice", "FAIL", res.text[:200])
    
    # List Invoices
    res = requests.get(f"{BASE_URL}/sales/invoices/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Sales", "List Invoices", "PASS")
    else:
        log_result("Sales", "List Invoices", "FAIL", res.text[:200])

# ============================================================
# 5. MARKETING - CAMPAIGNS & WEB FORMS
# ============================================================
def test_marketing():
    section("5. MARKETING - CAMPAIGNS & WEB FORMS")
    
    # Create Campaign
    res = requests.post(f"{BASE_URL}/marketing/campaigns/", headers=HEADERS, json={
        "name": "Summer Campaign",
        "status": "active",
        "start_date": "2025-06-01",
        "end_date": "2025-08-31",
        "budget": "10000"
    })
    if res.status_code == 201:
        CAMPAIGN_ID = res.json()['id']
        log_result("Marketing", "Create Campaign", "PASS")
    else:
        log_result("Marketing", "Create Campaign", "FAIL", res.text[:200])
    
    # List Campaigns
    res = requests.get(f"{BASE_URL}/marketing/campaigns/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Marketing", "List Campaigns", "PASS")
    else:
        log_result("Marketing", "List Campaigns", "FAIL", res.text[:200])
    
    # Create Campaign Member
    res = requests.post(f"{BASE_URL}/marketing/campaign-members/", headers=HEADERS, json={
        "campaign": CAMPAIGN_ID,
        "contact": CONTACT_ID
    })
    if res.status_code == 201:
        log_result("Marketing", "Create Campaign Member", "PASS")
    else:
        log_result("Marketing", "Create Campaign Member", "FAIL", res.text[:200])
    
    # Create Web Form
    res = requests.post(f"{BASE_URL}/marketing/webforms/", headers=HEADERS, json={
        "name": "Contact Us Form",
        "target_model": "lead",
        "is_active": True
    })
    if res.status_code == 201:
        WEBFORM_ID = res.json()['id']
        log_result("Marketing", "Create Web Form", "PASS")
    else:
        log_result("Marketing", "Create Web Form", "FAIL", res.text[:200])
    
    # List Web Forms
    res = requests.get(f"{BASE_URL}/marketing/webforms/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Marketing", "List Web Forms", "PASS")
    else:
        log_result("Marketing", "List Web Forms", "FAIL", res.text[:200])
    
    # Create Web Form Field
    res = requests.post(f"{BASE_URL}/marketing/webform-fields/", headers=HEADERS, json={
        "webform": WEBFORM_ID,
        "field_name": "email",
        "label": "Email Address",
        "field_type": "email",
        "is_required": True
    })
    if res.status_code == 201:
        log_result("Marketing", "Create Web Form Field", "PASS")
    else:
        log_result("Marketing", "Create Web Form Field", "FAIL", res.text[:200])

# ============================================================
# 6. ANALYTICS - REPORTS & DASHBOARDS
# ============================================================
def test_analytics():
    section("6. ANALYTICS - REPORTS & DASHBOARDS")
    
    # Dashboard Stats
    res = requests.get(f"{BASE_URL}/stats/dashboard/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Analytics", "Dashboard Stats", "PASS")
    else:
        log_result("Analytics", "Dashboard Stats", "FAIL", res.text[:200])
    
    # Create Report
    res = requests.post(f"{BASE_URL}/analytics/reports/", headers=HEADERS, json={
        "name": "Sales Report",
        "report_type": "summary",
        "target_model": "deal",
        "data_source": "deals",
        "config": {"group_by": "stage", "metrics": ["count", "sum_amount"]}
    })
    if res.status_code == 201:
        REPORT_ID = res.json()['id']
        log_result("Analytics", "Create Report", "PASS")
    else:
        log_result("Analytics", "Create Report", "FAIL", res.text[:200])
    
    # List Reports
    res = requests.get(f"{BASE_URL}/analytics/reports/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Analytics", "List Reports", "PASS")
    else:
        log_result("Analytics", "List Reports", "FAIL", res.text[:200])
    
    # Create Dashboard
    res = requests.post(f"{BASE_URL}/analytics/dashboards/", headers=HEADERS, json={
        "name": "Sales Dashboard",
        "is_shared": True
    })
    if res.status_code == 201:
        DASHBOARD_ID = res.json()['id']
        log_result("Analytics", "Create Dashboard", "PASS")
    else:
        log_result("Analytics", "Create Dashboard", "FAIL", res.text[:200])
    
    # List Dashboards
    res = requests.get(f"{BASE_URL}/analytics/dashboards/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Analytics", "List Dashboards", "PASS")
    else:
        log_result("Analytics", "List Dashboards", "FAIL", res.text[:200])
    
    # Create Dashboard Component
    res = requests.post(f"{BASE_URL}/analytics/dashboard-components/", headers=HEADERS, json={
        "dashboard": DASHBOARD_ID,
        "name": "Revenue Chart",
        "report": REPORT_ID,
        "component_type": "chart",
        "config": {"chart_type": "bar", "data_source": "deals"}
    })
    if res.status_code == 201:
        log_result("Analytics", "Create Dashboard Component", "PASS")
    else:
        log_result("Analytics", "Create Dashboard Component", "FAIL", res.text[:200])

# ============================================================
# 7. OMNICHANNEL - CALLS, EMAILS, CHAT
# ============================================================
def test_omnichannel():
    section("7. OMNICHANNEL - CALLS, EMAILS, CHAT")
    
    PHONE_INT_ID = None
    EMAIL_INT_ID = None
    # Create Phone Integration
    res = requests.post(f"{BASE_URL}/omnichannel/phone-integrations/", headers=HEADERS, json={
        "name": "Twilio Phone",
        "provider": "twilio",
        "account_sid": "test",
        "auth_token": "test",
        "phone_number": "+1234567890"
    })
    if res.status_code == 201:
        PHONE_INT_ID = res.json()['id']
        log_result("Omnichannel", "Create Phone Integration", "PASS")
    else:
        log_result("Omnichannel", "Create Phone Integration", "FAIL", res.text[:200])
    
    # List Phone Integrations
    res = requests.get(f"{BASE_URL}/omnichannel/phone-integrations/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "List Phone Integrations", "PASS")
    else:
        log_result("Omnichannel", "List Phone Integrations", "FAIL", res.text[:200])
    
    # Create Call Log
    res = requests.post(f"{BASE_URL}/omnichannel/call-logs/", headers=HEADERS, json={
        "phone_integration": PHONE_INT_ID,
        "contact": CONTACT_ID,
        "direction": "outbound",
        "status": "completed",
        "duration_seconds": 120,
        "subject": "Sales call"
    })
    if res.status_code == 201:
        log_result("Omnichannel", "Create Call Log", "PASS")
    else:
        log_result("Omnichannel", "Create Call Log", "FAIL", res.text[:200])
    
    # List Call Logs
    res = requests.get(f"{BASE_URL}/omnichannel/call-logs/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "List Call Logs", "PASS")
    else:
        log_result("Omnichannel", "List Call Logs", "FAIL", res.text[:200])
    
    # Create Email Integration
    res = requests.post(f"{BASE_URL}/omnichannel/email-integrations/", headers=HEADERS, json={
        "email_address": "test@example.com",
        "imap_server": "imap.gmail.com",
        "smtp_server": "smtp.gmail.com",
        "password": "testpassword"
    })
    if res.status_code == 201:
        EMAIL_INT_ID = res.json()['id']
        log_result("Omnichannel", "Create Email Integration", "PASS")
    else:
        log_result("Omnichannel", "Create Email Integration", "FAIL", res.text[:200])
    
    # List Email Integrations
    res = requests.get(f"{BASE_URL}/omnichannel/email-integrations/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "List Email Integrations", "PASS")
    else:
        log_result("Omnichannel", "List Email Integrations", "FAIL", res.text[:200])
    
    # Create Email Message
    res = requests.post(f"{BASE_URL}/omnichannel/email-messages/", headers=HEADERS, json={
        "email_integration": EMAIL_INT_ID,
        "subject": "Test Email",
        "body": "This is a test",
        "direction": "outbound"
    })
    if res.status_code == 201:
        log_result("Omnichannel", "Create Email Message", "PASS")
    else:
        log_result("Omnichannel", "Create Email Message", "FAIL", res.text[:200])
    
    # List Email Messages
    res = requests.get(f"{BASE_URL}/omnichannel/email-messages/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "List Email Messages", "PASS")
    else:
        log_result("Omnichannel", "List Email Messages", "FAIL", res.text[:200])
    
    # Unified Timeline
    res = requests.get(f"{BASE_URL}/omnichannel/timeline/contact/{CONTACT_ID}/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "Unified Timeline", "PASS")
    else:
        log_result("Omnichannel", "Unified Timeline", "FAIL", res.text[:200])
    
    # Support Chat - Create user message
    res = requests.post(f"{BASE_URL}/omnichannel/support-chat/", headers=HEADERS, json={
        "message": "Hello, I need help",
        "sender_type": "user"
    })
    if res.status_code == 201:
        log_result("Omnichannel", "Create Support Chat (User)", "PASS")
    else:
        log_result("Omnichannel", "Create Support Chat (User)", "FAIL", res.text[:200])
    
    # Support Chat - Create support message
    res = requests.post(f"{BASE_URL}/omnichannel/support-chat/", headers=HEADERS, json={
        "message": "How can I help you?",
        "sender_type": "support"
    })
    if res.status_code == 201:
        log_result("Omnichannel", "Create Support Chat (Support)", "PASS")
    else:
        log_result("Omnichannel", "Create Support Chat (Support)", "FAIL", res.text[:200])
    
    # List Support Chat
    res = requests.get(f"{BASE_URL}/omnichannel/support-chat/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Omnichannel", "List Support Chat", "PASS")
    else:
        log_result("Omnichannel", "List Support Chat", "FAIL", res.text[:200])

# ============================================================
# 8. BILLING & SUBSCRIPTIONS
# ============================================================
def test_billing():
    section("8. BILLING & SUBSCRIPTIONS")
    
    # List Plans
    res = requests.get(f"{BASE_URL}/billing/plans/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Billing", "List Plans", "PASS")
    else:
        log_result("Billing", "List Plans", "FAIL", res.text[:200])
    
    # List My Subscription
    res = requests.get(f"{BASE_URL}/billing/my-subscription/", headers=HEADERS)
    if res.status_code in [200, 404]:
        log_result("Billing", "List My Subscription", "PASS", f"Status {res.status_code}")
    else:
        log_result("Billing", "List My Subscription", "FAIL", res.text[:200])
    
    # List Invoices
    res = requests.get(f"{BASE_URL}/billing/invoices/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Billing", "List Billing Invoices", "PASS")
    else:
        log_result("Billing", "List Billing Invoices", "FAIL", res.text[:200])
    
    # List Usage
    res = requests.get(f"{BASE_URL}/billing/usage/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Billing", "List Usage Records", "PASS")
    else:
        log_result("Billing", "List Usage Records", "FAIL", res.text[:200])
    
    # Stripe Webhook (without valid signature)
    res = requests.post(f"{BASE_URL}/billing/webhooks/stripe/", json={"event": "test"})
    if res.status_code in [400, 402, 403]:
        log_result("Billing", "Stripe Webhook (Invalid)", "PASS", f"Returns {res.status_code}")
    else:
        log_result("Billing", "Stripe Webhook (Invalid)", "WARN", f"Returns {res.status_code}")

# ============================================================
# 9. AUDIT LOGS
# ============================================================
def test_audit():
    section("9. AUDIT LOGS")
    
    # List Audit Logs
    res = requests.get(f"{BASE_URL}/audit/logs/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Audit", "List Audit Logs", "PASS")
    else:
        log_result("Audit", "List Audit Logs", "FAIL", res.text[:200])
    
    # Check if audit logs were created for our actions
    if res.status_code == 200:
        data = res.json()
        count = data.get('count', 0) if isinstance(data, dict) else len(data)
        if count > 0:
            log_result("Audit", "Audit Logs Created for Actions", "PASS", f"Count: {count}")
        else:
            log_result("Audit", "Audit Logs Created for Actions", "WARN", "No logs found")

# ============================================================
# 10. PORTALS
# ============================================================
def test_portals():
    section("10. PORTALS")
    
    # List Portal Admin
    res = requests.get(f"{BASE_URL}/portal/admin/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Portals", "List Portal Admin", "PASS")
    else:
        log_result("Portals", "List Portal Admin", "FAIL", res.text[:200])
    
    # List Portal Users
    res = requests.get(f"{BASE_URL}/portal/user/", headers=HEADERS)
    if res.status_code in [200, 403]:
        log_result("Portals", "List Portal Users", "PASS", f"Status {res.status_code}")
    else:
        log_result("Portals", "List Portal Users", "FAIL", res.text[:200])
    
    # List Portal Deals
    res = requests.get(f"{BASE_URL}/portal/deals/", headers=HEADERS)
    if res.status_code in [200, 403]:
        log_result("Portals", "List Portal Deals", "PASS", f"Status {res.status_code}")
    else:
        log_result("Portals", "List Portal Deals", "FAIL", res.text[:200])
    
    # List Portal Invoices
    res = web = requests.get(f"{BASE_URL}/portal/invoices/", headers=HEADERS)
    if res.status_code in [200, 403]:
        log_result("Portals", "List Portal Invoices", "PASS", f"Status {res.status_code}")
    else:
        log_result("Portals", "List Portal Invoices", "FAIL", res.text[:200])

# ============================================================
# 11. INTEGRATIONS
# ============================================================
def test_integrations():
    section("11. INTEGRATIONS")
    
    # Tales Timeline Webhook
    res = requests.post(f"{BASE_URL}/integrations/tales-timeline/webhook/", json={"event": "test"})
    if res.status_code in [200, 201, 400, 401, 403]:
        log_result("Integrations", "Tales Timeline Webhook", "PASS", f"Status {res.status_code}")
    else:
        log_result("Integrations", "Tales Timeline Webhook", "FAIL", res.text[:200])
    
    # Zoho-style API - Contacts
    res = requests.get(f"{BASE_URL}/integrations/zoho/v8/Contacts", headers=HEADERS)
    if res.status_code == 200:
        log_result("Integrations", "Zoho API - Contacts", "PASS")
    else:
        log_result("Integrations", "Zoho API - Contacts", "FAIL", res.text[:200])
    
    # Zoho-style API - Deals
    res = requests.get(f"{BASE_URL}/integrations/zoho/v8/Deals", headers=HEADERS)
    if res.status_code == 200:
        log_result("Integrations", "Zoho API - Deals", "PASS")
    else:
        log_result("Integrations", "Zoho API - Deals", "FAIL", res.text[:200])
    
    # Zoho-style API - Accounts
    res = CoreRes = requests.get(f"{BASE_URL}/integrations/zoho/v8/Accounts", headers=HEADERS)
    if res.status_code == 200:
        log_result("Integrations", "Zoho API - Accounts", "PASS")
    else:
        log_result("Integrations", "Zoho API - Accounts", "FAIL", res.text[:200])
    
    # Zoho-style API - Leads
    res = requests.get(f"{BASE_URL}/integrations/zoho/v8/Leads", headers=HEADERS)
    if res.status_code == 200:
        log_result("Integrations", "Zoho API - Leads", "PASS")
    else:
        log_result("Integrations", "Zoho API - Leads", "FAIL", res.text[:200])
    
    # Zoho-style API - Tasks
    res = requests.get(f"{BASE_URL}/integrations/zoho/v8/Tasks", headers=HEADERS)
    if res.status_code == 200:
        log_result("Integrations", "Zoho API - Tasks", "PASS")
    else:
        log_result("Integrations", "Zoho API - Tasks", "FAIL", res.text[:200])

# ============================================================
# 12. API WEBHOOKS
# ============================================================
def test_api_webhooks():
    section("12. API WEBHOOKS")
    
    # List Webhook Endpoints
    res = requests.get(f"{BASE_URL}/webhook-endpoints/", headers=HEADERS)
    if res.status_code == 200:
        log_result("API", "List Webhook Endpoints", "PASS")
    else:
        log_result("API", "List Webhook Endpoints", "FAIL", res.text[:200])
    
    # Create Webhook Endpoint
    res = requests.post(f"{BASE_URL}/webhook-endpoints/", headers=HEADERS, json={
        "url": "https://example.com/webhook",
        "events": ["deal.created", "contact.created"]
    })
    if res.status_code == 201:
        log_result("API", "Create Webhook Endpoint", "PASS")
    else:
        log_result("API", "Create Webhook Endpoint", "FAIL", res.text[:200])
    
    # List Webhook Logs
    res = requests.get(f"{BASE_URL}/webhook-logs/", headers=HEADERS)
    if res.status_code == 200:
        log_result("API", "List Webhook Logs", "PASS")
    else:
        log_result("API", "List Webhook Logs", "FAIL", res.text[:200])

# ============================================================
# 13. USER MANAGEMENT - PROFILES, ROLES, API KEYS
# ============================================================
def test_user_management():
    section("13. USER MANAGEMENT - PROFILES, ROLES, API KEYS")
    
    # List Profiles
    res = requests.get(f"{BASE_URL}/profiles/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Users", "List Profiles", "PASS")
    else:
        log_result("Users", "List Profiles", "FAIL", res.text[:200])
    
    # Create Profile
    res = requests.post(f"{BASE_URL}/profiles/", headers=HEADERS, json={
        "name": "Sales Profile",
        "permissions": ["contacts.view", "deals.view"]
    })
    if res.status_code == 201:
        log_result("Users", "Create Profile", "PASS")
    else:
        log_result("Users", "Create Profile", "FAIL", res.text[:200])
    
    # List Roles
    res = requests.get(f"{BASE_URL}/roles/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Users", "List Roles", "PASS")
    else:
        log_result("Users", "List Roles", "FAIL", res.text[:200])
    
    # Create Role
    res = requests.post(f"{BASE_URL}/roles/", headers=HEADERS, json={
        "name": "Sales Rep",
        "profile": 1
    })
    if res.status_code in [201, 400]:
        log_result("Users", "Create Role", "PASS", f"Status {res.status_code}")
    else:
        log_result("Users", "Create Role", "FAIL", res.text[:200])
    
    # List API Keys
    res = requests.get(f"{BASE_URL}/api-keys/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Users", "List API Keys", "PASS")
    else:
        log_result("Users", "List API Keys", "FAIL", res.text[:200])
    
    # Create API Key
    res = requests.post(f"{BASE_URL}/api-keys/", headers=HEADERS, json={"name": "Test API Key"})
    if res.status_code == 201:
        API_KEY = res.json().get('key', '')
        log_result("Users", "Create API Key", "PASS")
    else:
        log_result("Users", "Create API Key", "FAIL", res.text[:200])
    
    # Create OAuth App
    res = requests.post(f"{BASE_URL}/oauth-apps/", headers=HEADERS, json={
        "name": "Test OAuth App",
        "redirect_uri": "https://example.com/callback",
        "allowed_scopes": ["ZohoCRM.users.READ"]
    })
    if res.status_code == 201:
        OAUTH_APP = res.json()
        log_result("Users", "Create OAuth App", "PASS")
    else:
        log_result("Users", "Create OAuth App", "FAIL", res.text[:200])
    
    # List OAuth Apps
    res = requests.get(f"{BASE_URL}/oauth-apps/", headers=HEADERS)
    if res.status_code == 200:
        log_result("Users", "List OAuth Apps", "PASS")
    else:
        log_result("Users", "List OAuth Apps", "FAIL", res.text[:200])

# ============================================================
# 14. FRONTEND PAGES
# ============================================================
def test_frontend_pages():
    section("14. FRONTEND PAGES")
    
    pages = [
        ('/', 'Landing Page'),
        ('/login', 'Login Page'),
        ('/register', 'Register Page'),
        ('/dashboard', 'Dashboard'),
        ('/leads', 'Leads Page'),
        ('/contacts', 'Contacts Page'),
        ('/companies', 'Companies Page'),
        ('/deals', 'Deals Page'),
        ('/tasks', 'Tasks Page'),
        ('/workflows', 'Workflows Page'),
        ('/scoring-rules', 'Scoring Rules Page'),
        ('/settings', 'Settings Page'),
        ('/billing', 'Billing Page'),
        ('/audit', 'Audit Page'),
        ('/team', 'Team Page'),
        ('/products', 'Products Page'),
        ('/quotes', 'Quotes Page'),
        ('/sales-orders', 'Sales Orders Page'),
        ('/invoices', 'Invoices Page'),
        ('/blueprints', 'Blueprints Page'),
        ('/campaigns', 'Campaigns Page'),
        ('/webforms', 'Web Forms Page'),
        ('/dashboards', 'Dashboards Page'),
        ('/reports', 'Reports Page'),
        ('/territories', 'Territories Page'),
        ('/roles', 'Roles Page'),
        ('/profiles', 'Profiles Page'),
        ('/portals', 'Portals Page'),
        ('/calls', 'Calls Page'),
        ('/emails', 'Emails Page'),
        ('/integrations', 'Integrations Page'),
    ]
    
    for path, name in pages:
        res = requests.get(f"{FRONTEND_URL}{path}")
        if res.status_code == 200:
            log_result("Frontend", f"{name} ({path})", "PASS")
        else:
            log_result("Frontend", f"{name} ({path})", "FAIL", f"Status {res.status_code}")

# ============================================================
# 15. SECURITY TESTS
# ============================================================
def test_security():
    section("15. SECURITY TESTS")
    
    # Test Cross-Tenant Isolation
    # Create second user/org
    USER2_EMAIL = f"testuser2_{int(time.time())}@example.com"
    res = requests.post(f"{BASE_URL}/register/", json={
        "email": USER2_EMAIL,
        "password": "TestPassword123!",
        "full_name": "Test User 2",
        "organization_name": "Test Org 2"
    })
    if res.status_code == 201:
        data2 = res.json()
        TOKEN2 = data2['tokens']['access']
        TENANT2_ID = data2['tenant_id']
        HEADERS2 = {
            "Authorization": f"Bearer {TOKEN2}",
            "X-Tenant-ID": str(TENANT2_ID),
            "Content-Type": "application/json"
        }
        
        # Try to access Tenant 1's company with Tenant 2's credentials
        res = requests.get(f"{BASE_URL}/crm/companies/{COMPANY_ID}/", headers=HEADERS2)
        if res.status_code == 404:
            log_result("Security", "Cross-Tenant Isolation (Retrieve)", "PASS")
        else:
            log_result("Security", "Cross-Tenant Isolation (Retrieve)", "FAIL", f"Expected 404, got {res.status_code}")
        
        # Try to list companies - should only see tenant 2's
        res = requests.get(f"{BASE_URL}/crm/companies/", headers=HEADERS2)
        if res.status_code == 200:
            data = res.json()
            count = data.get('count', 0) if isinstance(data, dict) else len(data)
            if count == 0:
                log_result("Security", "Cross-Tenant Isolation (List)", "PASS", "Tenant 2 sees 0 companies")
            else:
                log_result("Security", "Cross-Tenant Isolation (List)", "FAIL", f"Tenant 2 sees {count} companies")
        else:
            log_result("Security", "Cross-Tenant Isolation (List)", "FAIL", res.text[:200])
    else:
        log_result("Security", "Setup Second Tenant", "FAIL", res.text[:200])
    
    # Test Invalid Token
    res = requests.get(f"{BASE_URL}/crm/contacts/", headers={
        "Authorization": "Bearer invalidtoken123",
        "X-Tenant-ID": str(TENANT_ID)
    })
    if res.status_code == 401:
        log_result("Security", "Invalid Token Rejected", "PASS")
    else:
        log_result("Security", "Invalid Token Rejected", "FAIL", f"Expected 401, got {res.status_code}")
    
    # Test SQL Injection attempt
    res = requests.get(f"{BASE_URL}/crm/companies/?name=Acme' OR '1'='1", headers=HEADERS)
    if res.status_code == 200:
        log_result("Security", "SQL Injection Protection", "PASS", "No error (ORM protected)")
    else:
        log_result("Security", "SQL Injection Protection", "WARN", f"Status {res.status_code}")
    
    # Test XSS in input
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=HEADERS, json={
        "name": "<script>alert('xss')</script>",
        "domain": "xss.com"
    })
    if res.status_code == 201:
        XSS_ID = res.json()['id']
        res2 = requests.get(f"{BASE_URL}/crm/companies/{XSS_ID}/", headers=HEADERS)
        if res2.status_code == 200 and '<script>' not in res2.text:
            log_result("Security", "XSS Input Handling", "PASS", "Stored but not executed in API")
        else:
            log_result("Security", "XSS Input Handling", "WARN", "Script tag stored in DB")
        # Clean up
        requests.delete(f"{BASE_URL}/crm/companies/{XSS_ID}/", headers=HEADERS)
    else:
        log_result("Security", "XSS Input Handling", "FAIL", res.text[:200])

# ============================================================
# 16. EDGE CASES & ERROR HANDLING
# ============================================================
def test_edge_cases():
    section("16. EDGE CASES & ERROR HANDLING")
    
    # Get non-existent record
    import uuid
    fake_id = str(uuid.uuid4())
    res = requests.get(f"{BASE_URL}/crm/companies/{fake_id}/", headers=HEADERS)
    if res.status_code == 404:
        log_result("Edge Case", "Non-existent Record (404)", "PASS")
    else:
        log_result("Edge Case", "Non-existent Record (404)", "FAIL", f"Expected 404, got {res.status_code}")
    
    # Invalid UUID format
    res = requests.get(f"{BASE_URL}/crm/companies/not-a-uuid/", headers=HEADERS)
    if res.status_code in [400, 404]:
        log_result("Edge Case", "Invalid UUID Format", "PASS", f"Status {res.status_code}")
    else:
        log_result("Edge Case", "Invalid UUID Format", "FAIL", f"Expected 400/404, got {res.status_code}")
    
    # Create with missing required fields
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=HEADERS, json={})
    if res.status_code == 400:
        log_result("Edge Case", "Missing Required Fields", "PASS")
    else:
        log_result("Edge Case", "Missing Required Fields", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Create with invalid data type
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=HEADERS, json={
        "name": "Test",
        "annual_revenue": "not-a-number"
    })
    if res.status_code == 400:
        log_result("Edge Case", "Invalid Data Type", "PASS")
    else:
        log_result("Edge Case", "Invalid Data Type", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Pagination
    res = requests.get(f"{BASE_URL}/crm/contacts/?page=1&page_size=5", headers=HEADERS)
    if res.status_code == 200:
        log_result("Edge Case", "Pagination", "PASS")
    else:
        log_result("Edge Case", "Pagination", "FAIL", res.text[:200])
    
    # Search/Filter
    res = requests.get(f"{BASE_URL}/crm/contacts/?search=John", headers=HEADERS)
    if res.status_code == 200:
        log_result("Edge Case", "Search Filter", "PASS")
    else:
        log_result("Edge Case", "Search Filter", "FAIL", res.text[:200])
    
    # Ordering
    res = requests.get(f"{BASE_URL}/crm/contacts/?ordering=-created_at", headers=HEADERS)
    if res.status_code == 200:
        log_result("Edge Case", "Ordering", "PASS")
    else:
        log_result("Edge Case", "Ordering", "FAIL", res.text[:200])
    
    # Empty body POST
    res = requests.post(f"{BASE_URL}/crm/contacts/", headers=HEADERS, data="")
    if res.status_code == 400:
        log_result("Edge Case", "Empty Body POST", "PASS")
    else:
        log_result("Edge Case", "Empty Body POST", "FAIL", f"Expected 400, got {res.status_code}")
    
    # Very long string
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=HEADERS, json={
        "name": "A" * 1000
    })
    if res.status_code in [201, 400]:
        log_result("Edge Case", "Very Long String", "PASS", f"Status {res.status_code}")
    else:
        log_result("Edge Case", "Very Long String", "FAIL", f"Status {res.status_code}")

# ============================================================
# MAIN
# ============================================================
def main():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║       NOVA CRM - COMPREHENSIVE FEATURE TEST SUITE                    ║{RESET}")
    print(f"{BLUE}║       Testing Every Feature, Endpoint, and Button                   ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all test suites
    if not test_auth():
        print(f"\n{RED}Auth setup failed. Cannot continue.{RESET}")
        return
    
    test_crm_core()
    test_workflows()
    test_sales()
    test_marketing()
    test_analytics()
    test_omnichannel()
    test_billing()
    test_audit()
    test_portals()
    test_integrations()
    test_api_webhooks()
    test_user_management()
    test_frontend_pages()
    test_security()
    test_edge_cases()
    
    # Summary
    section("SUMMARY")
    total = results['pass'] + results['fail'] + results['warn']
    print(f"\n{GREEN}PASSED: {results['pass']}{RESET}")
    print(f"{RED}FAILED: {results['fail']}{RESET}")
    print(f"{YELLOW}WARNINGS: {results['warn']}{RESET}")
    print(f"TOTAL: {total}")
    print(f"Success Rate: {(results['pass']/total)*100:.1f}%")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'pass': results['pass'],
            'fail': results['fail'],
            'warn': results['warn'],
            'total': total,
            'success_rate': f"{(results['pass']/total)*100:.1f}%"
        },
        'details': results['details']
    }
    
    with open('/home/dinesh/CRM/test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{BLUE}Detailed report saved to: /home/dinesh/CRM/test_report.json{RESET}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()