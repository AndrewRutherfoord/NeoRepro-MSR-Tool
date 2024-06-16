import type { AxiosResponse } from 'axios'
import {
  type ListRepository,
  type ItemRepository,
  Repository,
  type DeleteItemRepository,
  type UpdateItemRepository
} from './Repository'

export type SaveFileContent = {
  content: string
}

/**
 * Repository for managing job configuration files in the backend.
 */
export class FileRepository
  extends Repository
  implements
    ListRepository<Object>,
    ItemRepository<string>,
    UpdateItemRepository<SaveFileContent>,
    DeleteItemRepository
{
  constructor(endpoint: string) {
    super(endpoint)
  }

  async getAll(): Promise<AxiosResponse<Object[]>> {
    return this.http.get(``)
  }

  async getById(id: string): Promise<AxiosResponse<string>> {
    return this.http.get(`${id}`)
  }

  /**
   * Creates or updates a file in the backend.
   *
   * @param path Location of the file in the backend.
   * @param content Contents of the file.
   * @returns Response from the backend.
   */
  async update(path: string, content: SaveFileContent): Promise<AxiosResponse<SaveFileContent>> {
    return this.http.post(`${path}`, content)
  }

  async delete(id: string): Promise<AxiosResponse<void>> {
    return this.http.delete(`${id}`)
  }
}

export class ConfigurationFileRepository extends FileRepository {
  constructor() {
    super(`configs/`)
  }

  /**
   * Creates or updates a configuration file in the backend.
   * Appends .yaml to the file name if it is not already present.
   *
   * @param path Location of the file in the backend.
   * @param content Contents of the file.
   * @returns Response from the backend.
   */
  async update(path: string, content: SaveFileContent): Promise<AxiosResponse<SaveFileContent>> {
    if (!(path.endsWith('.yaml') || path.endsWith('.yml'))) {
      path = path + '.yaml'
    }
    return super.update(path, content)
  }
}

export class QueryFileRepository extends FileRepository {
  constructor() {
    super(`queries/`)
  }

  /**
   * Creates or updates a query file in the backend.
   * Appends .cql to the file name if it is not already present.
   *
   * @param path Location of the file in the backend.
   * @param content Contents of the file.
   * @returns Response from the backend.
   */
  async update(path: string, content: SaveFileContent): Promise<AxiosResponse<SaveFileContent>> {
    if (!path.endsWith('.yaml')) {
      path = path + '.yaml'
    }
    return super.update(path, content)
  }
}
