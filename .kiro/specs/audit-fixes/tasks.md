# Audit Fixes — Tasks

## Wave 1 — Settings & Infrastructure (no model changes)

- [x] 1. Fix insecure defaults in `config/settings.py` and `.env.example`
  - Remove insecure `SECRET_KEY` default (raise `ImproperlyConfigured`)
  - Set `DEBUG` default to `False`
  - Set `ALLOWED_HOSTS` default to `[]`
  - Add `SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)`, `SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)`, `CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)`, `SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)`, `SESSION_COOKIE_HTTPONLY = True`, `SECURE_CONTENT_TYPE_NOSNIFF = True`
  - Update `.env.example`: add `DEBUG=False` as the recommended value with a comment

- [x] 2. Fix `hmac` call in `WebhookDispatcher.sign_payload()`
  - File: `crm/apps/api/services.py`
  - Verify and correct the `hmac` usage — use `hmac.new(key=secret.encode('utf-8'), msg=to_sign.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()`
  - Test by reading Python docs: `hmac.new` is valid Python 3 syntax (alias for `hmac.HMAC`), ensure import is `import hmac, hashlib`

- [x] 3. Fix sensitive data leakage in `AuditMiddleware`
  - File: `crm/apps/audit/middleware.py`
  - Add `SENSITIVE_KEYS = frozenset({'password', 'client_secret', 'access_token', 'refresh_token', 'api_key', 'auth_token', 'webhook_secret', 'key', 'secret', 'token', 'cvv', 'card_number'})`
  - Change filter to: `{k: v for k, v in payload.items() if not any(s in k.lower() for s in SENSITIVE_KEYS)}`
  - Add content-type guard: `if 'application/json' not in request.content_type: skip JSON parsing`
  - Replace bare `except:` with `except (json.JSONDecodeError, UnicodeDecodeError, ValueError):`

- [x] 4. Add `gte`/`lte` operators to workflow condition evaluator
  - File: `crm/apps/workflows/engine.py`
  - In `evaluate_condition()`, add after the `lt` branch: `elif operator == 'gte': return actual_value >= target_value` and `elif operator == 'lte': return actual_value <= target_value`

- [x] 5. Fix `OrganizationMemberSerializer` nonexistent `joined_at` field
  - File: `crm/apps/users/serializers.py`
  - In `OrganizationMemberSerializer.Meta.fields`, replace `'joined_at'` with `'created_at'`

- [x] 6. Remove hardcoded fake dashboard stats
  - File: `crm/apps/analytics/stats_views.py`
  - Replace `revenue_growth: 12.5`, `deals_trend: 8.2`, `leads_trend: -2.4`, `win_rate_trend: 5.0` with `None`
  - Replace hardcoded `ai_insights` list with `[]`
  - Add `"trends_computed": False` flag in the response

- [x] 7. Raise `PermissionDenied` when `tenant_id` is missing in `BaseTenantViewSet`
  - File: `crm/apps/crm/views.py`
  - At start of `get_queryset()`, add: `if not getattr(self.request, 'tenant_id', None): from rest_framework.exceptions import PermissionDenied; raise PermissionDenied('Tenant context is required. Provide X-Tenant-ID header.')`

- [x] 8. Refactor `IsOrganizationMember` to single database query
  - File: `crm/apps/users/permissions.py`
  - Replace the `.exists()` + `.get()` pattern with a single `.filter(...).first()` call
  - If `membership` is not None, set `request.user.current_role = membership.role` and return `True`
  - Remove any `DoesNotExist` risk

## Wave 2 — Security Patches

- [x] 9. Fix Google Auth to use official library
  - File: `crm/apps/users/views.py` and `crm/requirements.txt`
  - Add `google-auth` to requirements.txt
  - In `GoogleAuthView.post()`, replace `requests.get('https://oauth2.googleapis.com/tokeninfo', ...)` block with:
    ```python
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
    try:
        token_info = google_id_token.verify_oauth2_token(
            id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        return Response({'error': f'Invalid Google token: {e}'}, status=status.HTTP_400_BAD_REQUEST)
    ```
  - Remove the manual `audience` and `email_verified` checks (library handles them)
  - Keep `email = token_info.get('email')` and subsequent logic unchanged

