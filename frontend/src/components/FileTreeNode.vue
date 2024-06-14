<template>
    <v-list-item v-if="data === null">
        <pre class="text-red">{{ name }}</pre>
        <template v-slot:append>
            <v-tooltip text="Open Query">
                <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-open-in-app" density="compact" variant="plain" @click="onClick(`${path}`)"
                        v-bind="props">
                    </v-btn>
                </template>
            </v-tooltip>
            <v-tooltip text="Delete query">
                <template v-slot:activator="{ props }">
                    <v-btn icon="mdi-delete" density="compact" variant="plain" @click="onDeleteFile(`${path}`)"
                        v-bind="props">
                    </v-btn>
                </template>
            </v-tooltip>
        </template>
    </v-list-item>
    <v-list-group v-else>
        <template v-slot:activator="{ props }">
            <v-list-item v-bind="props" :title="name"></v-list-item>
        </template>
        <FileTreeNode v-for="k in Object.keys(data)" :key="k" :name="k" :data="data[k]" @link-clicked="onClick"
            :path="`${path}/${k}`" @delete-file="onDeleteFile">
        </FileTreeNode>
    </v-list-group>
</template>

<script setup lang="ts">

defineProps({
    name: { type: String, required: true },
    data: { type: Object },
    path: { type: String, required: true }
});

const emits = defineEmits(['linkClicked', "deleteFile"])

function onClick(path: string) {
    emits('linkClicked', path)
}

function onDeleteFile(path: string) {
    emits('deleteFile', path)
}

</script>