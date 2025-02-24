# Prompt utilizado: I want a tool to get into an opensearch database and search for clima

import os
import orjson
import pandas as pd

# Replace 'your_opensearch_database_url' with your actual database URL
db = osd.connect('http://localhost:8080', verify=False)

try:
    # Search for metadata containing 'climate'
    climate_metadata = db.searchmetadata(searchq={'match': {'climate': {}}})
    
    # Fetch detailed information for each matching entry
    results = []
    for entry in climate_metadata['entries']:
        try:
            # Get the full entry details
            entry_data = db.getentry(entry['_id'])
            
            # Extract relevant fields
            results.append({
                'ID': entry['_id'],
                'ClimateData': orjson.loads(entry_data['_content_']['json'])['data']
            })
            
        except Exception as e:
            print(f"Error fetching entry {entry['_id']}: {e}")
    
    # Convert results to DataFrame for better visualization
    df = pd.DataFrame(results)
    print(df)
except Exception as e:
    print(f"Connection error: {e}")