- [x] 10. Fix webhook secret timing attack in `TalesTimelineWebhookView`
  - File: `crm/apps/integrations/views.py`
  - Replace `IntegrationProvider.objects.filter(webhook_secret=secret, ...).first()` with:
    1. Fetch all active providers: `providers = IntegrationProvider.objects.filter(is_active=True)`
    2. Loop and use `hmac.compare_digest(str(p.webhook_secret), str(secret))` for constant-time compare
    3. Set `provider = matched_provider` or return 401 if none match

- [x] 11. Fix mass assignment in `WebFormSubmitView`
  - File: `crm/apps/marketing/views.py`
  - Add at top of file:
    ```python
    LEAD_SAFE_FIELDS = frozenset({'first_name', 'last_name', 'email', 'phone', 'company_name', 'source', 'title'})
    CONTACT_SAFE_FIELDS = frozenset({'first_name', 'last_name', 'email', 'phone'})
    ```
  - Replace `hasattr(Lead if ..., key)` with `key in (LEAD_SAFE_FIELDS if webform.target_model == 'lead' else CONTACT_SAFE_FIELDS)`

- [x] 12. Add OAuth redirect URI validation
  - File: `crm/apps/users/views.py`
  - In `TokenExchangeView.post()`, for `grant_type == 'authorization_code'`:
    ```python
    redirect_uri = request.data.get('redirect_uri', '')
    if app.redirect_uri and redirect_uri != app.redirect_uri:
        return Response({'error': 'invalid_grant', 'details': 'redirect_uri mismatch'}, status=status.HTTP_400_BAD_REQUEST)
    ```

- [x] 13. Add Stripe `invoice.paid` and `invoice.payment_failed` handlers
  - File: `crm/apps/billing/webhooks.py`
  - After the `customer.subscription.updated` block, add:
    ```python
    elif evt_type == 'invoice.paid':
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(gateway_subscription_id=sub_id).update(status='active')
    elif evt_type == 'invoice.payment_failed':
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(gateway_subscription_id=sub_id).update(status='past_due')
    ```

- [x] 14. Make `client_secret` write-only in `OAuthApplicationSerializer`
  - File: `crm/apps/users/serializers.py`
  - Add `extra_kwargs = {'client_secret': {'write_only': True}}` to `OAuthApplicationSerializer.Meta`
  - In `OAuthApplicationViewSet` (in views.py), override `create()` to return `client_secret` in the creation response only (by serializing with `instance.client_secret` in a custom response)

- [x] 15. Add OAuth scope enforcement
  - File: `crm/apps/users/authentication.py`
  - In `OAuthTokenAuthentication.authenticate()`, after verifying token, add: `request.oauth_scopes = [s.strip() for s in token_obj.scopes.split(',') if s.strip()]`
  - Add `HasOAuthScope` class to `crm/apps/users/permissions.py`:
    ```python
    class HasOAuthScope(permissions.BasePermission):
        required_scopes = []
        def has_permission(self, request, view):
            if not hasattr(request, 'oauth_scopes'):
                return True  # Non-OAuth request, defer to other permissions
            view_scopes = getattr(view, 'required_scopes', self.required_scopes)
            if not view_scopes:
                return True
            return any(scope in request.oauth_scopes for scope in view_scopes) or 'NovaCRM.modules.ALL' in request.oauth_scopes
    ```

- [x] 16. Fix `ReportExecutor` ORM field injection
  - File: `crm/apps/analytics/services.py`
  - After resolving `Model`, build: `allowed_fields = {f.name for f in Model._meta.get_fields() if hasattr(f, 'column')}`
  - Before each `qs.filter(**{field: val})`, check `field.split('__')[0] in allowed_fields` — skip if not
  - Apply same check to `group_by` and keys in `aggs_dict`

