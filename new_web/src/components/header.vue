<template>
    <header class="bg-white shadow p-4 flex items-center justify-between">
      <!-- Brand Icon -->
      <div class="flex items-center space-x-2">
        <img src="../assets/logo.svg" alt="Brand Icon" class="w-8 h-8">
      </div>
  
      <!-- Navigation Menu -->
      <nav class="flex items-center space-x-6">
        <span class="hover:underline cursor-pointer">免费课</span>
        <span class="hover:underline cursor-pointer">实战课</span>
        <span class="hover:underline cursor-pointer">体系课</span>
  
        <!-- Drop-down Menus -->
        <el-dropdown>
          <span class="cursor-pointer hover:underline">发现</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>教程</el-dropdown-item>
              <el-dropdown-item>专栏</el-dropdown-item>
              <el-dropdown-item>手记</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
  
        <el-dropdown>
          <span class="cursor-pointer hover:underline">商业合作</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item>企业服务</el-dropdown-item>
              <el-dropdown-item>讲师入驻</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>
  
      <!-- Search Box -->
      <div class="flex items-center space-x-2">
        <input
          type="text"
          placeholder="请输入关键字"
          class="border border-gray-300 rounded p-2"
        />
        <button class="bg-blue-500 text-white rounded px-4 py-2">搜索</button>
      </div>
  
      <!-- Auth Buttons -->
      <div class="flex items-center space-x-4">
        <button class="bg-gray-100 text-gray-800 rounded px-4 py-2">登录</button>
        <button class="bg-blue-500 text-white rounded px-4 py-2">注册</button>
      </div>
    </header>
  </template>
  
  <script setup>
  import { ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus';
  </script>
  
  <style scoped>
  /* No additional styles needed, using Tailwind CSS for styling */
  </style>