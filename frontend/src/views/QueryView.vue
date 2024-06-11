<template>
  <v-container fluid class="rounded-0">
    <v-app-bar>
      <v-app-bar-title>Jobs</v-app-bar-title>
    </v-app-bar>
    <v-row class="my-3">
      <v-col>
        <CypherCodeMirror v-model="content" class="border-sm" />
      </v-col>
      <v-col-1 class="d-flex align-center">
        <v-btn color="blue">Execute Query</v-btn>
      </v-col-1>
    </v-row>
    <hr>
    <v-sheet class="mt-3">
      {{content}}
    </v-sheet>

  </v-container>
</template>

<script setup lang="ts">
import CypherCodeMirror from '../components/CypherCodeMirror.vue';
import { ref, shallowRef, onMounted, onUnmounted, watch, watchEffect } from 'vue'

const content = ref();
</script>