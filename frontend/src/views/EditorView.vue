<template>
  <v-sheet height="100vh">
    <v-app-bar>
      <v-app-bar-title>Editor</v-app-bar-title>
      <template v-slot:append>
        <v-btn class="mx-2" variant="outlined" color="green" @click="checkConfig" prepend-icon="mdi-check">Check Config</v-btn>
        <v-btn variant="outlined" @click="executeDrillJob">Execute
          Drill Job</v-btn>
      </template>
    </v-app-bar>

    <Editor v-model="content"></Editor>
  </v-sheet>
</template>


<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import yaml from 'js-yaml';
import { onBeforeRouteLeave } from 'vue-router'
import axios from "axios";
import Ajv from 'ajv';
import addFormats from "ajv-formats"

import initial from '../assets/initial.yaml?raw'
// Fetch the schema from the root of the repository.
import schema from '../../../schemas/schema.json?raw'
import { useToast } from '../composables/useToast';
import Editor from '../components/Editor.vue'

const toast = useToast();

const confirmLeaveMessage = "You have unsaved changes. Are you sure you want to leave ?";

const content = ref("// Some code");
const unsavedChanges = ref(false);

async function checkConfig(createValidNotification = true) {
  let configuration;
  try {
    configuration = yaml.load(content.value)
  } catch (e) {
    toast.error("Could not parse yaml. Invalid syntax.")
    return false
  }

  const ajv = new Ajv();
  // Add formats extension to be able to check date formats
  addFormats(ajv)

  try {
    // Check if input matches schema
    const isValid = ajv.validate(JSON.parse(schema), configuration)

    if (isValid) {
      if (createValidNotification) {
        toast.success("Configuration is valid!")
      }
      return true;
    } else {
      let item = ajv.errors?.pop()
      let message = "";
      console.error(item)
      if (item?.params?.format === "date") {
        // For date fields, inform the user of the format that is expected.
        message = "Date format must match YYYY-MM-DD."
      } else {
        message = item?.message ? item.message : ":/";
      }
      toast.error("Configuration Invalid.", `Error at '${item?.instancePath}': ${message}\n`)
      return false;
    }
  } catch (e) {
    toast.error("Could not parse configuration.")
    return false;
  }

}

async function executeDrillJob() {
  if (!checkConfig(false)) {
    return
  }

  try {
    let response = axios.post("http://127.0.0.1:8000/jobs/", yaml.load(content.value))
    toast.success("Configuration Valid.")
  } catch (e) {
    toast.error("Could not create jobs.")
    console.error(e)
  }

}

async function loadInitial() {
  // const yamlFile = require('@/assets/initial.yaml'); // Adjust the path as necessary
  try {
    content.value = initial;
  } catch (e) {
    console.error("Error parsing YAML file:", e);
  }
}

function confirmLeave() {
  if (unsavedChanges.value && !confirm(confirmLeaveMessage)) {
    return false
  }
  return true;
}

function beforeReload(event: { returnValue: string; }) {
  // You can perform some cleanup here
  // To show a confirmation dialog:
  if (unsavedChanges.value) {
    event.returnValue = confirmLeaveMessage; // Needed for some browsers
  }
  return confirmLeaveMessage;
}

onMounted(() => {
  loadInitial();
  window.addEventListener('beforeunload', beforeReload);
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeReload);
})

watch(content, (newContent, oldContent) => {
  if (oldContent !== newContent && newContent !== initial) {
    unsavedChanges.value = true;
  }
})

onBeforeRouteLeave(() => {
  return confirmLeave()
})

</script>
