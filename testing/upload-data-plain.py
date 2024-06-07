import json
from neo4j import GraphDatabase

def create_node(tx, node):
    query = """
    CREATE (n:Commit {
        type: $type,
        url: $url,
        message: $message,
        codes: $codes
    })
    """
    tx.run(query, type=node['type'], url=node['url'], message=node['content'].get('message', None), codes=node['codes'])
        
def upload_to_neo4j(data, uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        for node in data:
            session.write_transaction(create_node, node)

    driver.close()

if __name__ == "__main__":
    neo4j_uri = 'bolt://localhost:7687' 
    neo4j_user = 'neo4j' 
    neo4j_password = 'neo4j123' 

    data = None
    with open('./dataset.json', 'r') as file:
        data = json.load(file)
    upload_to_neo4j(data, neo4j_uri, neo4j_user, neo4j_password)
