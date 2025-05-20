import boto3
import json
import os
from typing import Dict, Any
from decimal import Decimal

# Set AWS region in environment variable
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


class BedrockClient:
    def __init__(self):
        # Create session with explicit region
        session = boto3.Session(region_name="us-east-1")
        self.client = session.client("bedrock-runtime")
        self.model_id = (
            "anthropic.claude-3-5-sonnet-20240620-v1:0"  # Using Claude 3.5 Sonnet
        )

    def _parse_numeric(self, value: str) -> float:
        """Parse numeric values from strings, handling various formats."""
        if not value or not isinstance(value, str):
            return 0.0
        try:
            # Remove currency symbols and other non-numeric characters except decimal point and minus
            cleaned = "".join(c for c in value if c.isdigit() or c in ".-")
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _parse_line_items(self, items: list) -> list:
        """Parse numeric values in line items."""
        parsed_items = []
        for item in items:
            parsed_item = item.copy()
            for field in ["quantity", "unit_price", "total"]:
                if field in parsed_item:
                    parsed_item[field] = self._parse_numeric(str(parsed_item[field]))
            parsed_items.append(parsed_item)
        return parsed_items

    def extract_invoice_data(self, image_base64: str) -> Dict[str, Any]:
        """
        Extract invoice data using AWS Bedrock's Claude model from an image.

        Args:
            image_base64 (str): Base64 encoded image of the invoice

        Returns:
            Dict[str, Any]: Extracted invoice data
        """
        prompt = """These images are pages from a document sent to an accounts payable inbox. 
Your job is to identify the type of document and extract details for a number of different fields 
if the document is an invoice, credit note, or a reminder document, and return those in JSON format. 
Before extracting any information, you need to classify the document to one of the following types:
# invoice: If the any of the images contain an invoice then return 'invoice'
# statement: If the document is a statement, then return 'statement'
# reminder: If the document is marked as a reminder, or is a reminder letter, list of open/pending invoices, 
or aging report, then return 'reminder'
# credit_note: If the document is a credit note then return 'credit_note'
# purchase_order: If the document is a purchase order then return 'purchase_order'
# remittance_advice: If the document is a remittance advice then return 'remittance_advice'
# other: If the document is none of the above then return 'other'

If you've classified the document as 'invoice', 'reminder', or 'credit_note', proceed with extracting the 
invoice details from the document's images. 
If the document is classified as any other type, don't extract any invoice information from it.

When extracting invoice details, you must extract the details as precisely as possible and extract the 
exact answer that is provided in the form, without changing the text at all. 
If no answer has been provided for a field, then return an empty string for that field.

Below are the fields that you need to extract for each invoice mention and some instructions for each field:
- `number`: Return the invoice number for the invoice.
- `po_number`: Return the purchase order number if present.
- `amount`: Return the total amount in numeric format for the invoice, i.e. remove all 
non-numeric characters and make sure to handle cases where it looks like a comma is actually a decimal place. 
If the document appears to be a credit note and not an invoice, then return the number as a negative number.
- `tax_amount`: Return the total sales tax or VAT amount in numeric if it is present in the invoice, 
remove all non-numeric characters and make sure to handle cases where it looks like a comma is actually a 
decimal place.
- `currency_code`: Return the ISO 4217 three-letter currency code for this invoice if the currency is indicated, 
if it is not explicitly shown then infer the currency code for the currency of the nation indicated by the vendor's address.
- `date`: Return the invoice date for this invoice in ISO format (yyyy-mm-dd). Pay close attention to the country indicated 
by the vendor's address - if it is from the USA or Canada then assume that the date has been written in month-first date format 
and convert it to ISO format appropriately.
- `due_date`: Return the invoice due date for this invoice, if it is present, in ISO format (yyyy-mm-dd). 
Pay close attention to the country indicated by the vendor's address - if it is from the USA or Canada then 
assume that the date has been written in month-first date format and convert it to ISO format appropriately.
- `payment_term_days`: Return the number for payment term days if it is present
- `vendor`: Return the name of the business which has sent this invoice
- `line_items`: Return a list of line items, where each line item contains:
  - description: The item description
  - quantity: The quantity as a number
  - unit_price: The unit price as a number
  - total: The total amount for this line item as a number

Your response should be formatted in JSON format, with two keys in a dictionary: 
"document_type" and "invoices". 
"document_type" should contain your classification of the document, and "invoices" should be a list of 
dictionaries containing invoice details for every extracted invoice. 
Remember, if the document is not classified as 'invoice', 'reminder', or 'credit_note', "invoices" must be an empty list.

Here is an example output format for a document classified as 'invoice' containing one invoice with line items:
{
    "document_type": "invoice",
    "invoices": [{
        "number": "INV01",
        "po_number": "PO123",
        "amount": 100.00,
        "tax_amount": 10.00,
        "currency_code": "GBP",
        "date": "2024-11-09",
        "due_date": "2024-12-09",
        "payment_term_days": 30,
        "vendor": "ABC LTD",
        "line_items": [
            {
                "description": "Product A",
                "quantity": 2,
                "unit_price": 45.00,
                "total": 90.00
            }
        ]
    }]
}

Once again, make sure to return your answers in JSON format and do not return any other text in your answer."""

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 1000,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg",
                                            "data": image_base64,
                                        },
                                    },
                                ],
                            }
                        ],
                    }
                ),
            )

            # Parse the response
            response_body = json.loads(response["body"].read())
            extracted_text = response_body["content"][0]["text"]

            # Parse the JSON response
            extracted_data = json.loads(extracted_text)

            # Parse numeric values in the response
            if extracted_data.get("invoices"):
                for invoice in extracted_data["invoices"]:
                    # Parse main invoice amounts
                    invoice["amount"] = self._parse_numeric(
                        str(invoice.get("amount", "0"))
                    )
                    invoice["tax_amount"] = self._parse_numeric(
                        str(invoice.get("tax_amount", "0"))
                    )
                    invoice["payment_term_days"] = self._parse_numeric(
                        str(invoice.get("payment_term_days", "0"))
                    )

                    # Parse line items
                    if "line_items" in invoice:
                        invoice["line_items"] = self._parse_line_items(
                            invoice["line_items"]
                        )

            return extracted_data

        except Exception as e:
            print(f"Error calling Bedrock: {str(e)}")
            return None
