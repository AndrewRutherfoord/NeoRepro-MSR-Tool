<template>
    <v-data-table v-if="options !== undefined" :items="items.items" :headers="headers" :loading="loading"
        :items-per-page="options.limit" show-select v-model="selected">
        <template v-slot:item.status="{ item }">
            <v-progress-circular v-if="getJobStatus(item) === 'started'" color="green" indeterminate size="25"
                class="me-2"></v-progress-circular>
            <v-chip :color="getJobStatusColor(item)" text-color="white">
                {{ getJobStatus(item) }}
            </v-chip>
        </template>
        <template v-slot:item.timestamp="{ item }">
            {{ getJobTimestamp(item) }}
        </template>
        <template v-slot:item.button="{ item }">
            <v-btn color="primary" size="small" class="mx-2" @click="emit('show-job-information', item)">View</v-btn>
            <v-btn color="red-darken-2" size="small" class="mx-2" @click="emit('delete-job', item.id)">Delete</v-btn>
        </template>
        <template v-slot:bottom>
            <v-pagination :length="Math.ceil(items.total / options.limit)"
                @update:model-value="updatePage" :model-value="page"></v-pagination>
        </template>
    </v-data-table>
</template>

<script setup lang="ts">
import type { Job, JobStatus, Pagination } from '@/repositores/JobsRepository';
import type { PaginatedResults } from '@/repositores/Repository';
import { computed, ref } from 'vue';

const headers = [
    { title: 'Name', value: 'name' },
    { title: 'Status', value: 'status' },
    { title: 'timestamp', key: 'timestamp' },
    {
        title: '',
        key: 'button',
    }
]


const props = defineProps({
    items: {
        type: Object as () => PaginatedResults<Job>,
        required: true
    },
    loading: {
        type: Boolean,
        required: true
    }
})

const emit = defineEmits(['delete-job', 'show-job-information', 'reload'])

const selected = defineModel<number[]>('selected')

// Pagination

const options = defineModel<Pagination>('options')

function updatePage(value: number) {
    if (options.value == undefined) return
    options.value.offset = (value - 1) * options.value.limit
    console.log(options.value)
    emit('reload')
}

const page = computed(() => {
    if (options.value == undefined) return 1
    return Math.ceil(options.value?.offset / options.value.limit) + 1
})

// Render Functions

function getJobStatusObj(job: Job): JobStatus | undefined {
    if (job.statuses.length === 0) {
        return undefined
    }
    return job.statuses.slice(-1).pop()
}

function getJobStatus(job: Job) {
    let jobStatus = getJobStatusObj(job)

    if (jobStatus !== undefined) {
        return jobStatus.status
    }
    return 'pending'
}

function getJobTimestamp(job: Job) {
    let jobStatus = getJobStatusObj(job)

    if (jobStatus !== undefined) {
        let date = Date.parse(jobStatus.timestamp)
        return new Date(date).toLocaleString()
    }
    return ''
}

function getJobStatusColor(job: Job) {
    let status = getJobStatus(job)
    switch (status) {
        case 'pending':
            return 'primary'
        case 'started':
            return 'secondary'
        case 'complete':
            return 'success'
        case 'failed':
            return 'error'
    }
}

</script>

<style scoped></style>