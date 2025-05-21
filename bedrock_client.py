import boto3
import json
import os
from typing import Dict, Any
from decimal import Decimal
from prompts import INVOICE_EXTRACTION_PROMPT

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

    def extract_invoice_data(self, image_base64_list: list[str]) -> Dict[str, Any]:
        """
        Extract invoice data using AWS Bedrock's Claude model from a list of images.

        Args:
            image_base64_list (list[str]): List of base64 encoded images of the invoice pages

        Returns:
            Dict[str, Any]: Extracted invoice data
        """
        try:
            # Construct the content list with multiple images and the prompt
            content_list = []
            # The prompt text should come first for Claude via Bedrock according to some examples
            content_list.append({"type": "text", "text": INVOICE_EXTRACTION_PROMPT})
            for image_data in image_base64_list:
                content_list.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    }
                )

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4096,  # Increased max_tokens
                        "messages": [
                            {
                                "role": "user",
                                "content": content_list,  # Use the constructed content list
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
                    invoice["amount"] = self._parse_numeric(str(invoice.get("amount", "0")))
                    invoice["tax_amount"] = self._parse_numeric(str(invoice.get("tax_amount", "0")))
                    invoice["payment_term_days"] = self._parse_numeric(str(invoice.get("payment_term_days", "0")))

                    # Parse line items
                    if "line_items" in invoice:
                        invoice["line_items"] = self._parse_line_items(invoice["line_items"])

            return extracted_data

        except Exception as e:
            print(f"Error calling Bedrock: {str(e)}")
            return None
