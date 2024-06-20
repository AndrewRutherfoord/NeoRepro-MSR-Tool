<template>
    <div>
        <v-app-bar>
            <v-app-bar-title>Drill Job Statuses</v-app-bar-title>

            <v-btn v-if="selected" variant="outlined" prepend-icon="mdi-delete" @click="deleteSelected">Delete Selected
                Data</v-btn>
        </v-app-bar>
        <v-container>
            <v-card :title="`Open Drill Jobs (Remaining: ${pendingJobs.total})`">
                <job-status-table v-if="pendingJobs && pendingJobs.items" :items="pendingJobs"
                    v-model:options="pendingOptions" v-model:selected="selected" @delete-job="deleteJob"
                    @show-job-information="showDialog" :loading="loading" @reload="fetchPendingData"></job-status-table>

            </v-card>
            <v-card :title="`Failed Drill Jobs`">
                <job-status-table v-if="failedJobs && failedJobs.items" :items="failedJobs"
                    v-model:options="failedOptions" v-model:selected="selected" @delete-job="deleteJob"
                    @show-job-information="showDialog" :loading="loading" @reload="fetchFailedData"></job-status-table>

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

const panel = ref(false)
function openExpansion(state: boolean) {
    panel.value = state
}

const pendingJobs = ref<PaginatedResults<Job>>({ total: 0, items: [] })
const pendingOptions = ref<ListOptions>({
    limit: 20,
    offset: 0,
    statuses: ['pending', 'started']
})

const failedJobs = ref<PaginatedResults<Job>>({ total: 0, items: [] })
const failedOptions = ref<ListOptions>({
    limit: 20,
    offset: 0,
    statuses: ['failed']
})

async function fetchData(options: ListOptions) {
    loading.value = true
    console.log("Fetching data")
    try {
        const result = await jobsRepository.getAll(options)
        return result.data
    } catch (e) {
        console.log(e)
        throw e
    } finally {
        loading.value = false
    }

}

async function fetchPendingData() {
    pendingJobs.value = await fetchData(pendingOptions.value)
}

async function fetchFailedData() {
    failedJobs.value = await fetchData(failedOptions.value)
}


const loading = ref(true)
const items = ref<PaginatedResults<Job>>({ total: 0, items: [] })
const selected = ref<number[]>([])
const failed = ref<number>(0)

async function fetchAll() {
    await fetchPendingData();
    await fetchFailedData();
}
onMounted(() => {
    fetchAll()
})

// Delete

async function deleteJob(id: number) {
    let ok = confirm("Are you sure you want to delete this job? (This will only delete the info from the database. It will not undo the work.)")
    if (ok) {

        try {
            await jobsRepository.delete(id)
            await fetchAll()
            toast.success("Deleted selected jobs.")
        } catch (e) {
            console.error(e)
        }
    }
}


async function deleteSelected() {
    let ok = confirm("Are you sure you want to delete the selected jobs?")
    if (ok) {
        try {
            for (let id of selected.value) {
                await jobsRepository.delete(id)
            }
            selected.value = []
            await fetchAll()
            toast.success("Deleted selected jobs.")
        } catch (e) {
            console.error(e)
            toast.error("Failed to delete selected jobs.")
        }
    }
}

// Dialog 
const dialog = ref(false);
const dialogItem = ref();

function showDialog(item: Job) {
    dialogItem.value = item;
    dialog.value = true;
}


// Job Status Updates - Websocket
const { status } = useWebSocket('ws://127.0.0.1:8000/jobs/statuses/', { onMessage })

let messageBuffer: { job: Job, job_status: JobStatus }[] = []


function addStatus(job: Job, status: JobStatus) {
    let idx = items.value.items.findIndex(j => j.id === job.id)
    if (status.status === 'failed') {
        failedJobs.value.items.push({ ...job, statuses: [status] })
        items.value.items.splice(idx, 1)
        items.value.total--;
    }

    if (idx === -1) {
        items.value.items.push({ ...job, statuses: [status] })
    } else if (status.status === 'complete') {
        items.value.items.splice(idx, 1)
        items.value.total--;
    } else {
        try {
            items.value.items[idx].statuses.push(status)
        } catch (e) {
            console.error(e)
            console.error(items.value.items[idx])
        }
    }

    console.log(items.value.total)
    // Fetch more data if we have less than 5 items and more than 5 total
    if ((items.value.items.length - failed.value) < 5 && items.value.total > 5) {
        fetchPendingData()
    }
}

let isProcessing = false;
function processMessages() {
    if (isProcessing || loading.value) return
    isProcessing = true
    while (messageBuffer.length > 0) {
        let message = messageBuffer.shift()
        if (message) {
            let job: Job = message.job
            let jobStatus: JobStatus = message.job_status
            addStatus(job, jobStatus)
        }
    }
    isProcessing = false
}

function onMessage(ws: WebSocket, event: MessageEvent) {
    let message = JSON.parse(event.data)
    console.log(message)

    if (message.job_status.status === 'complete') {
        toast.success(`Drilling of '${message.job.name}' is complete.`)
    } else if (message.job_status.status === 'started') {
        toast.success(`Drilling of '${message.job.name}' started.`)
    } else if (message.job_status.status === 'error') {
        toast.error(message.message)
    } else if (message.job_status.status === 'warning') {
        toast.warn(message.message)
    }

    messageBuffer.push(message)
    processMessages();

}

</script>

<style scoped></style>