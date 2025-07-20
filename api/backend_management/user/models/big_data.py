from django.db import models
from django.utils import timezone
from decimal import Decimal

class KubernetesCluster(models.Model):
    name = models.CharField(max_length=255)
    endpoint = models.URLField()
    status = models.CharField(max_length=50)

    def manage_cluster(self):
        # Logic to manage the Kubernetes cluster
        # Example: Update status based on cluster health
        pass

class DAG(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    clusters = models.ManyToManyField(KubernetesCluster, related_name='dags')

    def schedule_dag(self, components_data):
        """
        Schedule the DAG by creating components and deploying to clusters.
        components_data: List of dicts with component details
        """
        components = []
        for comp_data in components_data:
            component = Component.objects.create(
                dag=self,
                type=comp_data['type'],
                execution_command=comp_data['execution_command'],
                order=comp_data['order']
            )
            components.append(component)
        # Additional logic to deploy to clusters
        return components

class Component(models.Model):
    COMPONENT_TYPES = (
        ('Spark', 'Spark'),
        ('Flink', 'Flink'),
        ('Shell', 'Shell'),
        ('Jar', 'Jar'),
    )
    dag = models.ForeignKey(DAG, on_delete=models.CASCADE, related_name='components')
    type = models.CharField(max_length=50, choices=COMPONENT_TYPES)
    execution_command = models.TextField()
    order = models.IntegerField()

    def execute(self, dag_id, cluster_id, parameters):
        """
        Execute the component by creating a Task.
        """
        task = Task.objects.create(
            component=self,
            dag_id=dag_id,
            cluster_id=cluster_id,
            status='running',
            parameters=parameters
        )
        return task

class Task(models.Model):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='tasks')
    dag = models.ForeignKey(DAG, on_delete=models.CASCADE, related_name='tasks')
    cluster = models.ForeignKey(KubernetesCluster, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    parameters = models.JSONField()

    def complete_task(self, success=True):
        """
        Mark the task as completed or failed, generate logs, alerts, and billing.
        """
        self.status = 'completed' if success else 'failed'
        self.end_time = timezone.now()
        self.save()

        # Generate log
        Log.objects.create(
            task=self,
            timestamp=timezone.now(),
            message="Task completed successfully." if success else "Task failed.",
            level="INFO" if success else "ERROR"
        )

        # Trigger alert if failed
        if not success:
            Alert.objects.create(
                task=self,
                timestamp=timezone.now(),
                message="Task failed.",
                severity="CRITICAL"
            )

        # Incurs billing
        Billing.objects.create(
            task=self,
            amount=Decimal('25.50'),  # Example fixed amount
            currency="USD",
            billed_at=timezone.now()
        )

class Log(models.Model):
    LEVEL_CHOICES = (
        ('INFO', 'Info'),
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)

class Alert(models.Model):
    SEVERITY_CHOICES = (
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='alerts')
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES)

class Billing(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='billing')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    billed_at = models.DateTimeField(default=timezone.now)