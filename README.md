# Graph DB MSR Tool

## Executing the Project

1. Copy env from example:

```bash
cp .env.example .env
```

2. Run the docker container:

```bash
docker compose up -d
```

3. Change the permissions of the import directory. This is necessary so that the backend can access the import directory.

```bash
chmod -R 775 neo4j_db/import/
```

4. Navigate to http://localhost:5173/

## 3 Operating Modes

This application can be used in  3 different ways, catering to different use cases.

### 1. Interacting with an existing reproduction dataset

TODO: Write this section

### 2. Reproduce a study using the replication package

TODO: Write this section

### 3. Create a new study

TODO: Write this section

## The Configuration Syntax

The configuration file is a YAML file that contains the following fields:

- `defaults`: Object containing default values for each drill job.
- `repositores`: List of repositories to be drilled. Defaults from `defaults` are applied to each, unless overridden.

### Defaults

The `defaults` object contains the following fields:

- `pydriller`: Object containing configurations for pydriller `Repository` class. All options explained at [pydriller](https://pydriller.readthedocs.io/en/latest/repository.html).
  - `since`: Date from which to start drilling. Format: YYYY-MM-DD
  - `to`: Date to which commits should be drilled. Format: YYYY-MM-DD
  - `from_commit`: A commit hash from which to start drilling.
  - `to_commit`: A commit hash to which commits should be drilled.
  - `from_tag`: A tag from which to start drilling.
  - `to_tag`: A tag to which commits should be drilled.
  - `only_in_branch`: Name of branch to be drilled.
  - `only_no_merge`: Boolean. If true, only commits that are not merged will be included.
  - `only_authors`: List of strings. Only commits by these authors will be included.
  - `only_commits`: List of strings. Commit hashes for commits to be included.
  - `only_release`: Boolean. Only commits that are tagged release will be included.
  - `filepath`: Only commits that modify this file will be included.
  - `only_modifications_with_file_types`: List of string. Only commits that modify files of this type will be included.
- `filters`: Object containing string filters.
  - `commit`: List of filters. (Shown below)

- `delete_clone`: Boolean. Indicates whether to delete the cloned repository after the drilling is complete.
- `index_file_modifications`: Boolean. Indicates whether to drill the modified files. If false, only the commits will be drilled.
- `index_file_diff`: Boolean. Indicates whether the file diffs should be indexed. If false, it won't be added to database.

#### Filters

A filter contains the following fields:

- `field`: The field to be checked for the filter.
- `value`: A string or list of strings. The value(s) to be checked for the filter. If list, then behaves as an `OR` (if field contains any of the values).
- `method`: Can be one of the following:
  - `contains`: The value is contained in the field.
  - `!contains`: The value is not contained in the field.
  - `exact`: The value is equal to the field.
  - `!exact`: The value is not equal to the field.


### Repositories

Each repository can contain all of the fields from `defaults` but must also contain the following fields:

- `name`: Name of the repository.
- `url`: Https url to the repository to clone it in the case it isn't already cloned.

If any values are not provided in the repository, the default values from `defaults` will be used.



## Working with Neo4j

### Exporting the Database

Exports the database to a file in the `import` directory of Neo4j.

```
CALL apoc.export.cypher.all("all.cypher", {
    format: "cypher-shell",
    useOptimizations: {type: "UNWIND_BATCH", unwindBatchSize: 20}
})
YIELD file, batches, source, format, nodes, relationships, properties, time, rows, batchSize
RETURN file, batches, source, format, nodes, relationships, properties, time, rows, batchSize;
```

### Importing the Database

```
CALL apoc.import.cypher.all("all.cypher")
```

## Use cases:

- I'm here to access the data
- I'm here to replicate the study
- I'm here to create a replication package

## Outline

- Intro
- Related Works
  - Say here why not using GraphRepo
- Case Study - Looking at cost awareness
  - REquirements go here.
- Design (& IMplementation)
- Evaluation
  - Show that fulfilled requirements

- Discussion (explain limitations)
  - Lessons learned 
- COnclusions
  - THis is how we answered the RQs
