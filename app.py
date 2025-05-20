import streamlit as st
import pandas as pd
from datetime import datetime
from bedrock_client import BedrockClient
from image_processor import get_image_from_pdf
import base64
from io import BytesIO

st.set_page_config(
    page_title="Invoice Processing Platform", page_icon="📄", layout="wide"
)

# Custom CSS for the preview container
st.markdown(
    """
    <style>
    div[data-testid="stImage"] {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        background-color: #f8f9fa;
        margin-right: 3rem;
        max-width: 95% !important;
    }
    div[data-testid="stImage"] img {
        max-width: 100% !important;
        height: auto !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📄 Invoice Processing Platform")

# Initialize Bedrock client
bedrock_client = BedrockClient()

# File uploader
uploaded_file = st.file_uploader("Upload an invoice (PDF)", type=["pdf"])

if uploaded_file is not None:
    try:
        # Read PDF content
        pdf_bytes = uploaded_file.read()

        # Convert PDF to image
        with st.spinner("Converting PDF to image..."):
            image_base64 = get_image_from_pdf(pdf_bytes)

            if image_base64 is None:
                st.error("Failed to process the PDF. Please try again.")
                st.stop()

        # Show processing status
        with st.spinner("Processing document..."):
            # Extract data using Bedrock
            extracted_data = bedrock_client.extract_invoice_data(image_base64)

            if extracted_data is None:
                st.error("Failed to extract data from the document. Please try again.")
                st.stop()

            # Create two columns for the main layout
            preview_col, data_col = st.columns([0.4, 0.6])

            # Display the processed image in the left column
            with preview_col:
                st.subheader("Document Preview")
                st.image(base64.b64decode(image_base64), use_column_width=True)

            # Display extracted data in the right column
            with data_col:
                # Display document type
                st.subheader(
                    f"Document Type: {extracted_data.get('document_type', 'Unknown').upper()}"
                )

                # Only proceed if we have invoices to display
                if extracted_data.get("document_type") in [
                    "invoice",
                    "reminder",
                    "credit_note",
                ] and extracted_data.get("invoices"):
                    for idx, invoice in enumerate(extracted_data["invoices"]):
                        st.markdown("---")
                        # Display extracted information in a clean layout
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Invoice Number:** {invoice.get('number', '')}")
                            st.write(f"**PO Number:** {invoice.get('po_number', '')}")
                            st.write(f"**Vendor:** {invoice.get('vendor', '')}")
                            st.write(f"**Invoice Date:** {invoice.get('date', '')}")
                            st.write(f"**Due Date:** {invoice.get('due_date', '')}")
                            st.write(
                                f"**Payment Terms:** {invoice.get('payment_terms', '')}"
                            )

                        with col2:
                            currency = invoice.get("currency_code", "")
                            amount = invoice.get("amount", "")
                            tax_amount = invoice.get("tax_amount", "")
                            st.write(f"**Currency:** {currency}")
                            if amount:
                                st.write(f"**Total Amount:** {float(amount):,.2f}")
                            else:
                                st.write(f"**Total Amount:**")
                            if tax_amount:
                                st.write(f"**Tax Amount:** {float(tax_amount):,.2f}")
                            else:
                                st.write(f"**Tax Amount:**")

                        # Display line items in a table
                        if "line_items" in invoice:
                            st.subheader("Line Items")
                            df = pd.DataFrame(invoice["line_items"])

                            # Convert numeric columns to float
                            numeric_columns = ["quantity", "unit_price", "total"]
                            for col in numeric_columns:
                                if col in df.columns:
                                    df[col] = pd.to_numeric(df[col], errors="coerce")

                            st.dataframe(
                                df,
                                column_config={
                                    "description": "Description",
                                    "quantity": st.column_config.NumberColumn(
                                        "Quantity", format="%.0f"
                                    ),
                                    "unit_price": st.column_config.NumberColumn(
                                        "Unit Price", format="%.2f"
                                    ),
                                    "total": st.column_config.NumberColumn(
                                        "Total", format="%.2f"
                                    ),
                                },
                                hide_index=True,
                                use_container_width=True,
                            )

                            # Add a download button for the extracted data
                            if st.button(f"Download Invoice Data"):
                                # Convert to CSV
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"invoice_{invoice.get('number', 'unknown')}.csv",
                                    mime="text/csv",
                                )
                else:
                    st.info("No invoice data to display for this document type.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.stop()
