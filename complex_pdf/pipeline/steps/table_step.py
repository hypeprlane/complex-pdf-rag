"""Step 4: Table metadata - Generate detailed metadata for tables."""

import logging

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.metadata.extract_table_metadata import process_all_tables

logger = logging.getLogger(__name__)


def run_table_step(
    config: PipelineConfig,
    llm_client: LitellmClient,
) -> dict:
    """
    Run table metadata extraction step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client for generating table metadata

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 4: Table Metadata Extraction")
    logger.info("=" * 60)

    pdf_base_path = config.pdf_base_path

    if not pdf_base_path.exists():
        return {
            "status": "error",
            "error": f"OCR output not found at {pdf_base_path}. Run OCR step first.",
        }

    logger.info(f"Processing tables in {pdf_base_path}...")

    try:
        # The process_all_tables function uses its own LitellmClient
        # We need to modify it or create a wrapper, but for now let's use it as-is
        # and note that it creates its own client
        logger.warning(
            "Note: process_all_tables creates its own LLM client. "
            "Cost tracking will be separate."
        )

        process_all_tables(scratch_path=pdf_base_path, max_pages=config.max_pages)

        # Count pages with tables
        pages_with_tables = 0
        total_tables = 0

        for page_dir in pdf_base_path.glob("page_*"):
            if not page_dir.is_dir():
                continue

            context_file = (
                page_dir / f"context_metadata_page_{page_dir.name.split('_')[1]}.json"
            )
            if context_file.exists():
                import json

                with open(context_file, "r") as f:
                    context_metadata = json.load(f)
                    if context_metadata.get("has_tables", False):
                        pages_with_tables += 1
                        table_metadata = context_metadata.get("table_metadata", [])
                        total_tables += len(table_metadata)

        logger.info(
            f"✅ Table metadata extraction complete! "
            f"Pages with tables: {pages_with_tables}, Total tables: {total_tables}"
        )

        return {
            "status": "success",
            "pages_with_tables": pages_with_tables,
            "total_tables": total_tables,
        }
    except Exception as e:
        logger.error(f"❌ Table metadata extraction failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
