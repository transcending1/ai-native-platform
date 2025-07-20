from django.contrib import admin
from user.models.big_data import KubernetesCluster, Component


@admin.register(KubernetesCluster)
class KubernetesClusterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'endpoint', 'status')
    search_fields = ('name', 'status')
    list_filter = ('status',)
    ordering = ('name',)
    readonly_fields = ('id',)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('id', 'dag', 'type', 'order')
    search_fields = ('type', 'dag__name')
    list_filter = ('type',)
    ordering = ('order',)
    readonly_fields = ('id',)
