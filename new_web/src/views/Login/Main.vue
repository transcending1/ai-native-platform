<template>
  <div class="container mx-auto p-4">
    <SearchBar />
    <ApplicationTable class="mt-4" />
  </div>
</template>

<script setup>
import SearchBar from './components/SearchBar.vue'
import ApplicationTable from './components/ApplicationTable.vue'
</script>