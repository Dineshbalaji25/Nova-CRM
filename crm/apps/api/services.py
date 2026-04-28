import hmac
import hashlib
import json
import time
import requests
from django.utils import timezone
from .models import WebhookEndpoint, WebhookEventLog

class WebhookDispatcher:
    
    @staticmethod
    def sign_payload(secret, payload_body, timestamp):
        """
        Generates HMAC-SHA256 signature.
        Format: t={timestamp},v1={hash}
        """
        to_sign = f"{timestamp}.{payload_body}"
        signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    @classmethod
    def dispatch(cls, endpoint_id, event_type, data, attempt=1):
        """
        Synchronous dispatch logic (called by worker).
        """
        try:
            endpoint = WebhookEndpoint.objects.get(id=endpoint_id)
        except WebhookEndpoint.DoesNotExist:
            return

        if endpoint.status != 'active':
            return

        # Prepare Payload
        payload = {
            "id": f"evt_{int(time.time()*1000)}",
            "event": event_type,
            "created_at": timezone.now().isoformat(),
            "data": data,
            "attempt": attempt
        }
        json_body = json.dumps(payload)
        timestamp = str(int(time.time()))
        
        # Sign
        signature = cls.sign_payload(endpoint.secret, json_body, timestamp)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CRM-SaaS-Webhook/1.0",
            "X-CRM-Signature": signature
        }

        # Send
        start_time = time.time()
        success = False
        status_code = 0
        resp_text = ""
        
        try:
            response = requests.post(
                endpoint.url, 
                data=json_body, 
                headers=headers, 
                timeout=5
            )
            status_code = response.status_code
            resp_text = response.text[:1000] # Truncate log
            duration = int((time.time() - start_time) * 1000)
            
            if 200 <= status_code < 300:
                success = True
                endpoint.failure_count = 0 
                endpoint.save()
            else:
                # 4xx/5xx error
                endpoint.failure_count += 1
                if endpoint.failure_count >= 50:
                    endpoint.status = 'failing'
                endpoint.save()
                
        except requests.RequestException as e:
            resp_text = str(e)
            endpoint.failure_count += 1
            endpoint.save()
            duration = int((time.time() - start_time) * 1000)

        # Log
        WebhookEventLog.objects.create(
            endpoint=endpoint,
            event_type=event_type,
            payload=payload,
            response_status=status_code,
            response_body=resp_text,
            duration_ms=duration,
            attempt=attempt,
            is_success=success
        )
        
        return success
