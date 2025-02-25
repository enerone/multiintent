import pandas as pd
from opensearchpy import OpenSearch

# Correct OpenSearch client initialization (example)
osd = OpenSearch(
    host="localhost",
    port=9200,
    http_auth=('admin', 'password'),
    use_ssl=True,
    verify_certs=True,
    ResponsiveScrolling=True
)

url = osd.get_url()
db = OpenSearchClient(url, verify_certs=False).create_index()

# Fix the search query to correctly find metadata entries with climate data
query = {
    "match": {
        "_source": ["climate"]
    }
}

metadata_result = db.search(
    body=query,
    per_page=1000
)

entries = []
for entry in metadata_result.entries():
    entry_data = entry.get('_content_')
    climate_json = entry_data.get('json', {}).get('data', {})
    if 'attributes' in climate_json:
        # Assuming data is nested under the 'attributes' key within 'json'
        entries.append(climate_json)
    
if entries:
    df = pd.DataFrame(entries),