## Wave 3 — Logic Bug Fixes

- [x] 17. Implement `BillingService.record_usage()`
  - File: `crm/apps/billing/services.py`
  - Replace `pass` with:
    ```python
    from django.db.models import F
    from datetime import timedelta
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end_of_month = start_of_month.replace(year=now.year + 1, month=1)
    else:
        end_of_month = start_of_month.replace(month=now.month + 1)
    updated = UsageRecord.objects.filter(
        tenant_id=tenant_id, metric=metric, period_start=start_of_month
    ).update(count=F('count') + count)
    if not updated:
        UsageRecord.objects.get_or_create(
            tenant_id=tenant_id, metric=metric, period_start=start_of_month,
            defaults={'count': count, 'period_end': end_of_month}
        )
    ```

- [x] 18. Fix `ScoringEngine` signal loop and N+1 queries
  - File: `crm/apps/crm/services.py`
  - Before the loop, prefetch: `applied_ids = set(AppliedScoringRule.objects.filter(record_model=model_name, record_id=instance.id).values_list('rule_id', flat=True))`
  - Replace `if AppliedScoringRule.objects.filter(...).exists()` with `if rule.id in applied_ids`
  - Accumulate: `total_score = 0; new_applications = []`
  - Inside loop: `total_score += rule.score_change; new_applications.append(AppliedScoringRule(...))`
  - After loop: `if total_score != 0: instance.score += total_score; instance.save(update_fields=['score'])`
  - After loop: `AppliedScoringRule.objects.bulk_create(new_applications, ignore_conflicts=True)`

- [x] 19. Fix workflow engine to advance to next node
  - File: `crm/apps/workflows/engine.py`
  - At end of `run_node()`, after the if/elif dispatch block:
    - Update `log.status = 'success'`, `log.output_data = result`, `log.completed_at = timezone.now()`, call `log.save()`
    - Update `execution.current_node_id = next_step_id`, call `execution.save(update_fields=['current_node'])`
    - If `next_step_id`: `from .tasks import process_workflow_step; process_workflow_step.delay(str(execution_id), str(next_step_id))`
    - Else: `execution.status = 'completed'; execution.completed_at = timezone.now(); execution.save()`

- [x] 20. Add tenant scoping to AI deal suggestions task
  - File: `crm/apps/crm/tasks.py`
  - Add import: `from apps.billing.models import Subscription`
  - Before querying deals: `active_tenant_ids = set(Subscription.objects.filter(status__in=['active', 'trialing']).values_list('tenant_id', flat=True))`
  - Change `Deal.objects.filter(...)` to `Deal.objects.filter(..., tenant_id__in=active_tenant_ids)`

- [x] 21. Fix `TerritoryEngine` to break after first owner assignment
  - File: `crm/apps/crm/services.py`
  - After `instance.save(update_fields=['owner'])` in `TerritoryEngine.process_record()`, add `break`

- [x] 22. Fix `GDPRService.anonymize_tenant_data()` to use bulk update
  - File: `crm/apps/audit/utils.py`
  - Replace the for-loop with:
    ```python
    from django.db.models.functions import Cast
    Contact.objects.filter(tenant_id=tenant_id).update(
        first_name='Anonymized',
        last_name='User',
        phone='',
        custom_data={},
    )
    # Email needs to be unique per contact — use a subquery or set a pattern
    # Use raw SQL via annotate+update or just loop for email only:
    Contact.objects.filter(tenant_id=tenant_id).update(
        email=models.Func(
            models.Value('deleted_'),
            models.Cast('id', output_field=models.TextField()),
            models.Value('@removed.invalid'),
            function='CONCAT'
        )
    )
    ```
    If `CONCAT` approach is complex, simplify: loop only for the email field update (keep the bulk update for all other fields), calling `.update()` for all non-unique fields and a tight loop only for email.

