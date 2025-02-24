import warnings
warnings.filterwarnings('ignore')

from elasticsearch import Elasticsearch

def get_data(host, index, query=None, offset=0):
    es = Elasticsearch([host], http insol= True)
    
    try:
        if isinstance(query, dict):
            q = {k: v for k, v in query.items() if v is not None}
            query_str = ' '.join(f'"{k}":{v.replace("=", "")}' for k, v in q.items())
            es.indices.create(index=index)
            raw_data = es.search(
                index=index,
                body={'query': {'match_all': query}, 'from': offset},
                size=1000
            )['hits']['hits']
        else:
            if index:
                raw_data = es.get(index=index, size=1000)
            else:
                raw_data = []
        
        return raw_data
    except Exception as e:
        print(f"Error: {e}")
        return []

def how_to_use():
    """Cómo usar el tool de multiintent para acceder a datos OpenSearch"""
    print("1. Conectarse a tu Instancia de Elasticsearch")
    print("2. Definir la query que deseas ejecutar")
    print("3. Configurar los parámetros de offset si necesitas múltiples peticiones")
    print("4. Llama a get_data con tus parámetros")

if __name__ == "__main__":
    host = "tu host de Elasticsearch"
    index = "tu índice en OpenSearch"
    
    query_template = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"id": "*"}},
                    {  # filtrar por otros campos si es necesario
                        "term": {"variable": "*"}
                    }
                ]
            },
            "should": []
        }
    }
    
    results = get_data(host, index, query=query_template, offset=0)
    print("Resultados iniciales:")
    print(results[:5])
    print("\nFormato más detallado:")
    for item in results:
        print(item),index,offset,query,host