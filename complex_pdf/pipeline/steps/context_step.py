"""Step 2: Context metadata extraction - Generate rich metadata using LLM vision."""

import logging

import fitz

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.metadata.extract_page_context import (
    extract_and_save_context_metadata,
)

logger = logging.getLogger(__name__)


def run_context_step(
    config: PipelineConfig,
    llm_client: LitellmClient,
) -> dict:
    """
    Run context metadata extraction step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client for generating metadata

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 2: Context Metadata Extraction")
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

    # Determine how many pages to process
    if config.max_pages is not None:
        pages_to_check = min(config.max_pages, total_pages)
        logger.info(
            f"Processing {pages_to_check} pages for context metadata "
            f"(limited from {total_pages} total pages)"
        )
    else:
        pages_to_check = total_pages
        logger.info(f"Processing {total_pages} pages for context metadata...")

    # Count pages that already have context metadata
    pages_with_metadata = 0
    pages_to_process = []

    for page_num in range(1, pages_to_check + 1):
        context_metadata_path = (
            pdf_base_path
            / f"page_{page_num}"
            / f"context_metadata_page_{page_num}.json"
        )
        if context_metadata_path.exists() and config.skip_metadata_if_exists:
            pages_with_metadata += 1
        else:
            pages_to_process.append(page_num)

    if pages_with_metadata > 0:
        logger.info(f"Found {pages_with_metadata} pages with existing context metadata")

    if not pages_to_process:
        logger.info("All pages already have context metadata. Skipping.")
        return {
            "status": "skipped",
            "message": "All pages already have context metadata",
            "pages_processed": total_pages,
        }

    logger.info(f"Processing {len(pages_to_process)} pages...")

    successful = 0
    failed = 0

    for page_num in pages_to_process:
        try:
            logger.info(f"Processing page {page_num}/{total_pages}...")
            context_metadata_path = extract_and_save_context_metadata(
                litellm_client=llm_client,
                page_number=page_num,
                pdf_base_path=pdf_base_path,
            )
            logger.info(f"✅ Page {page_num} metadata saved to {context_metadata_path}")
            successful += 1
        except Exception as e:
            logger.error(f"❌ Failed to process page {page_num}: {e}", exc_info=True)
            failed += 1

    logger.info(
        f"✅ Context metadata extraction complete! "
        f"Success: {successful}, Failed: {failed}, Skipped: {pages_with_metadata}"
    )

    return {
        "status": "success",
        "pages_processed": successful,
        "pages_failed": failed,
        "pages_skipped": pages_with_metadata,
        "total_pages": total_pages,
    }
