import logging
from django.apps import apps
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from apps.workflows.engine import evaluate_condition # We might use parts of this or implement a QuerySet version

logger = logging.getLogger(__name__)

class ReportExecutor:
    """
    Service to execute Report definitions and return structured data.
    """
    
    AGGREGATE_MAP = {
        'sum': Sum,
        'avg': Avg,
        'count': Count,
        'max': Max,
        'min': Min,
    }

    @classmethod
    def execute(cls, report, tenant_id, date_range=None):
        """
        Executes a report and returns a dict with results.
        """
        try:
            # 1. Resolve Model
            app_label, model_name = report.target_model.split('.')
            Model = apps.get_model(app_label, model_name)
            
            # 2. Initial QuerySet
            qs = Model.objects.filter(tenant_id=tenant_id)
            
            # 3. Apply Filters (Simple version: field__operator=value)
            # report.filters example: {"status": "new", "source__contains": "Web"}
            if report.filters:
                qs = qs.filter(**report.filters)
                
            # 4. Apply Date Range if provided
            if date_range:
                # Expecting {"field": "created_at", "start": "...", "end": "..."}
                field = date_range.get('field', 'created_at')
                if 'start' in date_range:
                    qs = qs.filter(**{f"{field}__gte": date_range['start']})
                if 'end' in date_range:
                    qs = qs.filter(**{f"{field}__lte": date_range['end']})

            # 5. Grouping & Aggregation
            if report.group_by:
                # Grouping by a field (e.g. 'status')
                aggregation_kwargs = {}
                for field, func_name in report.aggregate_functions.items():
                    func = cls.AGGREGATE_MAP.get(func_name.lower())
                    if func:
                        aggregation_kwargs[f"{field}_{func_name}"] = func(field)
                
                if not aggregation_kwargs:
                    # Default to count if no agg provided but group_by exists
                    aggregation_kwargs['count'] = Count('id')
                
                results = qs.values(report.group_by).annotate(**aggregation_kwargs).order_by(report.group_by)
                return list(results)
            
            # 6. Tabular Data (No grouping)
            columns = report.selected_columns or ['id', 'created_at']
            # Ensure columns exist on model to avoid crash
            valid_columns = [c for c in columns if hasattr(Model, c.split('__')[0])]
            
            return list(qs.values(*valid_columns)[:1000]) # Cap at 1000 for safety
            
        except Exception as e:
            logger.error(f"Report execution failed for {report.id}: {str(e)}")
            raise

class FunnelAnalyzer:
    """
    Calculates conversion funnels.
    """
    @classmethod
    def analyze_stage_conversion(cls, tenant_id, model_name='crm.Lead', stage_field='status', stages=None):
        """
        Returns count and conversion % for each stage.
        """
        app_label, model_name = model_name.split('.')
        Model = apps.get_model(app_label, model_name)
        
        if not stages:
            # Default Lead stages if not provided
            stages = ['new', 'contacted', 'qualified', 'converted']
            
        funnel_data = []
        prev_count = 0
        
        for i, stage in enumerate(stages):
            count = Model.objects.filter(tenant_id=tenant_id, **{stage_field: stage}).count()
            
            conversion_rate = 100.0
            if i > 0 and prev_count > 0:
                conversion_rate = (count / prev_count) * 100
                
            funnel_data.append({
                "stage": stage,
                "count": count,
                "conversion_rate": round(conversion_rate, 2)
            })
            prev_count = count
            
        return funnel_data
