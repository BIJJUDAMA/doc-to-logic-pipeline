"""
File description: MinerU-based document parsing pipeline
Purpose: Provides a wrapper logic around MinerU to extract layout, text, tables, and images from PDFs
How it works: Initializes MinerU dataset mapping, branches into OCR or text mode based on PDF type, and standardizes output into a list of contents
"""
import os
import uuid
from dataclasses import asdict, is_dataclass
from typing import Dict, Any

from src.parsing.utils import setup_logger

logger = setup_logger(__name__)


def _to_jsonable(value: Any) -> Any:
    # Helper recursive function to serialize complex object types to basic JSON structures
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _to_jsonable(model_dump())
    to_dict = getattr(value, "dict", None)
    if callable(to_dict):
        return _to_jsonable(to_dict())
    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))
    return str(value)

class Pipeline:
    # Core pipeline class managing layout analysis routines
    def __init__(self):
        

        pass

    def miner_u_parse(self, pdf_path: str) -> Dict[str, Any]:
        # Parses a PDF document and extracts its structured formatting

        from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.config.enums import SupportedPdfParseMethod

        logger.info(f"MinerU Parsing: {os.path.basename(pdf_path)}")
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(pdf_path)
        

        image_writer = FileBasedDataWriter("/tmp/mineru_images")
        
        ds = PymuDocDataset(pdf_bytes)
        

        if ds.classify() == SupportedPdfParseMethod.OCR:
            # Branch OCR processing mode
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            # Branch direct text extraction mode
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)
            

        content_list = []
        if hasattr(pipe_result, "get_content_list"):
            content_list = pipe_result.get_content_list("")
        else:

            logger.warning(f"pipe_result missing get_content_list. Available: {dir(pipe_result)}")

            if hasattr(pipe_result, "get_markdown"):
                content_list = [pipe_result.get_markdown("")]
        
        return {
            "source": os.path.basename(pdf_path),
            "doc_id": str(uuid.uuid4()),
            "content_list": _to_jsonable(content_list) # Return normalized layout list
        }
