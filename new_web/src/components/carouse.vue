<template>
  <div class="w-full max-w-4xl mx-auto">
    <el-carousel :interval="1000" arrow="always" class="rounded-lg">
      <el-carousel-item v-for="(item, index) in carouselItems" :key="index">
        <img :src="item.src" :alt="item.alt" class="w-full h-64 object-cover"/>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const carouselItems = ref([
  { src: 'https://via.placeholder.com/800x400?text=Slide+1', alt: 'Slide 1' },
  { src: 'https://via.placeholder.com/800x400?text=Slide+2', alt: 'Slide 2' },
  { src: 'https://via.placeholder.com/800x400?text=Slide+3', alt: 'Slide 3' },
])
</script>