import anthropic
import json
import os
from typing import Dict, Any
from decimal import Decimal
from prompts import INVOICE_EXTRACTION_PROMPT
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AnthropicClient:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables. Please set it in your .env file.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20240620"

    def _parse_numeric(self, value: str) -> float:
        """Parse numeric values from strings, handling various formats."""
        if not value or not isinstance(value, str):
            return 0.0
        try:
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
                if field in parsed_item and parsed_item[field] is not None:
                    parsed_item[field] = self._parse_numeric(str(parsed_item[field]))
                else:
                    # Handle cases where a numeric field might be missing or None
                    parsed_item[field] = 0.0 # Default to 0.0 or handle as appropriate
            parsed_items.append(parsed_item)
        return parsed_items

    def extract_invoice_data(self, image_base64_list: list[str]) -> Dict[str, Any]:
        """Extract invoice data from a list of images using Anthropic's Claude."""
        try:
            # Construct the content list with multiple images and the prompt
            content_list = []
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
            content_list.append({"type": "text", "text": INVOICE_EXTRACTION_PROMPT})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096, # Increased max_tokens for potentially longer multi-page documents
                messages=[
                    {
                        "role": "user",
                        "content": content_list, # Use the constructed content list
                    }
                ],
            )

            if response.content and isinstance(response.content, list) and len(response.content) > 0:
                extracted_text = response.content[0].text
            else:
                print("Error: Unexpected response structure from Anthropic API.")
                return None
                
            extracted_data = json.loads(extracted_text)

            if "invoices" in extracted_data:
                for invoice in extracted_data["invoices"]:
                    invoice["amount"] = self._parse_numeric(str(invoice.get("amount", "0")))
                    invoice["tax_amount"] = self._parse_numeric(str(invoice.get("tax_amount", "0")))
                    invoice["payment_term_days"] = self._parse_numeric(str(invoice.get("payment_term_days", "0")))
                    if "line_items" in invoice and isinstance(invoice["line_items"], list):
                        invoice["line_items"] = self._parse_line_items(invoice["line_items"])
                    else:
                        invoice["line_items"] = []
            else:
                 extracted_data["invoices"] = []

            return extracted_data

        except anthropic.APIStatusError as e:
            print(f"Anthropic API returned an error: {e.status_code} - {e.message}")
            return None
        except anthropic.APIConnectionError as e:
            print(f"Failed to connect to Anthropic API: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Anthropic response: {e}")
            print(f"Raw response text: {extracted_text if 'extracted_text' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred in Anthropic client: {str(e)}")
            return None 