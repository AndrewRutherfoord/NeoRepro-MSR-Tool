import json
from typing import Optional

from pydantic import BaseModel
from driller.drillers.neo4j_storage import Neo4jStorage


class LabelledCommit(BaseModel):
    type: str
    url: str
    hash: Optional[str] = None
    content: dict
    codes: list[str]


class Code(BaseModel):
    name: str
    description: str


class LabellingStorage(Neo4jStorage):
    def __init__(self, user, password, host, port, batch_size):
        super().__init__(user, password, host, port, batch_size)

    def load_codes(self):
        with open("./driller/scripts/cost_awareness_codes.json", "r") as file:
            codes = json.load(file)
        self.codes = []
        for code in codes:
            self.codes.append(Code.model_validate(code))

    def load_dataset(self):
        with open("./driller/scripts/cost_awareness_dataset.json", "r") as file:
            data = json.load(file)

        self.dataset: list[LabelledCommit] = []
        for item in data:
            obj = LabelledCommit.model_validate(item)
            self.dataset.append(obj)

    def get_commit_hash_from_url(self, url):
        url_split = url.split("/")

        if url_split[-2] != "commit":
            print(f"URL in the wrong format:  {url}")

        return url_split[-1]

    def filter_remove_issues(self):
        """In this case I am only using commit data, but dataset contains labelled issues."""

        self.dataset = list(filter(lambda o: o.type == "commit", self.dataset))

    def add_commit_hashes(self):
        for obj in self.dataset:
            obj.hash = self.get_commit_hash_from_url(obj.url)

    def store_code(self, code: Code):
        self._run_query(
            "MERGE (code:Code {name: $name}) SET code.description = $description",
            {"name": code.name, "description": code.description},
        )

    def store_codes(self):
        for code in self.codes:
            self.store_code(code)

    def store_code_commit_relationship(self, code: str, commit_hash: str):
        self._run_query(
            "MATCH (commit:Commit {hash: $commit_hash}) "
            "MATCH (code:Code {name: $code_name})"
            "MERGE (commit)-[:MEMBER_OF]->(code)",
            {"commit_hash": commit_hash, "code_name": code},
        )

    def store_code_commit_relationships(self):
        for obj in self.dataset:
            for code in obj.codes:
                self.store_code_commit_relationship(code, obj.hash)

    def execute(self):
        self.load_dataset()
        self.load_codes()

        print("Dataset & Codes Loaded.")

        self.filter_remove_issues()
        self.add_commit_hashes()

        print("Setup Complete. Adding to DB.")

        self.store_codes()

        print("Codes stored.")

        self.store_code_commit_relationships()

        print("Complete.")


def run():
    storage = LabellingStorage(
        user="neo4j", password="neo4j123", host="neo4j", port=7687, batch_size=10
    )

    storage.execute()

    storage.close()


if __name__ == "__main__":
    run()
