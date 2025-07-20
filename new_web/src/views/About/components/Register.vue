<template>
    <el-form
      :model="form"
      :rules="rules"
      ref="formRef"
      class="max-w-md mx-auto p-6 bg-white shadow-md rounded-md"
      @submit.prevent="onSubmit"
    >
      <el-form-item label="手机号" prop="phone">
        <el-input
          v-model="form.phone"
          placeholder="请输入手机号"
          class="w-full"
        />
      </el-form-item>
  
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入密码"
          class="w-full"
        />
      </el-form-item>
  
      <div class="flex justify-end">
        <el-button type="primary" native-type="submit">
          注册
        </el-button>
      </div>
    </el-form>
  </template>
  
  <script setup>
  import { reactive, ref } from 'vue';
  import { ElForm, ElFormItem, ElInput, ElButton, ElMessage } from 'element-plus';
  
  const formRef = ref(null);
  
  const form = reactive({
    phone: '',
    password: '',
  });
  
  const rules = {
    phone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      {
        pattern: /^1[3-9]\d{9}$/,
        message: '手机号格式不正确',
        trigger: 'blur',
      },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      {
        min: 6,
        message: '密码长度不能少于6位',
        trigger: 'blur',
      },
    ],
  };
  
  const onSubmit = () => {
    formRef.value.validate((valid) => {
      if (valid) {
        // 处理注册逻辑
        ElMessage.success('注册成功！');
        // 重置表单
        formRef.value.resetFields();
      } else {
        ElMessage.error('请正确填写表单内容');
        return false;
      }
    });
  };
  </script>