from rest_framework import serializers
from .models import Namespace, Directory, Note

class NamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class DirectorySerializer(serializers.ModelSerializer):
    namespace = serializers.PrimaryKeyRelatedField(queryset=Namespace.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Directory.objects.all(), allow_null=True)
    full_path = serializers.SerializerMethodField()

    class Meta:
        model = Directory
        fields = ['id', 'name', 'namespace', 'parent', 'full_path', 'created_at', 'updated_at']
        read_only_fields = ['id', 'full_path', 'created_at', 'updated_at']

    def get_full_path(self, obj):
        return obj.get_full_path()

    def validate(self, data):
        # 检查同级目录名称唯一性
        if Directory.objects.filter(
            namespace=data['namespace'],
            parent=data.get('parent'),
            name=data['name']
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("同级目录下名称必须唯一")
        return data

class RecursiveDirectorySerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = DirectoryTreeSerializer(value, context=self.context)
        return serializer.data

class DirectoryTreeSerializer(serializers.ModelSerializer):
    children = RecursiveDirectorySerializer(many=True, read_only=True)
    notes = serializers.SerializerMethodField()

    class Meta:
        model = Directory
        fields = ['id', 'name', 'children', 'notes']

    def get_notes(self, obj):
        notes = obj.notes.all()[:20]  # 限制返回数量
        return SimpleNoteSerializer(notes, many=True).data

class SimpleNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'created_at', 'updated_at', 'category']

class NoteSerializer(serializers.ModelSerializer):
    directory = serializers.PrimaryKeyRelatedField(queryset=Directory.objects.all())

    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'directory', 'created_at', 'updated_at', 'category']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # 检查同目录下笔记标题唯一性
        print(data)
        if Note.objects.filter(
            directory=data['directory'],
            title=data['title']
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("同目录下笔记标题必须唯一")
        return data