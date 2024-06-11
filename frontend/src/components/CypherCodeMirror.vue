<template>
    <div ref="editorRef"></div>
</template>

<script setup lang="ts">
import { createCypherEditor } from '@neo4j-cypher/codemirror';
import { ref, onMounted, defineModel } from 'vue'

const editorRef = ref();


const model = defineModel();

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

    const { editor } = createCypherEditor(editorRef.value, {})
    editor.onValueChanged((value: string) => {
        model.value = value
    })
})

</script>

<style scoped></style>