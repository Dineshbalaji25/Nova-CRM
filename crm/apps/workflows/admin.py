from django.contrib import admin
from .models import Workflow, WorkflowNode, WorkflowExecution, NodeExecution, Blueprint, BlueprintState, BlueprintTransition, BlueprintRecordContext

admin.site.register(Workflow)
admin.site.register(WorkflowNode)
admin.site.register(WorkflowExecution)
admin.site.register(NodeExecution)
admin.site.register(Blueprint)
admin.site.register(BlueprintState)
admin.site.register(BlueprintTransition)
admin.site.register(BlueprintRecordContext)
