from rest_framework import viewsets, serializers
from .models import Ticket
from apps.crm.views import BaseTenantViewSet

class TicketSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.get_full_name')

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class TicketViewSet(BaseTenantViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    search_fields = ['subject', 'description']
    filterset_fields = ['status', 'priority', 'assigned_to']
