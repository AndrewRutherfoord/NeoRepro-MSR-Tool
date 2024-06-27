import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNeo4jAuthStore = defineStore('neo4jAuthStore', () => {
  const host = ref<string>('localhost')
  const port = ref<string>('7687')
  const user = ref<string>('neo4j')
  const password = ref<string>('neo4j123')

  return {
    host,
    port,
    user,
    password
  }
})
