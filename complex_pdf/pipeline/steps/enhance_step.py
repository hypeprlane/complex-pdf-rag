"""Step 3: Enhance metadata - Add has_tables/has_figures flags to context metadata."""

import logging

import fitz

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.core.utils import enhance_context_metadata_file

logger = logging.getLogger(__name__)


def run_enhance_step(
    config: PipelineConfig,
    llm_client: LitellmClient,  # Not used but kept for consistency
) -> dict:
    """
    Run metadata enhancement step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client (not used but kept for consistency)

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 3: Enhance Metadata")
    logger.info("=" * 60)

    pdf_base_path = config.pdf_base_path

    if not pdf_base_path.exists():
        return {
            "status": "error",
            "error": f"OCR output not found at {pdf_base_path}. Run OCR step first.",
        }

    # Get total page count from PDF
    with fitz.open(config.pdf_path) as pdf_doc:
        total_pages = pdf_doc.page_count

    logger.info(f"Enhancing metadata for {total_pages} pages...")

    enhanced = 0
    skipped = 0
    failed = 0

    for page_num in range(1, total_pages + 1):
        page_dir = pdf_base_path / f"page_{page_num}"
        if not page_dir.exists():
            logger.warning(f"Page {page_num} directory not found, skipping")
            skipped += 1
            continue

        context_metadata_path = page_dir / f"context_metadata_page_{page_num}.json"
        basic_metadata_path = page_dir / f"metadata_page_{page_num}.json"

        # Check if both files exist
        if not context_metadata_path.exists():
            logger.warning(
                f"Context metadata not found for page {page_num}, skipping enhancement"
            )
            skipped += 1
            continue

        if not basic_metadata_path.exists():
            logger.warning(
                f"Basic metadata not found for page {page_num}, skipping enhancement"
            )
            skipped += 1
            continue

        try:
            # Enhance the metadata
            enhance_context_metadata_file(
                context_metadata_path=context_metadata_path,
                basic_metadata_path=basic_metadata_path,
            )
            logger.debug(f"✅ Enhanced metadata for page {page_num}")
            enhanced += 1
        except Exception as e:
            logger.error(
                f"❌ Failed to enhance metadata for page {page_num}: {e}",
                exc_info=True,
            )
            failed += 1

    logger.info(
        f"✅ Metadata enhancement complete! "
        f"Enhanced: {enhanced}, Skipped: {skipped}, Failed: {failed}"
    )

    return {
        "status": "success",
        "pages_enhanced": enhanced,
        "pages_skipped": skipped,
        "pages_failed": failed,
        "total_pages": total_pages,
    }
