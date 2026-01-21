"""Step 2: Improve table structure - Correct HTML structure using LLM vision."""

import logging

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.extraction.metadata.improve_table_structure import (
    process_all_tables_structure,
)

logger = logging.getLogger(__name__)


def run_improve_table_step(
    config: PipelineConfig,
    llm_client: LitellmClient,
) -> dict:
    """
    Run table structure improvement step.

    Args:
        config: Pipeline configuration
        llm_client: LLM client for vision analysis

    Returns:
        Dictionary with step results and metrics
    """
    logger.info("=" * 60)
    logger.info("Step 2: Improve Table Structure")
    logger.info("=" * 60)

    pdf_base_path = config.pdf_base_path

    if not pdf_base_path.exists():
        return {
            "status": "error",
            "error": f"OCR output not found at {pdf_base_path}. Run OCR step first.",
        }

    logger.info(f"Improving table structures in {pdf_base_path}...")

    try:
        results = process_all_tables_structure(
            pdf_base_path, llm_client, max_pages=config.max_pages
        )

        logger.info(
            f"✅ Table structure improvement complete! "
            f"Processed: {results['tables_processed']}, "
            f"Failed: {results['tables_failed']}, "
            f"Total: {results['total_tables']}"
        )

        return {
            "status": results["status"],
            "tables_processed": results["tables_processed"],
            "tables_failed": results["tables_failed"],
            "total_tables": results["total_tables"],
        }
    except Exception as e:
        logger.error(f"❌ Table structure improvement failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }
