<template>
    <!-- <v-navigation-drawer permanent> -->
    <v-list-item title="Saved Queries" subtitle="Click on one to open it and then execute it."></v-list-item>
    <v-divider></v-divider>
    <v-list v-if="!isLoading">
        <FileTreeNode v-for="key in Object.keys(data)" :key="key" :name="key" :data="data[key]" :path="key"
            @link-clicked="onClick" @delete-file="onDeleteFile"></FileTreeNode>
    </v-list>
    <!-- </v-navigation-drawer> -->
</template>

<script setup lang="ts">
import FileTreeNode from './FileTreeNode.vue'

defineProps(
    { data: Object, isLoading: Boolean }
)

const emits = defineEmits(['linkClicked', 'deleteFile'])

function onClick(path: string) {
    emits('linkClicked', path)
}

function onDeleteFile(path: string) {
    console.log("DELETE")
    emits('deleteFile', path)
}

</script>