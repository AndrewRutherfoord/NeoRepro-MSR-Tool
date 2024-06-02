<script setup lang="ts">
// import { ref, onMounted } from 'vue'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import Editor from '../components/Editor.vue'
// import Editor2 from '../components/Editor2.vue'
import yaml from 'js-yaml';
import initial from '../assets/initial.yaml?raw'
import { onBeforeRouteLeave } from 'vue-router'

const confirmLeaveMessage = "You have unsaved changes. Are you sure you want to leave ?";

const content = ref("// Some code");
const unsavedChanges = ref(false);

function parseYaml() {
  let yamlOutput;
  try {
    const result = yaml.load(content.value);
    yamlOutput = JSON.stringify(result, null, 2);
  } catch (e) {
    yamlOutput = `Error parsing YAML: ${e.message}`;
  }
  console.log(yamlOutput)
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
          <button class="btn btn-outline-success me-2" type="button" @click="parseYaml">Execute
            Drill Job</button>
        </div>
      </div>
    </div>
  </nav>


  <!-- <header class="px-3 pb-1 pt-2 d-flex justify-content-between align-items-center">
    <h3>Editor</h3>
  </header> -->
  <Editor v-model="content"></Editor>
  <!-- <Editor></Editor> -->
</template>
