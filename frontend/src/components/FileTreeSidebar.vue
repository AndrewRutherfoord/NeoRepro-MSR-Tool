<template>
    <!-- <v-navigation-drawer permanent> -->
    <v-list-item :title="title" :subtitle="subtitle">
        <template v-slot:append>
            <v-btn icon="mdi-file-document-plus-outline" variant="text" @click="createFile"></v-btn>
        </template>
    </v-list-item>
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
    { title: String, subtitle: String, data: Object, isLoading: Boolean }
)

const emits = defineEmits(['linkClicked', 'deleteFile','createFile'])

function onClick(path: string) {
    emits('linkClicked', path)
}

function onDeleteFile(path: string) {
    emits('deleteFile', path)
}

function createFile() {
    emits('createFile')
}

</script>