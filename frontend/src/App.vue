<script setup lang="ts">
import { ref } from 'vue'
import SidebarNav from './components/SidebarNav.vue'
import { Notifications } from '@kyvg/vue3-notification';
</script>

<template>
  <v-card>
    <v-layout>
      <SidebarNav></SidebarNav>
      <v-main>
        <RouterView />
      </v-main>
    </v-layout>
  </v-card>
  <Notifications />
</template> 
