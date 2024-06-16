<template>
  <vue-splitter initial-percent="20" style="height: 100%">
    <template #left-pane>
      <file-tree-sidebar title="Saved Configs" subtitle="Click on one to open it and then execute it."
        @link-clicked="sidebarFileSelected" @delete-file="deleteConfiguration" @create-file="openNewFile" :data="files"
        :is-loading="filesIsLoading"></file-tree-sidebar>
    </template>
    <template #right-pane>
      <div class="d-flex justify-space-between">
        <v-breadcrumbs class="py-2" :items="currentFile ? currentFile.split('/') : ['new-file.json']"></v-breadcrumbs>
        <v-btn class="mt-1 me-" size="compact" variant="text" @click="saveConfiguration" icon="mdi-content-save"
          :disabled="!unsavedChanges"></v-btn>
      </div>
      <hr>
      <!-- {{ currentFile }} -->
      <v-sheet height="100vh">
        <v-app-bar>
          <v-app-bar-title>Editor</v-app-bar-title>
          <template v-slot:append>
            <v-btn class="mx-2" variant="outlined" color="green" @click="checkConfig" prepend-icon="mdi-check">Check
              Config</v-btn>
            <v-btn variant="outlined" @click="executeDrillJob">Execute
              Drill Job</v-btn>
          </template>
        </v-app-bar>

        <Editor v-model="content" @save="saveConfiguration"></Editor>
      </v-sheet>
    </template>
  </vue-splitter>
</template>


<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import axios from "axios";
import yaml from 'js-yaml';
import { onBeforeRouteLeave } from 'vue-router'

import { useAxios } from '@vueuse/integrations/useAxios'
import { useToast } from '../composables/useToast';

import FileTreeSidebar from '../components/FileTreeSidebar.vue'
import VueSplitter from '@rmp135/vue-splitter'

import initial from '../assets/initial.yaml?raw'
import schema from '../../../schemas/schema.json?raw'
import Editor from '../components/Editor.vue'

import { ConfigurationFileRepository } from '../repositores/FileRepository'
import { useRepositoryList } from '@/composables/useRepositoryList';
import { useYamlValidation } from '@/composables/useYamlValidation';

const configurationsRepository = new ConfigurationFileRepository();

const toast = useToast();
const { execute } = useAxios(axios)

// Editor content.
const currentFile = ref<string | null>(null);
const content = ref<string>("");

// Most recently saved content. Used to compare with current content to see if it has changed.
const savedContent = ref<string>("");

const unsavedChanges = computed(() => content.value !== savedContent.value)

const { valid, error, validate } = useYamlValidation(schema, content)

/**
 * Checks if the current configuration is valid.
 */
function checkConfig() {
  if (validate()) {
    toast.success("Configuration is valid!")
  } else {
    toast.error("Configuration Invalid.", error.value ? error.value : '')
  }
}

/**
 * Sends job config file to backend. Should then be sent to workers to drill repositories.
 * Checks config before sending. If invalid, halts and creates error toast.
 */
async function executeDrillJob() {
  if (!validate()) {
    return
  }

  try {
    let response = await execute(`/jobs/${path}`, {
      method: 'POST',
      data: yaml.load(content.value)
    })
    toast.success("Jobs have been sent successfully.")
  } catch (e) {
    toast.error("Could not create jobs.")
    console.error(e)
  }

}

// ----- Confirm Leave when unsaved changes -----

const confirmLeaveMessage = "You have unsaved changes. Are you sure you want to leave ?";

/**
 * Before reloading the page, checks if there are unsaved changes and shows a confirm leave dialog.
 */
function beforeReload(event: { returnValue: string; }) {
  // To show confirm leave dialog.
  if (unsavedChanges.value) {
    event.returnValue = confirmLeaveMessage; // Needed for some browsers
  }
  return confirmLeaveMessage;
}

onMounted(() => {
  try {
    // Get the initial content from example config file.
    content.value = initial;
    savedContent.value = content.value;
  } catch (e) {
    console.error("Error parsing YAML file:", e);
  }
  window.addEventListener('beforeunload', beforeReload);
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeReload);
})

onBeforeRouteLeave(() => {
  if (unsavedChanges.value && !confirm(confirmLeaveMessage)) {
    return false
  }
  return true;
})

// ----- Saving Configurations -----

const { items: files, loading: filesIsLoading, fetchItems: getConfigFilesList } = useRepositoryList(configurationsRepository);

/**
 * On selection of file in sidebar, load the file and set the content.
 * @param path Path of the file to load.
 */
async function sidebarFileSelected(path: string) {
  try {
    let response = await configurationsRepository.getById(path)
    content.value = response.data;
    currentFile.value = path;
  } catch (e) {
    toast.error("Failed to load query files.")
  }
}

/**
 * Clears the editor content and sets back to initial boilerplate.
 * Sets current file name to null to indicate that a new file is being created.
 */
async function openNewFile() {
  content.value = initial;
  currentFile.value = null;
}


/**
 * Saves the current configuration file.
 */
async function saveConfiguration() {
  let filename = currentFile.value;
  if (filename === null) {
    filename = prompt("What do you want to name the configuration file?")
  }
  if (filename == null) {
    // User cancelled the save.
    return
  }
  let response = await configurationsRepository.update(filename, { content: content.value })

  if (response.status === 200) {
    toast.success("Saved configuration to new file.")
  } else if (response.status === 201) {
    toast.success("Updated saved configuration file.")
  }

  currentFile.value = filename;
  savedContent.value = content.value;

  await getConfigFilesList()

}
async function deleteConfiguration(path: string) {
  let ok = await confirm("Are you sure you want to delete this configuration file?")
  try {
    if (ok) {
      let response = await configurationsRepository.delete(path)
      toast.success("Query deleted.")
      // If the deleted file is the current file, open a clean new file.
      if (path === currentFile.value) {
        openNewFile()
      }
      await getConfigFilesList()
    } else {
      toast.warn("Deletion cancelled.")
    }
  } catch (e) {
    console.error(e)
    toast.error("Failed to delete query.")
  }
}

</script>
