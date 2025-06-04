# Import necessary libraries
import os
import json
import requests
from pathlib import Path

# Create a new cell with the following code
# Create the directory structure
base_path = './data_sources'
Path(base_path).mkdir(parents=True, exist_ok=True)

# URLs for the shareholder letters
urls = {
    'Amazon-Shareholder-Letter-2023.pdf': 'https://s2.q4cdn.com/299287126/files/doc_financials/2024/ar/Amazon-com-Inc-2023-Shareholder-Letter.pdf',
    'Amazon-Shareholder-Letter-2020.pdf': 'https://s2.q4cdn.com/299287126/files/doc_financials/2021/ar/Amazon-2020-Shareholder-Letter-and-1997-Shareholder-Letter.pdf'
}

# Download PDFs
for filename, url in urls.items():
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(base_path, filename), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")

# Create metadata files
metadata = {
    'Amazon-Shareholder-Letter-2023.pdf.metadata.json': {
        "metadataAttributes": {
            "_created_at": "2025-03-26T05:33:59+00:00",
            "_last_updated_at": "2025-04-02T06:34:52+00:00",
            "DocumentId": "Amazon-Shareholder-Letter-2023.pdf",
            "Title": "Amazon-Shareholder-Letter-2023.pdf"
        }
    },
    'Amazon-Shareholder-Letter-2020.pdf.metadata.json': {
        "metadataAttributes": {
            "_created_at": "2025-03-26T05:33:59+00:00",
            "_last_updated_at": "2025-04-02T06:34:52+00:00",
            "DocumentId": "Amazon-Shareholder-Letter-2020.pdf",
            "Title": "Amazon-Shareholder-Letter-2020.pdf"
        }
    }
}

# Write metadata files
for filename, content in metadata.items():
    with open(os.path.join(base_path, filename), 'w') as f:
        json.dump(content, f, indent=4)
    print(f"Created metadata file {filename}")

print("\nAll tasks completed!")
