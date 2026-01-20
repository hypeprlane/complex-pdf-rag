"""Configuration for PDF processing pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    """Configuration for PDF processing pipeline."""

    pdf_path: Path
    output_dir: Path
    model_name: str = "openai/gpt-4o"
    skip_ocr_if_exists: bool = True
    skip_metadata_if_exists: bool = True

    def __post_init__(self):
        """Validate and normalize paths."""
        if isinstance(self.pdf_path, str):
            self.pdf_path = Path(self.pdf_path)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def pdf_base_path(self) -> Path:
        """Get the base path for processed PDF output (output_dir/pdf_name)."""
        return self.output_dir / self.pdf_path.stem
