import json
from neo4j import GraphDatabase

def create_commit_node(tx, node):
    query = """
    CREATE (c:Commit {
        type: $type,
        url: $url,
        message: $message
    })
    RETURN c
    """
    result = tx.run(query, type=node['type'], url=node['url'], message=node['content'].get('message', None))
    return result.single()[0].element_id

def create_code_node(tx, code):
    query = """
    MERGE (code:Code {name: $name})
    RETURN code
    """
    result = tx.run(query, name=code)
    return result.single()[0].element_id

def create_relationship(tx, commit_id, code_id):
    query = """
    MATCH (c:Commit), (code:Code)
    WHERE elementId(c) = $commit_id AND elementId(code) = $code_id
    CREATE (c)-[:USES]->(code)
    """
    tx.run(query, commit_id=commit_id, code_id=code_id)

def upload_to_neo4j(data, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        for node in data:
            commit_id = session.execute_write(create_commit_node, node)
            for code in node['codes']:
                code_id = session.execute_write(create_code_node, code)
                session.execute_write(create_relationship, commit_id, code_id)

    driver.close()

if __name__ == "__main__":
    neo4j_uri = 'bolt://localhost:7687' 
    neo4j_user = 'neo4j' 
    neo4j_password = 'neo4j123' 

    data = None
    with open('./dataset.json', 'r') as file:
        data = json.load(file)
    upload_to_neo4j(data, neo4j_uri, neo4j_user, neo4j_password)