# Invoice Processing Platform Prototype

A Streamlit-based prototype for processing and extracting information from invoice PDFs.

## Setup

1.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up Environment Variables**:
    Create a file named `.env` in the root directory of the project.
    Add your API keys to this file in the following format:

    ```env
    ANTHROPIC_API_KEY=your_anthropic_api_key_here
    # If using AWS Bedrock, you would also set your AWS credentials here or configure them via other standard AWS methods.
    # AWS_ACCESS_KEY_ID=your_aws_access_key_id
    # AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
    # AWS_SESSION_TOKEN=your_aws_session_token (if using temporary credentials)
    # AWS_DEFAULT_REGION=your_aws_region (e.g., us-east-1)
    ```
    Replace `your_anthropic_api_key_here` with your actual Anthropic API key. The `.env` file is already in `.gitignore` to prevent accidental commits of your keys.

4.  **Run the Application**:
    ```bash
    streamlit run app.py
    ```

## Features

- PDF invoice upload
- Choice of API provider (Anthropic API or AWS Bedrock)
- Automatic extraction of invoice details
- Clean display of extracted information
- Line items table view
- Export functionality for extracted data

## Note

This is an early prototype version. The actual LLM-based extraction functionality may require further refinement for accuracy and robustness across different invoice formats.