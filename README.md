# Invoice Processing Platform Prototype

A Streamlit-based prototype for processing and extracting information from invoice PDFs.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Features

- PDF invoice upload
- Automatic extraction of invoice details (placeholder for now)
- Clean display of extracted information
- Line items table view
- Export functionality for extracted data

## Note

This is a prototype version with mock data extraction. The actual LLM-based extraction functionality will be implemented in future versions.