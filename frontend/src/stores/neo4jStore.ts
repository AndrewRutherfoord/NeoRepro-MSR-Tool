import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * Storage that holds the Neo4j database login details.
 */
export const useNeo4jAuthStore = defineStore('neo4jAuthStore', () => {
  // Todo: Make a way to change the login details

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
