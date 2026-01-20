"""Main PDF processing pipeline orchestrator."""

import logging
from typing import Dict, List, Optional

from complex_pdf.config.pipeline_config import PipelineConfig
from complex_pdf.core.llm.litellm_client import LitellmClient
from complex_pdf.pipeline.steps import (
    run_context_step,
    run_enhance_step,
    run_ocr_step,
    run_table_step,
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Orchestrates the PDF processing pipeline."""

    def __init__(self, config: PipelineConfig):
        """
        Initialize PDF processor.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.llm_client = LitellmClient(model_name=config.model_name)
        self.results: Dict[str, Dict] = {}

    def run(self, steps: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Run the PDF processing pipeline.

        Args:
            steps: Optional list of step names to run. If None, runs all steps.
                  Valid step names: 'ocr', 'context', 'enhance', 'table', 'test'

        Returns:
            Dictionary containing results from each step
        """
        logger.info("=" * 60)
        logger.info("PDF Processing Pipeline")
        logger.info("=" * 60)
        logger.info(f"PDF: {self.config.pdf_path}")
        logger.info(f"Output: {self.config.output_dir}")
        logger.info(f"Model: {self.config.model_name}")
        logger.info("=" * 60)

        # Define all available steps
        all_steps = {
            "ocr": ("OCR Extraction", run_ocr_step),
            "context": ("Context Metadata", run_context_step),
            "enhance": ("Enhance Metadata", run_enhance_step),
            "table": ("Table Metadata", run_table_step),
        }

        # Determine which steps to run
        if steps is None:
            steps_to_run = list(all_steps.keys())
        else:
            # Validate step names
            invalid_steps = [s for s in steps if s not in all_steps]
            if invalid_steps:
                raise ValueError(
                    f"Invalid step names: {invalid_steps}. "
                    f"Valid steps: {list(all_steps.keys())}"
                )
            steps_to_run = steps

        logger.info(f"Running steps: {', '.join(steps_to_run)}")

        # Execute each step
        for step_name in steps_to_run:
            step_title, step_func = all_steps[step_name]
            try:
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Starting: {step_title}")
                logger.info(f"{'=' * 60}")

                result = step_func(self.config, self.llm_client)
                self.results[step_name] = result

                if result.get("status") == "error":
                    logger.error(
                        f"Step '{step_name}' failed. Continuing with next step..."
                    )
                else:
                    logger.info(f"Step '{step_name}' completed successfully")

            except Exception as e:
                logger.error(
                    f"Step '{step_name}' raised an exception: {e}",
                    exc_info=True,
                )
                self.results[step_name] = {
                    "status": "error",
                    "error": str(e),
                }

        # Print cost summary
        self._print_cost_summary()

        # Print final summary
        self._print_final_summary()

        return self.results

    def _print_cost_summary(self):
        """Print cost tracking summary."""
        cost_summary = self.llm_client.get_cost_summary()
        logger.info("\n" + "=" * 60)
        logger.info("Cost Summary")
        logger.info("=" * 60)
        logger.info(f"Total Cost: ${cost_summary['total_cost']:.6f}")
        logger.info(f"Total Tokens: {cost_summary['total_tokens']:,}")
        logger.info(
            f"  Prompt: {cost_summary['total_prompt_tokens']:,} | "
            f"Completion: {cost_summary['total_completion_tokens']:,}"
        )
        logger.info(f"Total API Calls: {cost_summary['call_count']}")

        if cost_summary["cost_breakdown"]:
            logger.info("\nCost Breakdown by Call Type:")
            for entry in cost_summary["cost_breakdown"]:
                logger.info(
                    f"  {entry['call_type']}: ${entry['cost']:.6f} "
                    f"({entry['total_tokens']} tokens)"
                )

    def _print_final_summary(self):
        """Print final pipeline summary."""
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline Summary")
        logger.info("=" * 60)

        for step_name, result in self.results.items():
            status = result.get("status", "unknown")
            status_icon = (
                "✅" if status == "success" else "❌" if status == "error" else "⏭️"
            )
            logger.info(f"{status_icon} {step_name}: {status}")

        logger.info("=" * 60)
