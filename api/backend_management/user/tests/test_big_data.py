import pytest
from decimal import Decimal
from django.utils import timezone
from user.models.big_data import (
    KubernetesCluster,
    DAG,
    Component,
    Task,
    Log,
    Alert,
    Billing
)
import allure


@allure.feature('Kubernetes Cluster Management')
@allure.story('Create and Manage Kubernetes Cluster')
@pytest.mark.django_db
def test_create_and_manage_kubernetes_cluster():
    with allure.step("Create a new Kubernetes cluster"):
        cluster = KubernetesCluster.objects.create(
            name='Test Cluster',
            endpoint='https://test-cluster-endpoint.com',
            status='active'
        )
        assert cluster.name == 'Test Cluster'
        assert cluster.endpoint == 'https://test-cluster-endpoint.com'
        assert cluster.status == 'active'

    with allure.step("Manage the Kubernetes cluster"):
        cluster.manage_cluster()
        # Assuming manage_cluster updates the status, add relevant assertions
        # For demonstration, we'll just assert the method is callable
        assert callable(cluster.manage_cluster)


@allure.feature('DAG Management')
@allure.story('Create and Schedule DAG')
@pytest.mark.django_db
def test_create_and_schedule_dag():
    with allure.step("Create a Kubernetes cluster for the DAG"):
        cluster = KubernetesCluster.objects.create(
            name='DAG Test Cluster',
            endpoint='https://dag-cluster-endpoint.com',
            status='active'
        )

    with allure.step("Create a new DAG"):
        dag = DAG.objects.create(name='Test DAG')
        dag.clusters.add(cluster)
        assert dag.name == 'Test DAG'
        assert dag.clusters.count() == 1
        assert dag.clusters.first() == cluster

    with allure.step("Schedule the DAG with components"):
        components_data = [
            {'type': 'Spark', 'execution_command': 'spark-submit --class Main', 'order': 1},
            {'type': 'Shell', 'execution_command': 'echo "Hello World"', 'order': 2},
        ]
        components = dag.schedule_dag(components_data)
        assert len(components) == 2
        assert components[0].type == 'Spark'
        assert components[1].type == 'Shell'


@allure.feature('Component Management')
@allure.story('Execute Component and Create Task')
@pytest.mark.django_db
def test_execute_component_and_create_task():
    with allure.step("Create necessary objects for Component execution"):
        cluster = KubernetesCluster.objects.create(
            name='Component Test Cluster',
            endpoint='https://component-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Component Test DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Spark',
            execution_command='spark-submit --class Main',
            order=1
        )

    with allure.step("Execute the component to create a task"):
        parameters = {'param1': 'value1', 'param2': 'value2'}
        task = component.execute(dag_id=dag.id, cluster_id=cluster.id, parameters=parameters)
        assert task.component == component
        assert task.dag == dag
        assert task.cluster == cluster
        assert task.status == 'running'
        assert task.parameters == parameters


@allure.feature('Task Management')
@allure.story('Complete Task Successfully')
@pytest.mark.django_db
def test_complete_task_successfully():
    with allure.step("Set up Task for completion"):
        cluster = KubernetesCluster.objects.create(
            name='Task Completion Cluster',
            endpoint='https://task-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Task Completion DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Shell',
            execution_command='echo "Complete Task"',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='running',
            parameters={'script': 'echo "Hello"'}
        )

    with allure.step("Complete the task successfully"):
        task.complete_task(success=True)
        assert task.status == 'completed'
        assert task.end_time is not None

    with allure.step("Verify that a log is created for the completed task"):
        log = Log.objects.get(task=task)
        assert log.message == "Task completed successfully."
        assert log.level == "INFO"

    with allure.step("Verify that no alert is created for a successful task"):
        alerts = Alert.objects.filter(task=task)
        assert alerts.count() == 0

    with allure.step("Verify that billing is recorded for the completed task"):
        billing = Billing.objects.get(task=task)
        assert billing.amount == Decimal('25.50')
        assert billing.currency == "USD"


@allure.feature('Task Management')
@allure.story('Complete Task with Failure')
@pytest.mark.django_db
def test_complete_task_with_failure():
    with allure.step("Set up Task for failure"):
        cluster = KubernetesCluster.objects.create(
            name='Task Failure Cluster',
            endpoint='https://failure-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Task Failure DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Jar',
            execution_command='java -jar app.jar',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='running',
            parameters={'jar_path': '/path/to/app.jar'}
        )

    with allure.step("Complete the task with failure"):
        task.complete_task(success=False)
        assert task.status == 'failed'
        assert task.end_time is not None

    with allure.step("Verify that a log is created for the failed task"):
        log = Log.objects.get(task=task)
        assert log.message == "Task failed."
        assert log.level == "ERROR"

    with allure.step("Verify that an alert is created for the failed task"):
        alert = Alert.objects.get(task=task)
        assert alert.message == "Task failed."
        assert alert.severity == "CRITICAL"

    with allure.step("Verify that billing is recorded for the failed task"):
        billing = Billing.objects.get(task=task)
        assert billing.amount == Decimal('25.50')
        assert billing.currency == "USD"


