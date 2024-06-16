import { onBeforeUnmount, onMounted, ref } from 'vue'
import neo4j, { Driver, Session } from 'neo4j-driver'

export function useNeo4j(uri: string, user: string, password: string) {
  const driver = ref<Driver | null>(null)
  const session = ref<Session | null>(null)
  const error = ref<any>(null)
  const loading = ref(false)

  const result = ref<any>(null)
  const headers = ref<string[] | null>(null)
  const notifications = ref<any>(null)

  // Initialize the driver and session
  const initialize = () => {
    driver.value = neo4j.driver(uri, neo4j.auth.basic(user, password))
    session.value = driver.value.session()
  }

  // Close the session and driver
  const close = () => {
    if (session.value) {
      session.value.close()
    }
    if (driver.value) {
      driver.value.close()
    }
  }

  // Run a Cypher query
  const runQuery = async (query: string, parameters = {}) => {
    loading.value = true
    error.value = null
    result.value = null
    headers.value = null

    try {
      if (!session.value) {
        throw new Error('Session not initialized')
      }

      const resultSet = await session.value.run(query, parameters)
      result.value = resultSet.records
      notifications.value = resultSet.summary.notifications
      result.value = resultSet.records.map((record) => record.toObject())

      if (resultSet.records.length > 0) {
        headers.value = resultSet.records[0].keys
        console.log(headers.value)
      }
    } catch (err) {
      error.value = err
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    initialize();
  });
  
  onBeforeUnmount(() => {
    close();
  });

  return {
    initialize,
    close,
    runQuery,
    error,
    loading,
    result,
    headers,
    notifications
  }
}
