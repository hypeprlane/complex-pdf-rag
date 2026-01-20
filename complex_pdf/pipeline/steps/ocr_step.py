"""Step 1: OCR extraction - Extract tables, figures, and text from PDF."""

import logging

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.extract_images_tables import export_figures_tables_and_text

logger = logging.getLogger(__name__)


def run_ocr_step(
    config: PipelineConfig,
    llm_client: LitellmClient,  # Not used but kept for consistency
) -> dict:
    """
    Run OCR extraction step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client (not used in this step but kept for consistency)

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 1: OCR Extraction")
    logger.info("=" * 60)

    pdf_base_path = config.pdf_base_path

    # Check if we should skip (if output already exists)
    if config.skip_ocr_if_exists and pdf_base_path.exists():
        # Check if at least one page directory exists
        page_dirs = list(pdf_base_path.glob("page_*"))
        if page_dirs:
            logger.info(
                f"Skipping OCR extraction - output already exists at {pdf_base_path}"
            )
            return {
                "status": "skipped",
                "message": "OCR output already exists",
                "output_path": str(pdf_base_path),
            }

    logger.info(f"Extracting from PDF: {config.pdf_path}")
    logger.info(f"Output directory: {config.output_dir}")

    try:
        export_figures_tables_and_text(
            pdf_path=str(config.pdf_path), output_dir=str(config.output_dir)
        )

        # Count pages processed
        page_count = len(list(pdf_base_path.glob("page_*")))

        logger.info(f"✅ OCR extraction complete! Processed {page_count} pages")
        return {
            "status": "success",
            "pages_processed": page_count,
            "output_path": str(pdf_base_path),
        }
    except Exception as e:
        logger.error(f"❌ OCR extraction failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
