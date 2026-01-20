from typing import List, Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    PdfPipelineOptions,
    TableFormerMode,
)
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling_core.types.doc.document import DoclingDocument


class DoclingOCRStrategy:
    def __init__(self, **kwargs):
        # Configure pipeline options
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.do_cell_matching = True
        self.pipeline_options.ocr_options = EasyOcrOptions()
        self.pipeline_options.images_scale = 2
        self.pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        self.pipeline_options.generate_page_images = True
        self.pipeline_options.generate_picture_images = True

        # Initialize converter with pipeline options
        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
        }
        self.converter = DocumentConverter(format_options=format_options, **kwargs)

    def perform_ocr_on_pdf_docling_document(
        self, pdf_path: str, page_range: Optional[List[int]] = None
    ) -> DoclingDocument:
        if page_range is None:
            result = self.converter.convert(pdf_path)
        else:
            result = self.converter.convert(pdf_path, page_range=page_range)
        return result.document


if __name__ == "__main__":
    docling_ocr_strategy = DoclingOCRStrategy()
    content = docling_ocr_strategy.perform_ocr_on_pdf_docling_document(
        "/Users/vesaalexandru/Workspaces/cube/america/complex-rag/colpali_rag/ocr/__pycache__/AGREEMENT OF PURCHASE (analysis).docx"
    ).export_to_html()
    with open("content.html", "w") as f:
        f.write(content)
