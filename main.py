"""Main entry point for PDF processing pipeline."""

import logging
from pathlib import Path

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.pipeline import PDFProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for PDF processing pipeline."""
    # Configuration
    config = PipelineConfig(
        pdf_path=Path("data/short_complex_manual.pdf"),
        output_dir=Path("output"),
        model_name="openai/gpt-4o",
        skip_ocr_if_exists=True,
        skip_metadata_if_exists=True,
        max_pages=6,  # Limit to first 10 pages for testing (set to None to process all pages)
    )

    # Create processor and run pipeline
    processor = PDFProcessor(config)
    results = processor.run()

    # Log final status
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline execution complete!")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    main()
