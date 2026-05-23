from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from apps.users.models import Organization
from apps.crm.models import Deal, Pipeline, Stage, Note, Activity
from apps.workflows.models import Workflow, WorkflowNode, WorkflowExecution, NodeExecution
from apps.workflows.engine import run_node

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WorkflowEngineTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Workflow Org", slug="workflow-org")
        self.user = User.objects.create_user(email="workflow@example.com", password="password")
        self.pipeline = Pipeline.objects.create(name="Sales", tenant=self.org)
        self.stage = Stage.objects.create(pipeline=self.pipeline, name="New", position=1, tenant=self.org)

    def test_workflow_trigger_and_execution_flow(self):
        # 1. Create a workflow: triggers on deal.created with amount > 1000
        workflow = Workflow.objects.create(
            tenant=self.org,
            name="High Value Deal Flow",
            is_active=True,
            trigger_type="event",
            trigger_config={
                "event": "deal.created",
                "filters": [
                    {"field": "deal.amount", "operator": "gt", "value": 1000}
                ]
            }
        )

        # 2. Add nodes:
        # Node 1: Condition: does title contain "Premium"?
        cond_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="condition",
            label="Is Premium?",
            config={"field": "deal.title", "operator": "contains", "value": "Premium"}
        )

        # Node 2: Action: create note
        note_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="action",
            label="Create Note",
            action_key="crm.create_note",
            config={
                "model": "deal",
                "id": "{{ deal.id }}",
                "body": "Automated note: Premium deal {{ deal.title }} was created with amount {{ deal.amount }}"
            }
        )

        # Node 3: Action: create task
        task_node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="action",
            label="Create Task",
            action_key="crm.create_task",
            config={
                "model": "deal",
                "id": "{{ deal.id }}",
                "title": "Follow up on premium deal {{ deal.title }}",
                "description": "High value target task"
            }
        )

        # Link them up: Condition -> (True) -> Note -> Task
        cond_node.next_node = note_node
        cond_node.save()
        
        note_node.next_node = task_node
        note_node.save()

        # 3. Create a deal that triggers it
        deal = Deal.objects.create(
            tenant=self.org,
            title="Premium Deal A",
            amount=1500,
            pipeline=self.pipeline,
            stage=self.stage,
            owner=self.user
        )

        # 4. Verify workflow execution got kicked off
        executions = WorkflowExecution.objects.filter(workflow=workflow)
        self.assertEqual(executions.count(), 1)
        execution = executions.first()

        # Retrieve and verify execution status
        execution.refresh_from_db()
        self.assertEqual(execution.status, 'completed')
        
        # Verify note creation
        notes = Note.objects.filter(deal=deal)
        self.assertEqual(notes.count(), 1)
        note = notes.first()
        self.assertEqual(note.body, "Automated note: Premium deal Premium Deal A was created with amount 1500")
        self.assertEqual(note.tenant_id, self.org.id)

        # Verify task (activity) creation
        activities = Activity.objects.filter(deal=deal, activity_type="task")
        self.assertEqual(activities.count(), 1)
        task = activities.first()
        self.assertEqual(task.subject, "Follow up on premium deal Premium Deal A")
        self.assertEqual(task.body, "High value target task")
        self.assertEqual(task.tenant_id, self.org.id)
