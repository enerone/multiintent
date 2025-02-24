# Prompt utilizado: quiero una tool para que obtenga de opensearch todos los documentos relacionados con gimansia

import os
import requests
import json
import ollama
from toolitoolit import OpenSearch

def get_documents(query):
    config = {
        "key": os.getenv("OPEN_SEARCH_API_KEY"),
        "host": os.getenv("OPEN_SEARCH_HOST")
    }
    
    if not all(config.values()):
        raise ValueError("Configuración incompleta. Necesita tener una llave y un host.")

    search_options = {
        "parallelism": 1,
        "aggs": {
            "_all": {
                "terms Aggregation": {
                    "terms": {
                        "field": "$doc_type"
                    }
                }
            }
        },
        "paging": {
            "size": 100
        }
    }

    query_params = {
        "q": f"query:match({{'doc_type': '%'}},'gimansia')"
    }

    response = requests.post(
        f"{config['host']}/_search",
        json={
            "_type": " synonym",
            "query synonyms": [os.query(config, search_options, query_params)]
        }
    )

    if not response.ok:
        raise requests.exceptions.HTTPError(f"Error {response.status_code}: {response.text}")

    return json.loads(response.content.decode('utf-8'))

# Ejemplo de uso
resultados = get_documents({"q": {"doc_type": "gimansia"}})
print(resultados)