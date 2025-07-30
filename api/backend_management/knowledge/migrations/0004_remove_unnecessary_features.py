# Generated manually for removing unnecessary features

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0003_knowledgecategory_knowledgedocument_knowledgecomment_and_more'),
    ]

    operations = [
        # 删除KnowledgeDocument中与其他模型的关联字段
        migrations.RemoveField(
            model_name='knowledgedocument',
            name='category',
        ),
        migrations.RemoveField(
            model_name='knowledgedocument',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='knowledgedocument',
            name='view_count',
        ),
        migrations.RemoveField(
            model_name='knowledgedocument',
            name='attachment',
        ),
        
        # 删除版本模型
        migrations.DeleteModel(
            name='KnowledgeVersion',
        ),
        
        # 删除评论模型
        migrations.DeleteModel(
            name='KnowledgeComment',
        ),
        
        # 删除标签模型
        migrations.DeleteModel(
            name='KnowledgeTag',
        ),
        
        # 删除分类模型
        migrations.DeleteModel(
            name='KnowledgeCategory',
        ),
    ] 