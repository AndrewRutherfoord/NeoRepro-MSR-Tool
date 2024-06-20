<template>
    <div>
        <v-app-bar>
            <v-app-bar-title>Drill Job Statuses</v-app-bar-title>

            <v-btn v-if="selected" variant="outlined" prepend-icon="mdi-delete" @click="deleteSelected">Delete All</v-btn>
        </v-app-bar>
        <v-container>
            <v-card title="Complete Drill Jobs">
                <job-status-table v-if="jobs && jobs.items" :items="jobs" v-model:options="options"
                    v-model:selected="selected" @delete-job="deleteJob" @show-job-information="showDialog"
                    :loading="loading"></job-status-table>

            </v-card>
        </v-container>
        <job-info-dialog v-model="dialog" :job="dialogItem"></job-info-dialog>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useToast } from '@/composables/useToast';
import { useWebSocket } from '@vueuse/core'

import JobInfoDialog from '@/components/JobInfoDialog.vue'
import JobStatusTable from '@/components/JobStatusTable.vue'
import { useRepositoryList } from '@/composables/useRepositoryList';
import { JobsRepository, type JobStatus, type ListOptions } from '@/repositores/JobsRepository';
import { type Job } from '@/repositores/JobsRepository';
import type { PaginatedResults } from '@/repositores/Repository';

const toast = useToast();
const jobsRepository = new JobsRepository()


const jobs = ref<PaginatedResults<Job>>({ total: 0, items: [] })
const options = ref<ListOptions>({
    limit: 20,
    offset: 0,
    statuses: ['complete']
})
const loading = ref(true)

async function fetchData() {
    loading.value = true
    console.log("Fetching data")
    try {
        const result = await jobsRepository.getAll(options.value)
        jobs.value = result.data
    } catch (e) {
        console.log(e)
        toast.error("Failed to fetch jobs.")
    } finally {
        loading.value = false
    }
    
}
const selected = ref<number[]>([])

onMounted(() => {
    fetchData();
})

async function deleteJob(id: number) {
    let ok = confirm("Are you sure you want to delete this job? (This will only delete the info from the database. It will not undo the work.)")
    if (ok) {

        try {
            await jobsRepository.delete(id)
            await fetchData()
            toast.success("Deleted selected jobs.")
        } catch (e) {
            console.error(e)
        }
    }
}

const dialog = ref(false)
const dialogItem = ref<Job>()

function showDialog(item) {
    dialogItem.value = item
    dialog.value = true
}

</script>