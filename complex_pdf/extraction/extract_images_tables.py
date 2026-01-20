import json
import logging
from pathlib import Path

import fitz
from docling.datamodel.document import PictureItem, TextItem

from complex_pdf.core.ocr.docling_ocr import DoclingOCRStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def export_figures_tables_and_text(
    pdf_path: str,
    output_dir: str = "scratch",
):
    logger.info(f"Starting extraction from PDF: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")

    ocr_strategy = DoclingOCRStrategy()

    with fitz.open(pdf_path) as pdf_doc:
        total_pages = pdf_doc.page_count
        logger.info(f"Total pages: {total_pages}")

    for page_num in range(1, total_pages + 1):
        logger.info(f"Processing page {page_num}")
        doc = ocr_strategy.perform_ocr_on_pdf_docling_document(
            pdf_path, page_range=[page_num, page_num]
        )

        doc_name = Path(pdf_path).stem
        output_path = Path(output_dir) / doc_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Create page folder
        page_folder = output_path / f"page_{page_num}"
        tables_folder = page_folder / "tables"
        images_folder = page_folder / "images"
        text_folder = page_folder / "text"
        tables_folder.mkdir(parents=True, exist_ok=True)
        images_folder.mkdir(parents=True, exist_ok=True)
        text_folder.mkdir(parents=True, exist_ok=True)

        metadata = {
            "page_number": page_num,
            "page_image": f"page_{page_num}_full.png",
            "tables": [],
            "figures": [],
            "text_blocks": [],
        }

        # Save full page as image
        with fitz.open(pdf_path) as pdf_doc:
            page = pdf_doc[page_num - 1]  # 0-indexed
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            full_page_file = page_folder / f"page_{page_num}_full.png"
            pix.save(str(full_page_file))
            logger.info(f"Saved full page: {full_page_file}")

        # Export tables
        logger.info(f"Found {len(doc.tables)} tables on page {page_num}")
        page_table_idx = 0
        for table in doc.tables:
            page_table_idx += 1
            table_id = f"table-{page_num}-{page_table_idx}"
            metadata["tables"].append(table_id)

            logger.info(f"Exporting {table_id}")
            html = table.export_to_html(doc=doc)
            html_file = tables_folder / f"{table_id}.html"
            html_file.write_text(html)
            logger.info(f"Saved table HTML: {html_file}")

            img = table.get_image(doc)
            png_file = tables_folder / f"{table_id}.png"
            img.save(png_file, "PNG")
            logger.info(f"Saved table PNG: {png_file}")

        # Export figures
        # Export figures
        logger.info(f"Starting figure extraction for page {page_num}...")
        page_figure_idx = 0
        for item, _ in doc.iterate_items():
            if isinstance(item, PictureItem):
                img = item.get_image(doc)
                width, height = img.size
                area = width * height

                # Filter out icons/small images
                if area < 400:
                    logger.info(
                        f"Skipping image on page {page_num} due to small size or icon-like shape."
                    )
                    continue

                page_figure_idx += 1
                image_id = f"image-{page_num}-{page_figure_idx}"
                metadata["figures"].append(image_id)

                logger.info(f"Exporting {image_id}")
                img_file = images_folder / f"{image_id}.png"
                img.save(img_file, "PNG")
                logger.info(f"Saved image: {img_file}")

        # Export text blocks
        logger.info(f"Starting text extraction for page {page_num}...")
        page_text_blocks = []
        text_block_count = 0

        for item, _ in doc.iterate_items():
            if isinstance(item, TextItem):
                text_block_count += 1
                text_content = item.text if hasattr(item, "text") else str(item)
                page_text_blocks.append(text_content)

        if page_text_blocks:
            unified_text = "\n\n".join(page_text_blocks)
            txt_file = text_folder / f"page_{page_num}_text.txt"
            txt_file.write_text(unified_text, encoding="utf-8")
            metadata["text_blocks"].append(txt_file.name)
            logger.info(
                f"Saved unified text file: {txt_file} ({text_block_count} blocks)"
            )
        else:
            logger.info(f"No text blocks found on page {page_num}")

        # Save metadata for the page
        metadata_file = page_folder / f"metadata_page_{page_num}.json"
        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved page metadata: {metadata_file}")

        logger.info(
            f"Page {page_num} complete! Exported {page_table_idx} tables, {page_figure_idx} figures, {text_block_count} text blocks"
        )

    logger.info("All pages processed successfully!")


def export_figures_and_tables(
    pdf_path: str,
    output_dir: str = "scratch",
):
    return export_figures_tables_and_text(pdf_path, output_dir)


if __name__ == "__main__":
    pdf_path = "/Users/vesaalexandru/Workspaces/cube/complex-pdf-rag/data/short_complex_manual.pdf"
    export_figures_tables_and_text(pdf_path, output_dir="output")
