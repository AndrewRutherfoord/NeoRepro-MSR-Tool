<template>
  <vue-splitter initial-percent="20" style="height: 100%">
    <template #left-pane>
      <file-tree-sidebar title="Saved Queries" subtitle="Click on one to open it and then execute it."
        @link-clicked="sidebarFileSelected" @delete-file="deleteQuery" :data="files"
        :is-loading="filesIsLoading"></file-tree-sidebar>
    </template>
    <template #right-pane>

      <v-container fluid class="rounded-0">
        <v-app-bar>
          <v-app-bar-title>Query Graph Database</v-app-bar-title>

          <v-btn href="http://127.0.0.1:7474/">Open Neo4j Browser</v-btn>
          <v-btn v-if="result" variant="outlined" prepend-icon="mdi-download" @click="saveToFile">Download Data</v-btn>
        </v-app-bar>
        <!-- Query Bar -->
        <v-row class="my-2">
          <v-col cols="10">
            <cypher-code-mirror ref="editor" class="border-sm" />
          </v-col>

          <v-col class="d-flex align-center">

            <v-btn color="blue" @click="executeQuery">Execute Query
              <v-tooltip activator="parent" location="bottom">Execute query (Ctrl + Q)</v-tooltip>
            </v-btn>
            <v-btn density="compact" variant="plain" icon="mdi-content-save" class="ms-2" @click="saveQuery"></v-btn>
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
  </vue-splitter>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import axios from 'axios';

import { useNeo4j } from '@/composables/useNeo4j';
import { useSaveData } from '@/composables/useSaveData';
import { useAxios } from '@vueuse/integrations/useAxios'

import VueSplitter from '@rmp135/vue-splitter'
import FileTreeSidebar from '../components/FileTreeSidebar.vue'
import CypherCodeMirror from '../components/CypherCodeMirror.vue';
import QueryDataDialog from '../components/QueryDataDialog.vue'

const dialog = ref(false);
const dialogData = ref<string>()

const toast = useToast();

// ----- Executing Queries -----

const editor = ref()

const { initialize, close, runQuery, error, loading, result, headers, notifications } = useNeo4j('neo4j://localhost:7687', 'neo4j', 'neo4j123');

const tableHeaders = computed(() => {
  let result = headers.value?.map((h) => ({ title: h, key: h }));
  result?.push({ title: "", key: 'actions' })
  return result
})

onMounted(() => {
  initialize();
});

onBeforeUnmount(() => {
  close();
});

async function executeQuery() {
  let query = editor.value.getQuery()
  console.log(query)
  await runQuery(query)
}

// ----- Key Binds -----

import { useMagicKeys } from '@vueuse/core'
import { useToast } from '@/composables/useToast';

const keys = useMagicKeys()
const ctrlQ = keys['Ctrl+Q']

watch(ctrlQ, (v) => {
  if (v) {
    executeQuery()
  }
})

// ----- Download Data -----

const jsonifiedData = computed(() => {
  return JSON.stringify(result.value, null, 2)
})
const { saveToFile, filename } = useSaveData(jsonifiedData, "query-data.json")

function showDialog(item) {
  dialogData.value = item
  dialog.value = true
}

// ----- Saved Queries -----

const { data: files, isLoading: filesIsLoading, execute: getQueryFiles } = useAxios('/queries/', axios)

const { execute } = useAxios(axios)

async function sidebarFileSelected(name: string) {
  try {
    let response = await execute(`/queries/${name}`)
    // query.value = fileData.value
    editor.value.setValue(response.data.value)
  } catch (e) {
    toast.error("Failed to load query files.")
  }
}

async function saveQuery() {
  let filename = prompt("What do you want to name the query file?")
  console.log(filename)
  if (!filename?.endsWith('.cql')) {
    filename = filename + '.cql'
  }
  await execute(`queries/save/${filename}`, {
    method: "POST",
    data: { content: editor.value.getQuery() }
  })
  toast.success("Query Saved.")
  await getQueryFiles()

}

async function deleteQuery(path: string) {
  let ok = await confirm("Are you sure you want to delete this saved query?")
  try {
    if (ok) {
      await execute(`/queries/${path}`, { method: 'DELETE' })
      toast.success("Query deleted.")
      await getQueryFiles()
    } else {
      toast.warn("Deletion cancelled.")
    }
  } catch (e) {
    console.error(e)
    toast.error("Failed to delete query.")
  }
}

</script>