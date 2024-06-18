<template>
    <div>
        <v-app-bar>
            <v-app-bar-title>Manage Neo4j Database</v-app-bar-title>
        </v-app-bar>
        <v-container fluid class="rounded-0">
            <v-row>
                <v-col>
                    <neo4j-database-overview ref="overviewCard"></neo4j-database-overview>
                </v-col>
            </v-row>
            <v-row>
                <v-col>
                    <v-card>
                        <file-tree-list title="Database Images" subtitle="Here you can load database backups"
                            :data="files" :is-loading="filesIsLoading"
                            create-new-tooltip="Backup Current Database State" @linkClicked="restoreBackup"
                            @createFile="backupCurrentDatabase"></file-tree-list>
                    </v-card>
                </v-col>
                <v-col>
                    <v-card title="Settings">
                        <v-list>
                            <v-list-item value="notifications">
                                <template v-slot:prepend="{ isActive }">

                                    <v-list-item-action start>
                                        <v-btn color="red" @click="clearDatabase"><v-icon>mdi-delete</v-icon></v-btn>
                                    </v-list-item-action>
                                </template>

                                <v-list-item-title>Clear Database</v-list-item-title>

                            </v-list-item>
                        </v-list>
                    </v-card>
                </v-col>
            </v-row>
        </v-container>
    </div>
</template>

<script setup lang="ts">
import { useRepositoryList } from '@/composables/useRepositoryList';
import { DatabaseBackupsRepository } from '@/repositores/DatabaseBackupsRepository';
import FileTreeList from '@/components/FileTreeList.vue';
import { computed, onMounted, ref } from 'vue';
import { useNeo4j } from '@/composables/useNeo4j';
import { useToast } from '@/composables/useToast';
import Neo4jDatabaseOverview from '@/components/Neo4jDatabaseOverview.vue';

const repository = new DatabaseBackupsRepository();

const toast = useToast();
const { items, loading: filesIsLoading, fetchItems: getFiles } = useRepositoryList(repository);

// TODO: Move credentials to store.
const { runQuery, error, loading, result, headers } = useNeo4j('neo4j://localhost:7687', 'neo4j', 'neo4j123');

const files = computed(() => {
    if (items.value === null || items.value == undefined)  {
        return null
    }
    return items.value["neo4j_import"]
})

const overviewCard = ref()

function reload() {
    getFiles()
    overviewCard.value.getData()
}

async function clearDatabase() {
    let ok = await confirm("Are you sure you want to clear the database?")
    if (!ok) {
        return
    }
    try {
        await runQuery(`MATCH (n) DETACH DELETE n`)
        await runQuery(`CALL apoc.schema.assert({},{},true) YIELD label, key RETURN *`)
        toast.success("Database cleared.")
        reload()
    } catch (err) {
        console.log(err)
        toast.error("Failed to clear database.")
    }
}

async function restoreBackup(path: string) {
    let ok = await confirm(`Are you sure you want to restore '${path}'? This will first delete EVERYTHING in the database.`)
    if (!ok) {
        return
    }
    try {
        let clearDBResultSet = await runQuery(`MATCH (n) DETACH DELETE n`)
        console.log(clearDBResultSet)
        clearDBResultSet = await runQuery(`CALL apoc.schema.assert({},{},true) YIELD label, key RETURN *`)
        console.log(clearDBResultSet)
        let resultSet = await runQuery(`CALL apoc.cypher.runFile("${path}")`)
        console.log(resultSet)
        toast.success("Database wiped and restored from backup.")
        reload()
    } catch (err) {
        console.log(err)
        toast.error("Failed to restore backup.")
    }
}

async function backupCurrentDatabase() {
    let filename = prompt("What do you want to name the backup file?")
    if (filename == null || filename === "") {
        // User cancelled the save.
        return
    }
    if (!filename.endsWith(".cypher")) {
        filename += ".cypher"
    }
    try {

        let resultSet = await runQuery(`CALL apoc.export.cypher.all("${filename}", 
        {format: "cypher-shell",useOptimizations: {type: "UNWIND_BATCH", unwindBatchSize: 20}}) 
        YIELD file, batches, source, format, nodes, relationships, properties, time, rows, batchSize 
        RETURN file, batches, source, format, nodes, relationships, properties, time, rows, batchSize;`)
        toast.success("Backup created.")
        await reload()
        
    } catch (err) {
        console.log(err)
        toast.error("Failed to create backup.")
    }
}

</script>