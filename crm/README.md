# Antigravity CRM (SaaS)

A modern, API-first, multi-tenant CRM built with Django, DRF, and Vanilla JS.

## Architecture

*   **Backend**: Django Modular Monolith (API-first)
*   **Database**: PostgreSQL (Hybrid Multi-Tenancy via `tenant_id`)
*   **Task Queue**: Celery + Redis
*   **Frontend**: Vanilla HTML/CSS/JS (No build step required)

## Apps Structure

*   `core`: Multi-tenancy middleware, base models, utilities.
*   `users`: Authentication, RBAC, Organizations.
*   `crm`: Contacts, Deals, Pipelines (The core product).
*   `workflows`: Automation engine (Drag & Drop backend logic).
*   `api`: Webhook platform & Developer API keys.
*   `billing`: Subscriptions & Usage metering.
*   `audit`: Security logs & GDPR compliance.

## Quick Start (Docker) - Recommended

1.  **Build & Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access App**:
    *   API Root: `http://localhost:8000/api/v1/`
    *   Frontend: You need to serve `frontend/pages/`
    
    *For simple frontend testing:*
    ```bash
    cd frontend/pages
    python3 -m http.server 3000
    # Open http://localhost:3000/login.html
    ```

## Local Development (Manual)

1.  **Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Database**:
    Ensure PostgreSQL and Redis are running.
    ```bash
    export DATABASE_URL=postgres://user:pass@localhost:5432/crm_db
    export REDIS_URL=redis://localhost:6379/0
    ```

3.  **Run**:
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

4.  **Celery**:
    ```bash
    celery -A config worker --loglevel=info
    ```
