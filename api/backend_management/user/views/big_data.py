from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from user.models.big_data import (
    KubernetesCluster,
    DAG,
    Component,
    Task,
    Log,
    Alert,
    Billing
)
from user.serializers.big_data import (
    KubernetesClusterSerializer,
    DAGSerializer,
    ComponentSerializer,
    TaskSerializer,
    LogSerializer,
    AlertSerializer,
    BillingSerializer
)

class KubernetesClusterViewSet(viewsets.ModelViewSet):
    queryset = KubernetesCluster.objects.all()
    serializer_class = KubernetesClusterSerializer
    filterset_fields = ['name', 'status']

    @action(detail=True, methods=['post'])
    def manage_cluster(self, request, pk=None):
        cluster = self.get_object()
        cluster.manage_cluster()
        return Response({'status': 'Cluster managed successfully'}, status=status.HTTP_200_OK)


class DAGViewSet(viewsets.ModelViewSet):
    queryset = DAG.objects.all()
    serializer_class = DAGSerializer
    filterset_fields = ['name', 'created_at', 'updated_at']

    @action(detail=True, methods=['post'])
    def schedule_dag(self, request, pk=None):
        dag = self.get_object()
        components_data = request.data.get('components_data', [])
        components = dag.schedule_dag(components_data)
        serializer = ComponentSerializer(components, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ComponentViewSet(viewsets.ModelViewSet):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['type', 'order', 'dag']

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        component = self.get_object()
        dag_id = request.data.get('dag_id')
        cluster_id = request.data.get('cluster_id')
        parameters = request.data.get('parameters', {})
        task = component.execute(dag_id, cluster_id, parameters)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_fields = ['status', 'dag', 'cluster', 'component']

    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()
        success = request.data.get('success', True)
        task.complete_task(success=success)
        return Response({'status': 'Task completed successfully' if success else 'Task failed'}, status=status.HTTP_200_OK)


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    filterset_fields = ['level', 'task', 'timestamp']


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    filterset_fields = ['severity', 'task', 'timestamp']


class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer
    filterset_fields = ['currency', 'task', 'billed_at']