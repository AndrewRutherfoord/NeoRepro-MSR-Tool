<template>
  <v-app-bar>
    <v-app-bar-title>{{ title }}</v-app-bar-title>

    <template v-slot:append>
      <v-btn
        v-if="selectedJobs.length > 0"
        variant="outlined"
        prepend-icon="mdi-delete"
        @click="deleteSelected"
        >Delete Selected</v-btn
      >
      <v-btn icon="mdi-dots-vertical" id="menu-activator"></v-btn>
      <v-menu activator="#menu-activator">
        <v-list>
          <v-list-item @click="deleteAllJobs">
            <v-list-item-title>Delete All</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-app-bar>
</template>

<script lang="ts" setup>
import { useToast } from '@/composables/useToast'
const toast = useToast()

const selectedJobs = defineModel('selectedJobs')
const emit = defineEmits(['reload'])
const props = defineProps({
  title: String as PropType<string>
})

import { JobsRepository, type JobStatus, type ListOptions } from '@/repositores/JobsRepository'

const jobsRepository = new JobsRepository()

async function deleteSelected() {
  let ok = confirm('Are you sure you want to delete the selected jobs?')
  if (ok) {
    try {
      for (let id of selectedJobs.value) {
        await jobsRepository.delete(id)
      }
      selectedJobs.value = []
      emit('reload')
      toast.success('Deleted selected jobs.')
    } catch (e) {
      console.error(e)
      toast.error('Failed to delete selected jobs.')
    }
  }
}

async function deleteAllJobs() {
  let ok = confirm(
    'Are you sure you want to delete all of the jobs? This includes failed, pending and complete jobs. The work they did will not be undone.'
  )
  if (ok) {
    try {
      await jobsRepository.deleteAll()
      emit('reload')
      toast.success('Deleted All Jobs.')
    } catch (e) {
      console.error(e)
      toast.error('Failed to delete all jobs.')
    }
  }
}
</script>
