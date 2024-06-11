<script setup lang="ts">
import { ref } from 'vue'
import SidebarNav from './components/SidebarNav.vue'
import Toast from 'primevue/toast';

const sidebar = ref(
  {
    collapsed: true,
    width: '0px'
  }
)
</script>

<template>
  <div class="d-flex justify-content-start">
    <SidebarNav v-model:collapsed="sidebar.collapsed" v-model:sidebarWidth="sidebar.width"
      :style="{ 'flex-grow': '1', 'flex-basis': sidebar.width }"></SidebarNav>
    <main class="d-flex flex-column vh-100"
      :style="{ 'flex-shrink': '1', 'flex-basis': `calc(100% - ${sidebar.width})` }">
      <RouterView :key="sidebar.width" /> <!-- Force re-render on width change. -->
    </main>
    <Toast position="bottom-right" />
  </div>
</template>
