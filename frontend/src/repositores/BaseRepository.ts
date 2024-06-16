// src/repositories/BaseRepository.ts
import axios, { type AxiosInstance, type AxiosResponse } from 'axios'

/**
 * Base class for all repositories. It provides a common interface for fetching data from the backend.
 */
export abstract class BaseRepository<ListType, ItemType> {
  protected http: AxiosInstance

  constructor(endpoint: string, baseDomain: string = 'http://127.0.0.1:8000') {
    this.http = axios.create({ baseURL: `${baseDomain}/${endpoint}` })
  }

  public async getAll(): Promise<AxiosResponse<ListType[]>> {
    return this.http.get<ListType[]>('/')
  }

  public async getById(id: number | string): Promise<AxiosResponse<ItemType>> {
    return this.http.get<ItemType>(`/${id}`)
  }

  public async create(data: ItemType): Promise<AxiosResponse<ItemType>> {
    return this.http.post<ItemType>('/', data)
  }

  public async update(id: number | string, data: ItemType): Promise<AxiosResponse<ItemType>> {
    return this.http.put<ItemType>(`/${id}`, data)
  }

  public async delete(id: number | string): Promise<AxiosResponse<void>> {
    return this.http.delete<void>(`/${id}`)
  }
}
