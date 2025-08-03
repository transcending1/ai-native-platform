from rest_framework import serializers
from provider.models.provider import LLMModel


# ===== LLM模型序列化器 =====

class LLMModelSerializer(serializers.ModelSerializer):
    """
    LLM模型序列化器
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = LLMModel
        fields = [
            'id', 'provider', 'model_id', 'api_key', 'api_base', 
            'is_active', 'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True}  # API密钥不返回给前端
        }


class LLMModelCreateSerializer(serializers.ModelSerializer):
    """
    创建LLM模型序列化器
    """
    class Meta:
        model = LLMModel
        fields = ['provider', 'model_id', 'api_key', 'api_base', 'is_active']


class LLMModelUpdateSerializer(serializers.ModelSerializer):
    """
    更新LLM模型序列化器
    """
    class Meta:
        model = LLMModel
        fields = ['provider', 'model_id', 'api_key', 'api_base', 'is_active']


# ===== 响应序列化器 =====

class BaseResponseSerializer(serializers.Serializer):
    """
    基础响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")


class ErrorResponseSerializer(serializers.Serializer):
    """
    错误响应序列化器
    """
    code = serializers.IntegerField(help_text="错误状态码")
    message = serializers.CharField(help_text="错误消息")
    errors = serializers.DictField(required=False, help_text="详细错误信息")


class LLMModelListResponseSerializer(serializers.Serializer):
    """
    LLM模型列表响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = serializers.DictField(help_text="LLM模型列表数据")


class LLMModelDetailResponseSerializer(serializers.Serializer):
    """
    LLM模型详情响应序列化器
    """
    code = serializers.IntegerField(help_text="响应状态码")
    message = serializers.CharField(help_text="响应消息")
    data = LLMModelSerializer(help_text="LLM模型详情数据") 