- [x] 23. Fix `LeadConversionService` race condition
  - File: `crm/apps/crm/services.py`
  - Wrap `get_or_create` in:
    ```python
    from django.db import IntegrityError
    try:
        company, created = Company.objects.get_or_create(...)
    except IntegrityError:
        company = Company.objects.get(tenant_id=lead.tenant_id, name=lead.company_name)
    ```

- [x] 24. Add `is_deleted=False` to service layer queries
  - Files to update:
    - `crm/apps/workflows/services.py`: add `is_deleted=False` to `Blueprint.objects.filter(...)`, `BlueprintRecordContext.objects.filter(...)`
    - `crm/apps/crm/services.py`: add to `ScoringRule.objects.filter(...)`, `AssignmentRule.objects.filter(...)`
    - `crm/apps/omnichannel/services.py`: add to `Contact.objects.filter(...)`, `Lead.objects.filter(...)`
    - `crm/apps/crm/ai.py`: add to `Lead.objects.get(...)` (use `filter().first()` with `is_deleted=False`), `Deal.objects.get(...)`, `Note.objects.filter(...)`, `Activity.objects.filter(...)`

- [x] 25. Fix portal ViewSets to scope querysets
  - File: `crm/apps/portals/views.py`
  - In `PortalDealViewSet`, override `get_queryset()` to return `Deal.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)`
  - In `PortalBillingInvoiceViewSet`, override `get_queryset()` to return `BillingInvoice.objects.filter(tenant_id=self.request.tenant_id, is_deleted=False)`
  - In `PortalFilterMixin.get_queryset()`, add: `if not portal_member: return queryset.none()`

- [x] 26. Add CSV import size and billing limit guards
  - File: `crm/apps/crm/views.py`
  - At start of `import_csv`: check `if file.size > 5 * 1024 * 1024: return Response({'error': 'File too large. Max 5MB.'}, status=400)`
  - After collecting `contacts_to_create`, add row limit: `if len(contacts_to_create) > 10000: return Response({'error': 'Too many rows. Max 10,000 per import.'}, status=400)`
  - Before `bulk_create`, call `allowed, reason = BillingService.check_limit(request.tenant_id, 'contacts', increment=len(contacts_to_create))` and return 402 if not allowed

## Wave 4 — Model Changes + Migrations

- [x] 27. Encrypt `PhoneIntegration.auth_token`
  - File: `crm/apps/omnichannel/models.py`
  - Change `auth_token = models.CharField(max_length=255)` to `auth_token = EncryptedCharField(max_length=255)`
  - Import `EncryptedCharField` from `encrypted_model_fields.fields` (already imported in the file for EmailIntegration)
  - Create migration file: `crm/apps/omnichannel/migrations/000X_encrypt_phoneintegration_authtoken.py`
  - Run `python manage.py makemigrations omnichannel --name encrypt_phoneintegration_authtoken` equivalent (write migration manually if needed)

- [x] 28. Add `deal` FK to `CallLog` and fix `OmnichannelService`
  - File: `crm/apps/omnichannel/models.py`
  - Add to `CallLog`: `deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='calls')`
  - Create migration
  - File: `crm/apps/omnichannel/services.py`
  - In `get_timeline()`, wrap `calls = CallLog.objects.filter(**filter_kwargs)` in try/except `FieldError`, returning empty list for calls if field doesn't exist

- [x] 29. Add `last_executed_at` to `Workflow` model
  - File: `crm/apps/workflows/models.py`
  - Add `last_executed_at = models.DateTimeField(null=True, blank=True, help_text='Last time this scheduled workflow was executed')`
  - Create migration
  - File: `crm/apps/workflows/tasks.py`
  - In `evaluate_scheduled_workflows()`, check: `if wf.last_executed_at is not None` and compare to `timezone.now()` using the `trigger_config.get('interval_minutes', 60)`. Only fire if elapsed. After creating execution: `wf.last_executed_at = timezone.now(); wf.save(update_fields=['last_executed_at'])`