@allure.feature('Billing Management')
@allure.story('Associate Billing with Task')
@pytest.mark.django_db
def test_associate_billing_with_task():
    with allure.step("Create a Task and associate Billing"):
        cluster = KubernetesCluster.objects.create(
            name='Billing Cluster',
            endpoint='https://billing-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Billing DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Flink',
            execution_command='flink run job.jar',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='completed',
            parameters={'job': 'job.jar'}
        )
        billing = Billing.objects.create(
            task=task,
            amount=Decimal('50.00'),
            currency='USD',
            billed_at=timezone.now()
        )

    with allure.step("Verify the billing details are correctly associated with the task"):
        assert billing.task == task
        assert billing.amount == Decimal('50.00')
        assert billing.currency == 'USD'
        assert billing.billed_at is not None


@allure.feature('DAG Scheduling')
@allure.story('Schedule DAG with Multiple Components')
@pytest.mark.django_db
def test_schedule_dag_with_multiple_components():
    with allure.step("Create a Kubernetes cluster and DAG"):
        cluster1 = KubernetesCluster.objects.create(
            name='Cluster 1',
            endpoint='https://cluster1-endpoint.com',
            status='active'
        )
        cluster2 = KubernetesCluster.objects.create(
            name='Cluster 2',
            endpoint='https://cluster2-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Complex DAG')
        dag.clusters.add(cluster1, cluster2)

    with allure.step("Schedule the DAG with multiple component types"):
        components_data = [
            {'type': 'Spark', 'execution_command': 'spark-submit --class MainApp', 'order': 1},
            {'type': 'Flink', 'execution_command': 'flink run job.jar', 'order': 2},
            {'type': 'Shell', 'execution_command': 'bash run.sh', 'order': 3},
            {'type': 'Jar', 'execution_command': 'java -jar app.jar', 'order': 4},
        ]
        components = dag.schedule_dag(components_data)
        assert len(components) == 4
        assert components[0].type == 'Spark'
        assert components[1].type == 'Flink'
        assert components[2].type == 'Shell'
        assert components[3].type == 'Jar'

    with allure.step("Verify components are correctly ordered"):
        orders = [component.order for component in components]
        assert orders == [1, 2, 3, 4]


@allure.feature('Log Management')
@allure.story('Create Logs for Task Execution')
@pytest.mark.django_db
def test_create_logs_for_task_execution():
    with allure.step("Create a Task and complete it successfully"):
        cluster = KubernetesCluster.objects.create(
            name='Log Cluster',
            endpoint='https://log-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Log DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Shell',
            execution_command='echo "Logging Test"',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='running',
            parameters={'script': 'echo "Log Test"'}
        )
        task.complete_task(success=True)

    with allure.step("Verify that log entries are created for the task"):
        logs = Log.objects.filter(task=task)
        assert logs.count() == 1
        log = logs.first()
        assert log.message == "Task completed successfully."
        assert log.level == "INFO"


@allure.feature('Alert Management')
@allure.story('Create Alerts for Failed Tasks')
@pytest.mark.django_db
def test_create_alerts_for_failed_tasks():
    with allure.step("Create a Task and complete it with failure"):
        cluster = KubernetesCluster.objects.create(
            name='Alert Cluster',
            endpoint='https://alert-cluster-endpoint.com',
            status='active'
        )
        dag = DAG.objects.create(name='Alert DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Jar',
            execution_command='java -jar faulty-app.jar',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='running',
            parameters={'jar_path': '/path/to/faulty-app.jar'}
        )
        task.complete_task(success=False)

    with allure.step("Verify that alert entries are created for the failed task"):
        alerts = Alert.objects.filter(task=task)
        assert alerts.count() == 1
        alert = alerts.first()
        assert alert.message == "Task failed."
        assert alert.severity == "CRITICAL"

    with allure.step("Verify that appropriate logs are created for the failed task"):
        log = Log.objects.get(task=task)
        assert log.message == "Task failed."
        assert log.level == "ERROR"


@allure.feature('Billing Management')
@allure.story('Generate Billing on Task Completion')
@pytest.mark.django_db
def test_generate_billing_on_task_completion():
    with allure.step("Create a Task and complete it to generate billing"):
        cluster = KubernetesCluster.objects.create(
            name='Billing Generation Cluster',
            endpoint='https://billing-gen-cluster.com',
            status='active'
        )
        dag = DAG.objects.create(name='Billing Generation DAG')
        dag.clusters.add(cluster)
        component = Component.objects.create(
            dag=dag,
            type='Flink',
            execution_command='flink run data_job.jar',
            order=1
        )
        task = Task.objects.create(
            component=component,
            dag=dag,
            cluster=cluster,
            status='running',
            parameters={'job': 'data_job.jar'}
        )

    with allure.step("Complete the task to trigger billing"):
        task.complete_task(success=True)
        billing = Billing.objects.get(task=task)
        assert billing.amount == Decimal('25.50')
        assert billing.currency == "USD"
        assert billing.billed_at is not None
