from django.apps import apps
from django.db.models import Count, Sum, Avg, Min, Max

class ReportExecutor:
    """
    Dynamically builds Django querysets based on JSON configuration.
    """
    
    AGGREGATION_MAP = {
        'count': Count,
        'sum': Sum,
        'avg': Avg,
        'min': Min,
        'max': Max,
    }

    @classmethod
    def execute(cls, report, tenant_id):
        """
        Executes a Report object's configuration.
        """
        model_name = report.target_model
        try:
            Model = apps.get_model('crm', model_name)
        except LookupError:
            try:
                Model = apps.get_model('sales', model_name)
            except LookupError:
                raise ValueError(f"Model {model_name} not found in crm or sales apps.")
                
        # 1. Base Queryset (Tenant scoped)
        qs = Model.objects.filter(tenant_id=tenant_id, is_deleted=False)
        
        # 2. Apply Filters
        # Ex: [{"field": "status", "operator": "eq", "value": "won"}]
        filters = report.filter_config
        if isinstance(filters, list):
            for f in filters:
                field = f.get('field')
                op = f.get('operator', 'eq')
                val = f.get('value')
                
                if not field:
                    continue
                    
                if op == 'eq':
                    qs = qs.filter(**{field: val})
                elif op == 'neq':
                    qs = qs.exclude(**{field: val})
                elif op == 'gt':
                    qs = qs.filter(**{f"{field}__gt": val})
                elif op == 'gte':
                    qs = qs.filter(**{f"{field}__gte": val})
                elif op == 'lt':
                    qs = qs.filter(**{f"{field}__lt": val})
                elif op == 'lte':
                    qs = qs.filter(**{f"{field}__lte": val})
                elif op == 'contains':
                    qs = qs.filter(**{f"{field}__icontains": val})
                    
        # 3. Apply Grouping / Aggregation
        # Ex: {"group_by": "stage_id", "aggregations": [{"type": "sum", "field": "amount"}]}
        agg_config = report.aggregation_config
        if isinstance(agg_config, dict) and agg_config:
            group_by = agg_config.get('group_by')
            aggs = agg_config.get('aggregations', [])
            
            if group_by:
                qs = qs.values(group_by)
                
            annotate_args = {}
            for agg in aggs:
                agg_type = agg.get('type')
                field = agg.get('field')
                if agg_type in cls.AGGREGATION_MAP and field:
                    # e.g. amount_sum = Sum('amount')
                    alias = f"{field}_{agg_type}"
                    annotate_args[alias] = cls.AGGREGATION_MAP[agg_type](field)
                    
            if annotate_args:
                qs = qs.annotate(**annotate_args)
                
        # 4. Limit/Ordering (MVP: default ordering if grouped, else limit 1000)
        # If it's a list of records, limit to 1000 to prevent massive payloads.
        if not (isinstance(agg_config, dict) and agg_config.get('group_by')):
            qs = qs[:1000]
            
        return list(qs)
