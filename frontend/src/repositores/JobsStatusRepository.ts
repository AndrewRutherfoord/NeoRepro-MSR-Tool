import type { AxiosResponse } from 'axios'
import {
  Repository,
  type ListRepository,
  type ItemRepository,
  type DeleteItemRepository,
  type CreateItemRepository
} from './Repository'

interface Job {
  id: number
  name: string
  data: Object
}

/**
 * Repository for managing job configuration files in the backend.
 */
export class JobsRepository
  extends Repository
  implements
    ListRepository<Job>,
    ItemRepository<Job>,
    CreateItemRepository<Object>,
    DeleteItemRepository
{
  constructor() {
    super('jobs')
  }

  async getAll(): Promise<AxiosResponse<Job[]>> {
    return this.http.get(``)
  }

  async getById(id: string | number): Promise<AxiosResponse<Job>> {
    return this.http.get(`${id}`)
  }

  async create(data: Object): Promise<AxiosResponse<string>> {
    return this.http.post(``, data)
  }

  async delete(id: string | number): Promise<AxiosResponse<void>> {
    return this.http.delete(`${id}`)
  }

  async deleteAll(): Promise<AxiosResponse<void>> {
    return this.http.delete(``)
  }
}
