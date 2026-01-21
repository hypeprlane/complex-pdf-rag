"""Step 6: Image metadata - Generate detailed metadata for images and diagrams."""

import logging

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.metadata.extract_image_metadata import (
    process_all_images,
)

logger = logging.getLogger(__name__)


def run_image_step(
    config: PipelineConfig,
    llm_client: LitellmClient,
) -> dict:
    """
    Run image metadata extraction step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client for vision analysis

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 6: Image Metadata Extraction")
    logger.info("=" * 60)

    pdf_base_path = config.pdf_base_path

    if not pdf_base_path.exists():
        return {
            "status": "error",
            "error": f"OCR output not found at {pdf_base_path}. Run OCR step first.",
        }

    logger.info(f"Processing images in {pdf_base_path}...")

    try:
        results = process_all_images(
            pdf_base_path, llm_client, max_pages=config.max_pages
        )

        logger.info(
            f"✅ Image metadata extraction complete! "
            f"Processed: {results['images_processed']}, "
            f"Failed: {results['images_failed']}, "
            f"Total: {results['total_images']}"
        )

        return {
            "status": results["status"],
            "images_processed": results["images_processed"],
            "images_failed": results["images_failed"],
            "total_images": results["total_images"],
        }
    except Exception as e:
        logger.error(f"❌ Image metadata extraction failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
