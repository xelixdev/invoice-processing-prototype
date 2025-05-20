import fitz
import numpy as np
import cv2
import base64
from typing import Optional
from dataclasses import dataclass
from time import time

@dataclass
class PDFPageImage:
    data: bytes
    width: int
    height: int
    applied_rotation: float
    elapsed_time: float

def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """Convert bytes to OpenCV image format."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def cv2_to_bytes(image: np.ndarray) -> bytes:
    """Convert OpenCV image to bytes."""
    _, buffer = cv2.imencode('.jpg', image)
    return buffer.tobytes()

def extract_image_page_bytes(page: fitz.Page, zoom: float = 2.0) -> bytes:
    """Extract image from PDF page."""
    return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).pil_tobytes(format="JPEG", optimize=True)

def preprocess_pdf_page_image(
    source_image: np.ndarray,
    pre_defined_rotation: Optional[float] = None,
    is_structured: bool = True,
) -> PDFPageImage:
    """Preprocess the image for optimal processing."""
    start_time = time()
    source_image = np.copy(source_image)
    img_height, img_width, *_ = source_image.shape

    # For now, we'll keep it simple and just return the image as is
    # We can add more preprocessing steps later if needed
    page = source_image
    page_rotation = 0
    data = cv2_to_bytes(page)
    page_height, page_width, *_ = page.shape

    return PDFPageImage(
        data=data,
        width=page_width,
        height=page_height,
        applied_rotation=page_rotation,
        elapsed_time=time() - start_time,
    )

def get_image_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    """Convert PDF to base64 encoded image."""
    try:
        with fitz.Document(stream=pdf_bytes, filetype="pdf") as doc:
            # Get the first page
            page = doc[0]
            # Extract image
            image_bytes = extract_image_page_bytes(page)
            # Convert to OpenCV format
            cv_image = bytes_to_cv2(image_bytes)
            # Preprocess
            processed_image = preprocess_pdf_page_image(cv_image)
            # Convert to base64
            return base64.b64encode(processed_image.data).decode("utf-8")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None 