<!-- eslint-disable vue/valid-v-slot -->
<template>
    <!-- <div class="container-fluid mt-2"> -->
    <v-app-bar>
        <v-app-bar-title>Jobs</v-app-bar-title>
    </v-app-bar>


    <v-data-table :items="data" :loading="isLoading" :headers="headers" show-select v-model="selected"
        hide-default-footer>
        <template v-slot:item.statuses="{ value }">
            <v-chip class="ma-2 text-capitalize" variant="elevated" compact
                :color="getStatusChipColor(value.slice(-1)[0].status)">
                {{ value.slice(-1)[0].status }}
            </v-chip>
        </template>
        <template v-slot:item.button="{ item }">
            <v-btn color="primary" size="small" class="mx-2" @click="showDialog(item)">View</v-btn>
            <v-btn color="red-darken-2" size="small" class="mx-2" @click="deleteJob(item.id)">Delete</v-btn>
        </template>
    </v-data-table>


    <v-dialog v-model="dialog" width="700px">
        <v-card prepend-icon="mdi-update" title="Update in progress">
            <v-card-text>
                <h6>Job Configuration:</h6>
                <code class="text-red">
                <pre>{{ prettyJSON(dialogItem.data) }}</pre>
            </code>

                <h4>Statuses</h4>

                <ol>
                    <li v-for="status in dialogItem.statuses" :key="status.timestamp" class="text-capitalize"> {{ status.status }}
                        ({{ status.timestamp }})</li>
                </ol>


            </v-card-text>
            <template v-slot:actions>
                <v-btn class="ms-auto" text="Ok" @click="dialog = false"></v-btn>
            </template>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import axios from 'axios';
import { onMounted, ref } from 'vue'
import { useAxios } from '@vueuse/integrations/useAxios'
import yaml from 'js-yaml';

const { data, isLoading, execute } = useAxios('/jobs/', axios)

const selected = ref([])

const headers = [
    { title: 'ID', value: 'id' },
    { title: 'Job Name', value: 'name' },
    { title: 'Status', key: 'statuses' },
    {
        title: '',
        key: 'button',
    }
]

const dialog = ref(false);
const dialogItem = ref();

function showDialog(item) {
    dialogItem.value = item;
    dialog.value = true;
}

function prettyJSON(value: string) {
    //   return JSON.stringify(value, null, 2);
    return yaml.dump(value);
}

async function deleteJob(id: number) {
    let ok = confirm("Are you sure you want to delete this job? (This will only delete the info from the database. It will not undo the work.)")
    if (ok) {

        try {
            await axios.delete(`/jobs/${id}/`)
            execute();
        } catch (e) {
            console.error(e)
        }
    }
}


function getStatusChipColor(status: string) {
    switch (status) {
        case 'pending':
            return 'amber-lighten-1'
        case 'complete':
            return 'green'

        default:
            return "secondary";
    }
}

</script>