import type { AxiosResponse } from 'axios'
import {
  Repository,
  type ListRepository,
  type ItemRepository,
  type DeleteItemRepository,
  type CreateItemRepository
} from './Repository'

/**
 * Repository for managing job configuration files in the backend.
 */
export class DatabaseBackupsRepository extends Repository implements ListRepository<Object> {
  constructor() {
    super('db-exports/')
  }

  async getAll() {
    return this.http.get(``)
  }
}
