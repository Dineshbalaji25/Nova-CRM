from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from apps.users.permissions import IsOrganizationMember
from apps.crm.models import Deal, Lead, Activity
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get(self, request):
        tenant_id = request.tenant_id

        # 1. Revenue & Deals
        deals = Deal.objects.filter(tenant_id=tenant_id, is_deleted=False)
        total_revenue = deals.aggregate(Sum('amount'))['amount__sum'] or 0
        active_deals = deals.exclude(status__in=['closed_won', 'closed_lost']).count()

        # 2. Leads & Conversion
        leads = Lead.objects.filter(tenant_id=tenant_id, is_deleted=False)
        total_leads = leads.count()
        converted_leads = leads.filter(status='converted').count()
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        # 3. Win Rate
        closed_deals = deals.filter(status__in=['closed_won', 'closed_lost']).count()
        won_deals = deals.filter(status='closed_won').count()
        win_rate = (won_deals / closed_deals * 100) if closed_deals > 0 else 0

        # 4. Recent Activity (Already exists in ActivityViewSet, but we can aggregate here if needed)
        # For now, we provide the summary stats

        return Response({
            "kpis": {
                "total_revenue": total_revenue,
                "active_deals": active_deals,
                "leads_converted": converted_leads,
                "conversion_rate": round(conversion_rate, 1),
                "win_rate": round(win_rate, 1),
                "revenue_growth": 12.5, # Placeholder for trend analysis
                "deals_today": leads.filter(created_at__date=timezone.now().date()).count(),
                "leads_trend": -2.4, # Placeholder
                "win_rate_trend": 5.0 # Placeholder
            },
            "ai_insights": [
                {
                    "id": 1,
                    "title": "High-value Deal at Risk",
                    "description": "Acme Corp deal has had no activity for 5 days.",
                    "type": "warning"
                },
                {
                    "id": 2,
                    "title": "Conversion Opportunity",
                    "description": "Lead 'Jane Doe' has opened your proposal 3 times today.",
                    "type": "insight"
                }
            ]
        })
