<template>
    <div ref="editorDiv"></div>
</template>

<script setup lang="ts">
import { createCypherEditor } from '@neo4j-cypher/codemirror';
import { editor } from 'monaco-editor';
import { ref, onMounted, defineModel, watch } from 'vue'

const editorDiv = ref();

const originalValue = ref();

const editorInstance = ref();

const query = ref("")
onMounted(() => {
    // const myKeymap = [
    //     {
    //         key: "Ctrl-Enter",
    //         run: () => {
    //             console.log("Ctrl+Enter was pressed!");
    //             // Custom action on Ctrl+Enter
    //             return true; // Return true to prevent the default action
    //         },
    //     },
    // ];

    const { editor } = createCypherEditor(editorDiv.value, {})
    editorInstance.value = editor
    editor.onValueChanged((value: string) => {
        query.value = value
    })

    originalValue.value = "";
})

function setValue(value : string) {
    originalValue.value = value;
    editorInstance.value.setValue(value)
}

function getQuery() {
    return query.value
}

defineExpose({
    setValue,
    getQuery
});

</script>

<style scoped></style>