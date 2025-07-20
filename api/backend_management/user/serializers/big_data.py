from rest_framework import serializers
from user.models.big_data import (
    KubernetesCluster,
    DAG,
    Component,
    Task,
    Log,
    Alert,
    Billing
)

class KubernetesClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubernetesCluster
        fields = '__all__'

class DAGSerializer(serializers.ModelSerializer):
    class Meta:
        model = DAG
        fields = '__all__'

class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Component
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class BillingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Billing
        fields = '__all__'