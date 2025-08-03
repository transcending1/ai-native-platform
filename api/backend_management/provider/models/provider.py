from django.db import models
from django.conf import settings
from user.models.user import CustomUser


class LLMModel(models.Model):
    """
    LLM（大语言模型）配置
    """
    # 提供商选项
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('azure_openai', 'Azure OpenAI'),
        ('azure_ai', 'Azure AI'),
        ('google_vertexai', 'Google Vertex AI'),
        ('google_genai', 'Google GenAI'),
        ('bedrock', 'AWS Bedrock'),
        ('bedrock_converse', 'AWS Bedrock Converse'),
        ('cohere', 'Cohere'),
        ('fireworks', 'Fireworks'),
        ('together', 'Together'),
        ('mistralai', 'Mistral AI'),
        ('huggingface', 'Hugging Face'),
        ('groq', 'Groq'),
        ('ollama', 'Ollama'),
        ('google_anthropic_vertex', 'Google Anthropic Vertex'),
        ('deepseek', 'DeepSeek'),
        ('ibm', 'IBM'),
        ('nvidia', 'NVIDIA'),
        ('xai', 'xAI'),
        ('perplexity', 'Perplexity'),
    ]
    
    model_id = models.CharField(max_length=100, verbose_name="模型ID", unique=True)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, verbose_name="提供商")
    api_key = models.CharField(max_length=255, blank=True, verbose_name="API密钥")
    api_base = models.URLField(blank=True, verbose_name="API基础URL")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='llm_models_created',
        verbose_name="创建者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "LLM模型"
        verbose_name_plural = "LLM模型"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider} - {self.model_id}"
    
    def save(self, *args, **kwargs):
        """
        重写save方法，在保存时更新缓存
        """
        # 先保存到数据库
        super().save(*args, **kwargs)
        # 更新缓存
        self.update_cache()
    
    def delete(self, *args, **kwargs):
        """
        重写delete方法，在删除时清除缓存
        """
        # 先清除缓存
        self.clear_cache()
        # 再删除数据库记录
        super().delete(*args, **kwargs)
    
    def update_cache(self):
        """
        更新模型缓存
        """
        from django.core.cache import cache
        import json
        
        cache_key = f"model_{self.model_id}"
        cache_data = {
            'model_id': self.model_id,
            'provider': self.provider,
            'api_key': self.api_key,
            'api_base': self.api_base,
            'is_active': self.is_active
        }
        
        # 设置缓存，永不过期
        cache.set(cache_key, json.dumps(cache_data), timeout=None)
    
    def clear_cache(self):
        """
        清除模型缓存
        """
        from django.core.cache import cache
        
        cache_key = f"model_{self.model_id}"
        cache.delete(cache_key)
    
    @classmethod
    def get_model_config(cls, model_id):
        """
        根据模型ID获取模型配置（优先从缓存获取）
        """
        from django.core.cache import cache
        import json
        
        cache_key = f"model_{model_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # 如果缓存中没有，从数据库获取并更新缓存
        try:
            model = cls.objects.get(model_id=model_id, is_active=True)
            model.update_cache()
            return {
                'model_id': model.model_id,
                'provider': model.provider,
                'api_key': model.api_key,
                'api_base': model.api_base,
                'is_active': model.is_active
            }
        except cls.DoesNotExist:
            return None 