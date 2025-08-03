import json
import os

from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# 导入LLM和Embedding模型
from core.models.llm import llm
from llm_api.settings.base import info_logger, error_logger
from provider.models.provider import LLMModel
from provider.serializers.provider import (
    # LLM模型序列化器
    LLMModelSerializer, LLMModelCreateSerializer, LLMModelUpdateSerializer,
    LLMModelListResponseSerializer, LLMModelDetailResponseSerializer,
    # 通用响应序列化器
    BaseResponseSerializer, ErrorResponseSerializer
)
from user.permissions import IsAdminUser
from core.agent.coding.embedding import embedding_code_generator


# ===== LLM模型视图集 =====

class LLMModelViewSet(viewsets.ModelViewSet):
    """
    LLM模型视图集
    """
    queryset = LLMModel.objects.all().order_by('-created_at')
    serializer_class = LLMModelSerializer
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        """
        根据不同的action返回对应的序列化器
        """
        if self.action == 'create':
            return LLMModelCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LLMModelUpdateSerializer
        return LLMModelSerializer

    def get_queryset(self):
        """
        获取查询集，支持搜索和排序
        """
        queryset = LLMModel.objects.all()

        # 获取搜索参数
        model_id = self.request.query_params.get('model_id', None)
        provider = self.request.query_params.get('provider', None)
        is_active = self.request.query_params.get('is_active', None)
        ordering = self.request.query_params.get('ordering', '-created_at')

        # 构建搜索条件
        if model_id:
            queryset = queryset.filter(model_id__icontains=model_id)
        if provider:
            queryset = queryset.filter(provider__icontains=provider)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)

        # 排序
        valid_orderings = ['created_at', '-created_at', 'updated_at', '-updated_at', 'model_id', 'provider']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def perform_create(self, serializer):
        """
        创建时设置创建者
        """
        serializer.save(created_by=self.request.user)

    @extend_schema(
        operation_id="llm_model_list",
        summary="获取LLM模型列表",
        description="管理员获取所有LLM模型列表，支持搜索和排序",
        parameters=[
            {
                'name': 'model_id',
                'in': 'query',
                'description': '模型ID（模糊搜索）',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'provider',
                'in': 'query',
                'description': '提供商（模糊搜索）',
                'required': False,
                'schema': {'type': 'string'}
            },
            {
                'name': 'is_active',
                'in': 'query',
                'description': '是否启用',
                'required': False,
                'schema': {'type': 'boolean'}
            },
            {
                'name': 'ordering',
                'in': 'query',
                'description': '排序字段',
                'required': False,
                'schema': {'type': 'string',
                           'enum': ['created_at', '-created_at', 'updated_at', '-updated_at', 'model_id', 'provider']}
            }
        ],
        responses={
            200: LLMModelListResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    def list(self, request, *args, **kwargs):
        """
        获取LLM模型列表
        """
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                'code': 200,
                'message': '获取LLM模型列表成功',
                'data': response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"获取LLM模型列表时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="llm_model_create",
        summary="创建LLM模型",
        description="管理员创建新的LLM模型配置",
        request=LLMModelCreateSerializer,
        responses={
            201: LLMModelDetailResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    def create(self, request, *args, **kwargs):
        """
        创建LLM模型
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                llm_model = serializer.save(created_by=request.user)
                info_logger(f"管理员 {request.user.username} 创建了LLM模型 {llm_model.model_id}")

                response_serializer = LLMModelSerializer(llm_model)
                return Response({
                    'code': 201,
                    'message': '创建LLM模型成功',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'code': 400,
                    'message': '创建LLM模型失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"创建LLM模型时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="llm_model_update",
        summary="更新LLM模型",
        description="管理员更新指定的LLM模型配置",
        request=LLMModelUpdateSerializer,
        responses={
            200: LLMModelDetailResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    def update(self, request, *args, **kwargs):
        """
        更新LLM模型
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                llm_model = serializer.save()
                info_logger(f"管理员 {request.user.username} 更新了LLM模型 {llm_model.model_id}")

                response_serializer = LLMModelSerializer(llm_model)
                return Response({
                    'code': 200,
                    'message': '更新LLM模型成功',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'code': 400,
                    'message': '更新LLM模型失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_logger(f"更新LLM模型时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="llm_model_delete",
        summary="删除LLM模型",
        description="管理员删除指定的LLM模型配置",
        responses={
            200: BaseResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    def destroy(self, request, *args, **kwargs):
        """
        删除LLM模型
        """
        try:
            instance = self.get_object()
            model_id = instance.model_id
            instance.delete()
            info_logger(f"管理员 {request.user.username} 删除了LLM模型 {model_id}")

            return Response({
                'code': 200,
                'message': '删除LLM模型成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_logger(f"删除LLM模型时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="llm_model_test",
        summary="测试LLM模型",
        description="测试指定的LLM模型是否正常工作",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'response': {'type': 'string', 'description': 'LLM响应内容'},
                            'test_time': {'type': 'string', 'description': '测试时间'}
                        }
                    }
                }
            },
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    @action(detail=True, methods=['post'])
    def test_model(self, request, pk=None):
        """
        测试LLM模型
        """
        try:
            instance = self.get_object()
            
            # 检查模型是否启用
            if not instance.is_active:
                return Response({
                    'code': 400,
                    'message': '模型未启用，无法测试'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 检查必要字段
            if not instance.model_id or not instance.provider:
                return Response({
                    'code': 400,
                    'message': '模型ID和提供商不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 调用LLM模型进行测试
            try:
                import os
                from datetime import datetime
                
                # 构建配置
                config = {
                    "configurable": {
                        "global_model": instance.model_id,
                        "global_model_provider": instance.provider,
                        "global_temperature": 0.1,  # 固定写死
                        "global_base_url": instance.api_base,
                        "global_api_key": instance.api_key,
                    }
                }
                
                # 调用LLM模型
                response = llm.invoke("你是谁？", config=config)
                
                info_logger(f"管理员 {request.user.username} 测试LLM模型 {instance.model_id} 成功")
                
                return Response({
                    'code': 200,
                    'message': 'LLM模型测试成功',
                    'data': {
                        'response': response.content,
                        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                error_logger(f"LLM模型调用失败: {str(e)}")
                return Response({
                    'code': 500,
                    'message': f'LLM模型调用失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            error_logger(f"测试LLM模型时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="llm_model_get_providers",
        summary="获取LLM提供商列表",
        description="获取所有可用的LLM提供商选项",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'label': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-LLM模型"]
    )
    @action(detail=False, methods=['get'])
    def get_providers(self, request):
        """
        获取LLM提供商列表
        """
        try:
            from provider.models.provider import LLMModel
            
            providers = [
                {'value': choice[0], 'label': choice[1]} 
                for choice in LLMModel.PROVIDER_CHOICES
            ]
            
            return Response({
                'code': 200,
                'message': '获取提供商列表成功',
                'data': providers
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            error_logger(f"获取提供商列表时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== 全局配置缓存视图集 =====

class GlobalConfigCacheViewSet(viewsets.ViewSet):
    """
    全局配置缓存视图集 - 处理Redis缓存操作
    """
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="global_config_cache_get",
        summary="获取全局配置缓存",
        description="获取LLM和Embedding的全局配置缓存",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'llm_config': {
                                'type': 'object',
                                'properties': {
                                    'temperature': {'type': 'number'},
                                    'max_tokens': {'type': 'integer'},
                                    'base_url': {'type': 'string'},
                                    'api_key': {'type': 'string'},
                                    'model': {'type': 'string'},
                                    'model_provider': {'type': 'string'}
                                }
                            },
                            'embedding_config': {
                                'type': 'object',
                                'properties': {
                                    'base_url': {'type': 'string'},
                                    'token': {'type': 'string'},
                                    'model': {'type': 'string'},
                                    'model_provider': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            },
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['get'])
    def get_configs(self, request):
        """
        获取全局配置缓存
        """
        try:
            # 从Redis获取LLM配置
            llm_config_json = cache.get('code_model')
            llm_config = json.loads(llm_config_json) if llm_config_json else {}

            # 从Redis获取Embedding配置
            embedding_config_json = cache.get('global_embedding')
            embedding_config = json.loads(embedding_config_json) if embedding_config_json else {}

            info_logger("成功获取全局配置缓存")
            return Response({
                'code': 200,
                'message': '获取全局配置成功',
                'data': {
                    'llm_config': llm_config,
                    'embedding_config': embedding_config
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"获取全局配置缓存时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_update_llm",
        summary="更新LLM全局配置缓存",
        description="更新LLM的全局配置缓存",
        request={
            'type': 'object',
            'properties': {
                'temperature': {'type': 'number', 'description': '温度参数'},
                'max_tokens': {'type': 'integer', 'description': '最大token数'},
                'base_url': {'type': 'string', 'description': 'API基础URL'},
                'api_key': {'type': 'string', 'description': 'API密钥'},
                'model': {'type': 'string', 'description': '模型名称'},
                'model_provider': {'type': 'string', 'description': '模型提供商'}
            },
            'required': ['model', 'model_provider']
        },
        responses={
            200: BaseResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def update_llm_config(self, request):
        """
        更新LLM全局配置缓存
        """
        try:
            llm_config = request.data

            # 验证必需字段
            if not llm_config.get('model') or not llm_config.get('model_provider'):
                return Response({
                    'code': 400,
                    'message': '模型名称和提供商不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 设置默认值
            default_config = {
                'global_temperature': 0.1,
                'global_max_tokens': 1024,
                'global_base_url': os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', ''),
                'global_api_key': os.getenv('CHAT_MODEL_DEFAULT_API_KEY', ''),
                'global_model': llm_config.get('model'),
                'global_model_provider': llm_config.get('model_provider'),
            }

            # 更新配置
            default_config.update({
                'global_temperature': llm_config.get('temperature', 0.1),
                'global_max_tokens': llm_config.get('max_tokens', 1024),
                'global_base_url': llm_config.get('base_url', os.getenv('CHAT_MODEL_DEFAULT_BASE_URL', '')),
                'global_api_key': llm_config.get('api_key', os.getenv('CHAT_MODEL_DEFAULT_API_KEY', '')),
            })

            # 存储到Redis缓存，永不过期
            cache.set('code_model', json.dumps(default_config), timeout=None)

            info_logger(f"LLM全局配置更新成功: {default_config['global_model']}")
            return Response({
                'code': 200,
                'message': 'LLM全局配置更新成功'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"更新LLM全局配置缓存时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_test_llm",
        summary="测试LLM全局配置",
        description="测试LLM全局配置是否正常工作",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'response': {'type': 'string', 'description': 'LLM响应内容'}
                        }
                    }
                }
            },
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def test_llm_config(self, request):
        """
        测试LLM全局配置
        """
        try:
            # 从Redis获取LLM配置
            llm_config_json = cache.get('code_model')
            if not llm_config_json:
                return Response({
                    'code': 400,
                    'message': 'LLM全局配置不存在，请先配置LLM'
                }, status=status.HTTP_400_BAD_REQUEST)

            llm_config = json.loads(llm_config_json)

            # 调用LLM模型
            try:
                response = llm.invoke(
                    "你好",
                    config={
                        "configurable": llm_config
                    }
                )

                info_logger("LLM全局配置测试成功")
                return Response({
                    'code': 200,
                    'message': 'LLM全局配置测试成功',
                    'data': {
                        'response': response.content
                    }
                }, status=status.HTTP_200_OK)

            except Exception as e:
                error_logger(f"LLM调用失败: {str(e)}")
                return Response({
                    'code': 500,
                    'message': f'LLM调用失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            error_logger(f"测试LLM全局配置时发生错误: {str(e)}")
            return Response({
                'code': 500,
                'message': '服务器内部错误',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_test_embedding",
        summary="测试Embedding全局配置",
        description="测试Embedding全局配置是否正常工作",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'embedding': {
                                'type': 'array',
                                'items': {'type': 'number'},
                                'description': 'Embedding向量'
                            }
                        }
                    }
                }
            },
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def test_embedding_config(self, request):
        """
        测试Embedding全局配置
        """
        try:
            # 检查是否有Embedding配置
            embedding_config = cache.get('global_embedding_config')
            if not embedding_config:
                return Response({
                    'code': 400,
                    'message': 'Embedding配置不存在，请先配置Embedding模型'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 检查是否有生成的代码
            embedding_code = cache.get('global_embedding')
            if not embedding_code:
                return Response({
                    'code': 400,
                    'message': 'Embedding代码不存在，请先生成Embedding代码'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 测试Embedding模型
            from core.models.embedding import embedding
            test_text = "这是一个测试文本"
            embedding_result = embedding.embed_query(test_text)

            return Response({
                'code': 200,
                'message': 'Embedding配置测试成功',
                'data': {
                    'embedding': embedding_result
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"测试Embedding配置失败: {str(e)}")
            return Response({
                'code': 500,
                'message': f'测试Embedding配置失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_generate_embedding_code",
        summary="生成Embedding代码",
        description="根据用户需求生成Embedding模型接入代码",
        request={
            'type': 'object',
            'properties': {
                'user_demand': {
                    'type': 'string',
                    'description': '用户需求描述，包含接口信息、请求头、请求体等'
                }
            },
            'required': ['user_demand']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'is_success': {'type': 'boolean', 'description': '代码生成是否成功'},
                            'generated_code': {'type': 'string', 'description': '生成的代码'},
                            'test_code': {'type': 'string', 'description': '测试代码'}
                        }
                    }
                }
            },
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def generate_embedding_code(self, request):
        """
        生成Embedding代码
        """
        try:
            user_demand = request.data.get('user_demand')
            if not user_demand:
                return Response({
                    'code': 400,
                    'message': '用户需求不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 使用embedding_code_generator生成代码
            is_success, generated_code = embedding_code_generator.generation(
                user_demand,
                redis_key="global_embedding"
            )

            return Response({
                'code': 200,
                'message': 'Embedding代码生成成功' if is_success else 'Embedding代码生成失败，请检查需求描述',
                'data': {
                    'is_success': is_success,
                    'generated_code': generated_code
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"生成Embedding代码失败: {str(e)}")
            return Response({
                'code': 500,
                'message': f'生成Embedding代码失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_test_generated_embedding",
        summary="测试生成的Embedding代码",
        description="测试生成的Embedding代码是否正常工作",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'test_result': {'type': 'string', 'description': '测试结果'},
                            'embedding': {
                                'type': 'array',
                                'items': {'type': 'number'},
                                'description': 'Embedding向量'
                            }
                        }
                    }
                }
            },
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def test_generated_embedding(self, request):
        """
        测试生成的Embedding代码
        """
        try:
            # 检查是否有生成的代码
            embedding_code = cache.get('global_embedding')
            if not embedding_code:
                return Response({
                    'code': 400,
                    'message': 'Embedding代码不存在，请先生成Embedding代码'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 测试生成的Embedding代码
            from core.models.embedding import embedding
            test_texts = ["Deep Learning is not...", "Deep learning is..."]

            # 测试embed_documents
            texts_response = embedding.embed_documents(test_texts)

            # 测试embed_query
            text_response = embedding.embed_query("What is Deep Learning?")

            return Response({
                'code': 200,
                'message': '生成的Embedding代码测试成功',
                'data': {
                    'test_result': '测试通过',
                    'embedding': text_response,
                    'documents_embedding': texts_response
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"测试生成的Embedding代码失败: {str(e)}")
            return Response({
                'code': 500,
                'message': f'测试生成的Embedding代码失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        operation_id="global_config_cache_save_edited_embedding_code",
        summary="保存编辑的Embedding代码",
        description="保存用户编辑后的Embedding代码",
        request={
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': '全量代码'
                }
            },
            'required': ['code']
        },
        responses={
            200: BaseResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=["Provider管理-全局配置缓存"]
    )
    @action(detail=False, methods=['post'])
    def save_edited_embedding_code(self, request):
        """
        保存编辑的Embedding代码
        """
        try:
            code = request.data.get('code')
            embedding_code_generator.parse_generation_code(code, redis_key="global_embedding")
            info_logger("保存编辑的Embedding代码成功")
            return Response({
                'code': 200,
                'message': '编辑的Embedding代码保存成功'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            error_logger(f"保存编辑的Embedding代码失败: {str(e)}")
            return Response({
                'code': 500,
                'message': f'保存编辑的Embedding代码失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
