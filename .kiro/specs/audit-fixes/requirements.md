# Audit Fixes — Requirements

## Overview
Fix all critical security vulnerabilities, logic bugs, and design issues identified in the full codebase audit of the Nova CRM Django project.

---

## Security Fixes

### REQ-1: Google Auth SSRF / Wrong Verification
Replace `requests.get('https://oauth2.googleapis.com/tokeninfo', ...)` in `GoogleAuthView` with `google.oauth2.id_token.verify_oauth2_token` from the `google-auth` library. Add `google-auth` to `requirements.txt`.

### REQ-2: Insecure Production Defaults in settings.py
- `SECRET_KEY` must raise `ImproperlyConfigured` if not set (remove insecure default).
- `DEBUG` must default to `False`.
- `ALLOWED_HOSTS` must default to `[]`.
- Add security settings: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_HTTPONLY`, `SECURE_CONTENT_TYPE_NOSNIFF` — controlled by env vars, defaulting to secure values.
- Update `.env.example` to show `DEBUG=False`.

### REQ-3: Webhook Secret Timing Attack
`TalesTimelineWebhookView` must compare secrets using `hmac.compare_digest()` instead of a DB filter equality check.

### REQ-4: `hmac.new()` Crash Fix
In `apps/api/services.py` `WebhookDispatcher.sign_payload()`, replace `hmac.new(...)` with `hmac.new(...)` verified against Python 3.10+ behavior — use `hmac.new(key, msg, digestmod)` which is the correct Python 3 API (it is an alias for `hmac.HMAC`). Verify the import and call are correct.

### REQ-5: Mass Assignment in `WebFormSubmitView`
Define explicit allowlists: `LEAD_SAFE_FIELDS` and `CONTACT_SAFE_FIELDS`. Only map allowlisted fields to model kwargs. All other submitted fields go to `custom_data`.

### REQ-6: Stripe Webhook Missing Handlers
Add `invoice.paid` (set subscription `active`) and `invoice.payment_failed` (set `past_due`) handlers in `apps/billing/webhooks.py`.

### REQ-7: Sensitive Data in Audit Logs
Extend `AuditMiddleware` sensitive field filter to cover: password, client_secret, access_token, refresh_token, api_key, auth_token, webhook_secret, key, secret, token, cvv, card_number. Add content-type guard before JSON parsing.

### REQ-8: Plaintext `PhoneIntegration.auth_token`
Change to `EncryptedCharField`. Create migration.

### REQ-9: `OAuthApplicationSerializer` Exposes `client_secret`
Make `client_secret` write-only (never returned in responses after creation).

### REQ-10: OAuth Redirect URI Validation
In `TokenExchangeView`, validate `redirect_uri` matches `app.redirect_uri` for `authorization_code` grant type.

### REQ-11: OAuth Scope Enforcement
Attach `request.oauth_scopes` in `OAuthTokenAuthentication`. Create `HasOAuthScope` permission class.

### REQ-12: `ReportExecutor` ORM Injection
Validate filter field names against `Model._meta.get_fields()` before passing to Django ORM filter.

---

## Logic Bug Fixes

### REQ-13: `BillingService.record_usage()` Stub
Implement with `F('count') + count` atomic increment and proper month-aligned `period_end`.

### REQ-14: `ScoringEngine` Signal Loop and N+1
Prefetch applied rule IDs. Accumulate score changes. Call `save()` once after loop.

### REQ-15: Workflow Engine Not Advancing Nodes
At end of `run_node()`, call `process_workflow_step.delay(execution_id, next_step_id)` when `next_step_id` is not None. Mark execution `completed` when no next step.

### REQ-16: Scheduled Workflows Fire Every Run
Add `last_executed_at` to `Workflow` model. Only fire if interval has elapsed. Update after firing.

### REQ-17: AI Tasks No Tenant Scoping
Filter `Deal` queryset to only active/trialing tenant subscriptions in `generate_ai_suggestions_for_all_deals`.

### REQ-18: Fake Dashboard Stats
Replace hardcoded trend placeholders with `null` and remove fake `ai_insights`.

### REQ-19: `PortalDealViewSet` Unscoped Queryset
Add tenant scoping. Return `none()` in `PortalFilterMixin` when no portal_member found.

### REQ-20: CSV Import No Guards
Add 5MB file size check, 10k row limit, billing limit check via `BillingService.check_limit()`.

### REQ-21: `BaseTenantViewSet` Silent Empty on Missing `tenant_id`
Raise `PermissionDenied` instead of filtering on `None`.

### REQ-22: `IsOrganizationMember` Double DB Query
Refactor to single `.filter().first()` call.

### REQ-23: `TerritoryEngine` No Break After Owner Assignment
Add `break` after owner is set.

### REQ-24: `GDPRService` Memory Issue
Replace per-object loop with bulk `update()`.

### REQ-25: `LeadConversionService` Race Condition
Wrap `get_or_create` in `try/except IntegrityError`, retry with `.get()`.

### REQ-26: `CallLog` Missing `deal` FK
Add `deal` ForeignKey to `CallLog`. Create migration.

### REQ-27: Soft Delete Not Excluded in Services
Add `is_deleted=False` to all direct model queries in service files.

### REQ-28: `evaluate_condition` Missing `gte`/`lte`
Add `gte` and `lte` operators.

### REQ-29: `OrganizationMemberSerializer` Wrong Field Name
Replace `joined_at` with `created_at`.

### REQ-30: `OmnichannelService` `FieldError` on Missing Model Field
Wrap `CallLog.objects.filter(deal_id=...)` in try/except for entity types that don't exist on the model.
