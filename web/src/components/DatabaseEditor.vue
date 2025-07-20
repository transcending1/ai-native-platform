<template>
  <div class="database-editor">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <h2>{{ note ? '编辑数据表' : '新建数据表' }}</h2>
        </div>
      </template>

      <el-form
          ref="noteForm"
          :model="formData"
          :rules="formRules"
          label-position="top"
          class="note-form"
      >
        <div class="form-section">
          <h3>数据表信息</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数据表名称" prop="tableName">
                <el-input v-model="formData.tableName" placeholder="reading_notes" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="数据表描述">
                <el-input v-model="formData.tableDescription" placeholder="for saving reading notes" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="Table查询模式" prop="queryMode">
            <el-radio-group v-model="formData.queryMode">
              <el-radio label="single">单用户模式</el-radio>
              <el-radio label="multi">多用户模式</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>

        <div class="form-section">
          <div class="section-header">
            <h3>存储字段</h3>
            <el-button
                type="primary"
                :icon="Plus"
                @click="addField"
                class="add-field-btn"
            >
              新增字段
            </el-button>
          </div>

          <el-table :data="formData.fields" border class="field-table">
            <el-table-column label="字段名称" width="180">
              <template #default="{ $index }">
                <el-form-item
                    :prop="`fields.${$index}.name`"
                    :rules="fieldRules.name"
                >
                  <el-input v-model="formData.fields[$index].name" placeholder="字段名" />
                </el-form-item>
              </template>
            </el-table-column>

            <el-table-column label="描述">
              <template #default="{ $index }">
                <el-form-item :prop="`fields.${$index}.description`">
                  <el-input v-model="formData.fields[$index].description" placeholder="字段描述" />
                </el-form-item>
              </template>
            </el-table-column>

            <el-table-column label="数据类型" width="150">
              <template #default="{ $index }">
                <el-form-item
                    :prop="`fields.${$index}.dataType`"
                    :rules="fieldRules.dataType"
                >
                  <el-select v-model="formData.fields[$index].dataType" placeholder="选择类型">
                    <el-option label="整数" value="Integer" />
                    <el-option label="字符串" value="String" />
                    <el-option label="时间" value="Time" />
                    <el-option label="布尔值" value="Boolean" />
                    <el-option label="浮点数" value="Float" />
                  </el-select>
                </el-form-item>
              </template>
            </el-table-column>

            <el-table-column label="是否必需" width="100">
              <template #default="{ $index }">
                <el-form-item>
                  <el-checkbox v-model="formData.fields[$index].required" />
                </el-form-item>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button
                    type="danger"
                    :icon="Delete"
                    size="small"
                    @click="removeField($index)"
                >

                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="form-actions">
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="primary" @click="handleSave">{{ note ? '保存' : '创建数据表' }}</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus';

interface FieldItem {
  name: string;
  description: string;
  dataType: string;
  required: boolean;
}

interface FormData {
  tableName: string;
  tableDescription: string;
  queryMode: string;
  fields: FieldItem[];
  aiDescription: string;
}

interface Note {
  id: number;
  title: string;
  content: string;
  type?: string;
  directory?: number;
}

const props = defineProps<{
  note?: Note | null;
}>();

const emit = defineEmits<{
  save: [noteData: { id: number; title: string; content: string }];
  cancel: [];
}>();

const noteForm = ref<FormInstance>();
const formData = reactive<FormData>({
  tableName: 'reading_notes',
  tableDescription: 'for saving reading notes',
  queryMode: 'single',
  aiDescription: '',
  fields: [
    { name: 'id', description: '数据的唯一标识（主键）', dataType: 'Integer', required: true },
    { name: 'sys_platform', description: '数据库生成使用的渠道', dataType: 'String', required: true },
    { name: 'uuid', description: '用户唯一标识，由系统生成', dataType: 'String', required: true },
    { name: 'bstudio_create_time', description: '数据插入的时间', dataType: 'Time', required: true },
    { name: 'name', description: '笔记名称', dataType: 'String', required: true },
    { name: 'section', description: '章节', dataType: 'Integer', required: true },
    { name: 'note', description: '笔记内容', dataType: 'String', required: true }
  ]
});

const formRules = reactive<FormRules<FormData>>({
  tableName: [
    { required: true, message: '请输入数据表名称', trigger: 'blur' }
  ],
  queryMode: [
    { required: true, message: '请选择查询模式', trigger: 'change' }
  ]
});

const fieldRules = {
  name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' }
  ],
  dataType: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ]
};

// 获取默认字段
const getDefaultFields = () => [
  { name: 'id', description: '数据的唯一标识（主键）', dataType: 'Integer', required: true },
  { name: 'sys_platform', description: '数据库生成使用的渠道', dataType: 'String', required: true },
  { name: 'uuid', description: '用户唯一标识，由系统生成', dataType: 'String', required: true },
  { name: 'bstudio_create_time', description: '数据插入的时间', dataType: 'Time', required: true },
  { name: 'name', description: '笔记名称', dataType: 'String', required: true },
  { name: 'section', description: '章节', dataType: 'Integer', required: true },
  { name: 'note', description: '笔记内容', dataType: 'String', required: true }
];

// 重置为默认值
const resetToDefault = () => {
  formData.tableName = 'reading_notes';
  formData.tableDescription = 'for saving reading notes';
  formData.queryMode = 'single';
  formData.fields = getDefaultFields();
};

// 监听 note 变化，加载数据
watch(() => props.note, (newNote) => {
  if (newNote) {
    try {
      loadNoteData(newNote);
    } catch (error) {
      console.error('DatabaseEditor: 加载笔记数据时出错:', error);
      resetToDefault();
    }
  }
}, { immediate: true });

// 加载笔记数据
const loadNoteData = (note: Note) => {
  try {
    if (note.content) {
      const data = JSON.parse(note.content);
      formData.tableName = data.tableName || 'reading_notes';
      formData.tableDescription = data.tableDescription || 'for saving reading notes';
      formData.queryMode = data.queryMode || 'single';
      formData.fields = data.fields || getDefaultFields();
    } else {
      resetToDefault();
    }
  } catch (error) {
    console.error('DatabaseEditor: 解析笔记内容失败:', error);
    resetToDefault();
  }
};

const addField = () => {
  formData.fields.push({
    name: '',
    description: '',
    dataType: 'String',
    required: true
  });
};

const removeField = (index: number) => {
  formData.fields.splice(index, 1);
};

const handleSave = async () => {
  if (!noteForm.value) return;

  try {
    await noteForm.value.validate();
    
    const noteData = {
      id: props.note?.id || 0,
      title: formData.tableName,
      content: JSON.stringify(formData)
    };
    
    emit('save', noteData);
    ElMessage.success(props.note ? '数据表保存成功' : '数据表创建成功');
  } catch (error) {
    ElMessage.error('请填写必填字段');
  }
};

const handleCancel = () => {
  emit('cancel');
};

const resetForm = () => {
  if (noteForm.value) {
    noteForm.value.resetFields();
    resetToDefault();
  }
};
</script>

<style scoped>
.database-editor {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.form-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-section {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f9fafc;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.field-table {
  width: 100%;
  margin-top: 10px;
}

.field-table :deep(.el-form-item) {
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 12px;
}

.add-field-btn {
  margin-bottom: 10px;
}

h2 {
  color: #303133;
  margin: 0;
}

h3 {
  color: #606266;
  margin-top: 0;
}
</style>