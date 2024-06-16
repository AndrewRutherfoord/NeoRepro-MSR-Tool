import { BaseRepository } from './BaseRepository'

/**
 * Repository for managing job configuration files in the backend.
 */
export class ConfigurationsRepository extends BaseRepository<Object, string> {
  constructor() {
    super(`configs/`)
  }
}
