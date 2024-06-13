<template>
  <v-container fluid class="rounded-0">
    <v-app-bar>
      <v-app-bar-title>Query Graph Database</v-app-bar-title>

      <v-btn href="http://127.0.0.1:7474/">Open Neo4j Browser</v-btn>
      <v-btn v-if="result" variant="outlined" prepend-icon="mdi-download" @click="saveToFile">Download Data</v-btn>
    </v-app-bar>
    <!-- Query Bar -->
    <v-row class="my-2">
      <v-col cols="10">
        <CypherCodeMirror v-model="query" class="border-sm" />
      </v-col>

      <v-col class="d-flex align-center">

        <v-btn color="blue" @click="executeQuery">Execute Query
          <v-tooltip activator="parent" location="bottom">Execute query (Ctrl + Q)</v-tooltip>
        </v-btn>
        <v-btn density="compact" variant="plain" icon="mdi-information-outline" class="ms-2"></v-btn>
      </v-col>
    </v-row>



    <!-- Query Error Alert -->
    <v-alert v-if="error" type="error">{{ error }}</v-alert>
    <hr class="my-2">

    <!-- Query Results -->
    <v-data-table v-if="result !== null" :items="result" :headers="tableHeaders" :loading="loading">
      <template v-slot:item.actions="{ item }">
        <v-btn color="primary" size="small" class="mx-2" @click="showDialog(item)">View</v-btn>
      </template>
    </v-data-table>

  </v-container>
  <query-data-dialog v-model:data="dialogData" v-model:visibility="dialog"></query-data-dialog>

</template>

<script setup lang="ts">
import CypherCodeMirror from '../components/CypherCodeMirror.vue';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useNeo4j } from '@/composables/useNeo4j';
import { table } from 'console';
import QueryDataDialog from './QueryDataDialog.vue'
import { useSaveData } from '@/composables/useSaveData';

const query = ref();
const dialog = ref(false);
const dialogData = ref<string>()

const { initialize, close, runQuery, error, loading, result, headers, notifications } = useNeo4j('neo4j://localhost:7687', 'neo4j', 'neo4j123');
// const { query, data } = useNeo4j();
const tableHeaders = computed(() => {
  let result = headers.value?.map((h) => ({ title: h, key: h }));
  result?.push({ title: "", key: 'actions' })
  return result
})

async function executeQuery() {
  await runQuery(query.value)
}

import { useMagicKeys } from '@vueuse/core'

const keys = useMagicKeys()
const ctrlQ = keys['Ctrl+Q']

watch(ctrlQ, (v) => {
  if (v) {
    executeQuery()
  }
})

onMounted(() => {
  initialize();
});

onBeforeUnmount(() => {
  close();
});

const jsonifiedData = computed(() => {
  return JSON.stringify(result.value, null, 2)
})
const { saveToFile, filename } = useSaveData(jsonifiedData, "query-data.json")

function showDialog(item) {
  dialogData.value = item
  dialog.value = true
}

</script>