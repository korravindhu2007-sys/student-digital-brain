"""OCR text extraction using Tesseract with image preprocessing."""

from pathlib import Path
from typing import Tuple

from src.config import config
from src.utils.exceptions import OCRError
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class OCRProcessor:
    """Extract text from images using Tesseract OCR with preprocessing."""

    def __init__(self) -> None:
        self.tesseract_cmd = config.ocr.tesseract_cmd

    def _check_tesseract(self) -> None:
        """Verify Tesseract is installed and accessible."""
        import shutil

        if not shutil.which(self.tesseract_cmd):
            raise OCRError(
                f"Tesseract not found at '{self.tesseract_cmd}'. "
                "Please install Tesseract OCR and ensure it is in your PATH."
            )

    def preprocess_image(self, image_path: Path) -> object:
        """Apply preprocessing to improve OCR accuracy.

        Steps: grayscale, binarization (OTSU), denoising, deskewing.

        Args:
            image_path: Path to the input image.

        Returns:
            Preprocessed image array (numpy array).
        """
        try:
            import cv2
            import numpy as np
        except ImportError:
            logger.warning("OpenCV not installed; skipping image preprocessing")
            return None

        img = cv2.imread(str(image_path))
        if img is None:
            raise OCRError(
                f"Failed to read image: {image_path}",
                image_path=str(image_path),
            )

        # 1. Grayscale conversion
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Binarization using OTSU threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 3. Denoising
        denoised = cv2.fastNlMeansDenoising(binary, h=30)

        # 4. Deskewing
        coords = np.column_stack(np.where(denoised > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = 90 + angle
            if abs(angle) > 0.5:
                h, w = denoised.shape
                center = (w // 2, h // 2)
                matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(
                    denoised,
                    matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )

        logger.debug("Image preprocessed: %s", image_path.name)
        return denoised

    def extract_text(
        self,
        image_path: Path,
        preprocess: bool = True,
        image_type: str = "printed",
    ) -> str:
        """Extract text from an image using OCR.

        Args:
            image_path: Path to the image file.
            preprocess: Whether to apply image preprocessing.
            image_type: 'printed', 'handwritten', 'whiteboard', or 'screenshot'.

        Returns:
            Extracted text string.

        Raises:
            OCRError: If OCR processing fails.
        """
        try:
            import pytesseract
        except ImportError:
            raise OCRError("pytesseract is not installed. Install with: pip install pytesseract")

        self._check_tesseract()
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        # Build Tesseract configuration
        # PSM modes: 6=block, 3=auto, 4=single column, 7=single line
        psm_map = {
            "printed": 6,
            "handwritten": 6,
            "whiteboard": 3,
            "screenshot": 6,
        }
        psm = psm_map.get(image_type, 6)

        tess_config = (
            f"--oem {config.ocr.oem_mode} "
            f"--psm {psm} "
            f"-l {config.ocr.language} "
            f"--dpi {config.ocr.dpi}"
        )

        try:
            if preprocess and config.ocr.preprocessing_enabled:
                processed_img = self.preprocess_image(image_path)
                if processed_img is not None:
                    text = pytesseract.image_to_string(processed_img, config=tess_config)
                else:
                    text = pytesseract.image_to_string(str(image_path), config=tess_config)
            else:
                text = pytesseract.image_to_string(str(image_path), config=tess_config)

            cleaned = text.strip()
            char_count = len(cleaned)
            logger.info(
                "OCR extracted %d characters from %s (type=%s)",
                char_count,
                image_path.name,
                image_type,
            )
            return cleaned

        except pytesseract.TesseractError as e:
            raise OCRError(
                f"Tesseract OCR failed: {e}",
                image_path=str(image_path),
            )
        except Exception as e:
            raise OCRError(
                f"OCR processing error: {e}",
                image_path=str(image_path),
            )

    def extract_text_with_confidence(
        self,
        image_path: Path,
        preprocess: bool = True,
        image_type: str = "printed",
    ) -> Tuple[str, float]:
        """Extract text with confidence score.

        Args:
            image_path: Path to the image.
            preprocess: Whether to preprocess.
            image_type: Type of image.

        Returns:
            Tuple of (text: str, confidence: float 0-100).
        """
        try:
            import pytesseract
        except ImportError:
            raise OCRError("pytesseract is not installed.")

        self._check_tesseract()
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        psm_map = {
            "printed": 6,
            "handwritten": 6,
            "whiteboard": 3,
            "screenshot": 6,
        }
        tess_config = (
            f"--oem {config.ocr.oem_mode} "
            f"--psm {psm_map.get(image_type, 6)} "
            f"-l {config.ocr.language} --dpi {config.ocr.dpi}"
        )

        try:
            data = pytesseract.image_to_data(
                str(image_path), config=tess_config, output_type=pytesseract.Output.DICT
            )
            confidences = [int(c) for c in data["conf"] if c != "-1" and int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            text = " ".join(
                data["text"][i] for i in range(len(data["text"])) if data["text"][i].strip()
            )
            return text.strip(), avg_confidence

        except Exception as e:
            raise OCRError(
                f"OCR confidence extraction failed: {e}",
                image_path=str(image_path),
            )
