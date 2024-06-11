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

async function executeDrillJob() {
  let configuration = yaml.load(content.value)

  const ajv = new Ajv();
  // Add formats extension to be able to check date formats
  addFormats(ajv)

  try {

    const isValid = ajv.validate(JSON.parse(schema), configuration)
    if (!isValid) {
      let item = ajv.errors?.pop()
      let message = "";
      console.error(ajv.errorsText())
      if (item?.params && item.params?.format === "date") {
        // For date fields, inform the user of the format that is expected.
        message = "Date format must match YYYY-MM-DD."
      } else {
        message = item?.message ? item.message : ":/";
      }
      toast.error("Configuration Invalid.", `Error at '${item?.instancePath}': ${message}\n`)
      return
    }
  } catch (e) {
    toast.error("Could not parse configuration.")

    console.error(e)
  }
  toast.success("Configuration Valid.")

  try {
    let response = axios.post("http://127.0.0.1:8000/jobs/", configuration)
    console.log(response)
  } catch (e) {
    console.error(e)
  }
  console.log(configuration)

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

function beforeReload(event) {
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

<template>
  <nav class="navbar navbar-expand-lg bg-light">
    <div class="container-fluid">
      <div class="collapse navbar-collapse" id="navbarText">
        <div class="me-auto">
          <h2>Editor</h2>
        </div>
        <div class="navbar">
          <button class="btn btn-outline-success me-2" type="button" @click="executeDrillJob">Execute
            Drill Job</button>
        </div>
      </div>
    </div>
  </nav>


  <!-- <header class="px-3 pb-1 pt-2 d-flex justify-content-between align-items-center">
    <h3>Editor</h3>
  </header> -->
  <Editor v-model="content"></Editor>
</template>
