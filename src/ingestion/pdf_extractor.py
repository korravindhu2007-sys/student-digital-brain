"""PDF text and image extraction using PyMuPDF."""

from pathlib import Path
from typing import Dict, List

from src.utils.exceptions import PDFExtractionError
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


def is_pdf_encrypted(file_path: Path) -> bool:
    """Return True if the PDF is encrypted or requires a password."""
    try:
        import fitz
        doc = fitz.open(str(file_path))
        try:
            return bool(doc.needs_pass)
        finally:
            doc.close()
    except Exception:
        return False


def validate_pdf(file_path: Path) -> bool:
    """Basic PDF validation: check it can be opened and has pages."""
    try:
        import fitz
        doc = fitz.open(str(file_path))
        try:
            return doc.page_count > 0
        finally:
            doc.close()
    except Exception:
        return False


class PDFExtractor:
    """Extract text and images from PDF documents using PyMuPDF."""

    def __init__(self, file_path: Path) -> None:
        """Initialize PDF extractor.

        Args:
            file_path: Path to the PDF file.
        """
        self.file_path = file_path
        self._document = None

    def extract_text(self) -> List[Dict[str, object]]:
        """Extract text from all pages.

        Returns:
            List of dicts with 'page', 'text', and 'char_count' per page.

        Raises:
            PDFExtractionError: If extraction fails.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise PDFExtractionError(
                "PyMuPDF (fitz) is not installed. Install with: pip install PyMuPDF"
            )

        pages = []
        try:
            self._document = fitz.open(str(self.file_path))
            for page_num in range(len(self._document)):
                page = self._document[page_num]
                text = page.get_text()
                pages.append(
                    {
                        "page": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                    }
                )
                logger.debug(
                    "Extracted page %d: %d characters",
                    page_num + 1,
                    len(text),
                )
            return pages

        except fitz.FileDataError as e:
            raise PDFExtractionError(
                f"Corrupted or invalid PDF file: {e}",
                document_id=None,
            )
        except Exception as e:
            raise PDFExtractionError(
                f"Failed to extract PDF text: {e}",
                document_id=None,
            )
        finally:
            if self._document:
                self._document.close()

    def extract_images(self) -> List[Dict[str, object]]:
        """Extract embedded images from PDF pages.

        Returns:
            List of dicts with 'page', 'image_index', 'width', 'height',
            and 'image_bytes' for each image found.
        """
        try:
            import fitz
        except ImportError:
            raise PDFExtractionError("PyMuPDF (fitz) is not installed.")

        images = []
        try:
            self._document = fitz.open(str(self.file_path))
            for page_num in range(len(self._document)):
                page = self._document[page_num]
                image_list = page.get_images(full=True)

                for img_idx, img in enumerate(image_list):
                    xref = img[0]
                    base_image = self._document.extract_image(xref)
                    image_bytes = base_image["image"]
                    images.append(
                        {
                            "page": page_num + 1,
                            "image_index": img_idx,
                            "width": base_image["width"],
                            "height": base_image["height"],
                            "image_bytes": image_bytes,
                            "extension": base_image["ext"],
                        }
                    )
                    logger.debug(
                        "Extracted image %d from page %d (%dx%d)",
                        img_idx,
                        page_num + 1,
                        base_image["width"],
                        base_image["height"],
                    )
            return images

        except Exception as e:
            raise PDFExtractionError(f"Failed to extract PDF images: {e}")
        finally:
            if self._document:
                self._document.close()

    def get_metadata(self) -> Dict[str, object]:
        """Get PDF document metadata.

        Returns:
            Dict with title, author, subject, page_count, etc.
        """
        try:
            import fitz
        except ImportError:
            raise PDFExtractionError("PyMuPDF (fitz) is not installed.")

        try:
            self._document = fitz.open(str(self.file_path))
            metadata = self._document.metadata or {}
            return {
                "title": metadata.get("title", self.file_path.stem),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "page_count": len(self._document),
                "file_size": self.file_path.stat().st_size,
                "format": metadata.get("format", ""),
            }
        except Exception as e:
            raise PDFExtractionError(f"Failed to get PDF metadata: {e}")
        finally:
            if self._document:
                self._document.close()

    def extract_all_text(self) -> str:
        """Extract all text from the PDF as a single string.

        Returns:
            Concatenated text from all pages.
        """
        pages = self.extract_text()
        return "\n\n".join(page["text"] for page in pages)
