<template>
    <div class="container-fluid mt-2">
        <h2>Jobs</h2>
        <hr>
        <div class="d-flex justify-content-center" v-if="isLoading">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
        <p v-else-if="data.length === 0">
            No jobs available...
        </p>
        <div v-else class="accordion" id="accordionPanelsStayOpenExample">
            <div class="accordion-item" v-for="(job, index) in data" :key="job.id">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        :data-bs-target="`#job-${index}-details`" aria-expanded="false"
                        :aria-controls="`job-${index}-details`">
                        {{ job.name }} ({{ job.status }})
                    </button>
                </h2>
                <div :id="`job-${index}-details`" class="accordion-collapse collapse">
                    <div class="accordion-body">
                        <h6>Job Configuration:</h6>
                        <code>
                    <pre>{{ prettyJSON(job.data) }}</pre>
                </code>
                        <hr>
                        <button class="btn btn-danger btn-sm" @click="deleteJob(job.id)">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { onMounted } from 'vue'
import { useAxios } from '@vueuse/integrations/useAxios'
import yaml from 'js-yaml';

const { data, isFinished, isLoading, execute } = useAxios('/jobs/', axios)

function prettyJSON(value: string) {
    //   return JSON.stringify(value, null, 2);
    return yaml.dump(value);
}

async function deleteJob(id: number) {
    try {
        await axios.delete(`/jobs/${id}/`)
        execute();
    } catch (e) {
        console.error(e)
    }
}

</script>