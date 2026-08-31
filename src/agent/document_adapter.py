import io
import os
import json
import base64
import mimetypes
from typing import Dict, Any, List, Tuple, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from PIL import Image
except ImportError:
    Image = None

from google import genai
from google.genai import types
from src.agent.credentials import CredentialManager, RetrySignal

class DocumentProcessingError(Exception):
    """Raised when an uploaded document cannot be read or parsed safely."""
    pass

class DocumentAdapter:
    """
    Adapter that normalizes real-world supplier documents (PDF, PNG, JPG, JPEG, JSON)
    into the existing evidence representation used by AgentOrchestrator.
    """
    SUPPORTED_EXTENSIONS = {".json", ".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(self, credential_manager: Optional[CredentialManager] = None):
        self.cred_manager = credential_manager or CredentialManager()

    def process_file(self, filename: str, content_bytes: bytes, mime_type: Optional[str] = None) -> str:
        """
        Processes a single file and extracts its readable text/evidence content.
        """
        if not content_bytes or len(content_bytes) == 0:
            raise DocumentProcessingError(f"File '{filename}' is empty.")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise DocumentProcessingError(
                f"Unsupported file format '{ext}' for '{filename}'. "
                f"Supported formats are: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        if ext == ".json":
            return self._process_json(filename, content_bytes)
        elif ext == ".pdf":
            return self._process_pdf(filename, content_bytes)
        elif ext in {".png", ".jpg", ".jpeg"}:
            return self._process_image(filename, content_bytes, mime_type)
        else:
            raise DocumentProcessingError(f"Unhandled file extension: {ext}")

    def _process_json(self, filename: str, content_bytes: bytes) -> str:
        try:
            text = content_bytes.decode("utf-8")
            # Validate JSON syntax
            json.loads(text)
            return text
        except UnicodeDecodeError as e:
            raise DocumentProcessingError(f"Invalid text encoding in JSON file '{filename}': {e}") from e
        except json.JSONDecodeError as e:
            raise DocumentProcessingError(f"Invalid JSON syntax in '{filename}': {e}") from e

    def _process_pdf(self, filename: str, content_bytes: bytes) -> str:
        # Check PDF header magic bytes
        if not content_bytes.startswith(b"%PDF"):
            raise DocumentProcessingError(f"File '{filename}' is not a valid PDF document (missing PDF magic header).")

        extracted_text = []

        # 1. Try PyMuPDF (fitz)
        if fitz:
            try:
                doc = fitz.open(stream=content_bytes, filetype="pdf")
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    t = page.get_text()
                    if t.strip():
                        extracted_text.append(f"--- Page {page_num + 1} ---\n{t.strip()}")
                doc.close()
            except Exception as e:
                # Fall through to pypdf or image fallback
                pass

        # 2. Try pypdf fallback if fitz had no text or failed
        if not extracted_text and pypdf:
            try:
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                for page_num, page in enumerate(reader.pages):
                    t = page.extract_text()
                    if t and t.strip():
                        extracted_text.append(f"--- Page {page_num + 1} ---\n{t.strip()}")
            except Exception as e:
                pass

        full_text = "\n\n".join(extracted_text).strip()

        # 3. If PDF is text-based, return formatted text
        if full_text:
            return f"=== DOCUMENT: {filename} (Format: PDF) ===\n{full_text}"

        # 4. If PDF contains no selectable text (scanned PDF), use Multimodal Gemini extraction
        return self._extract_multimodal_document(filename, content_bytes, "application/pdf")

    def _process_image(self, filename: str, content_bytes: bytes, mime_type: Optional[str] = None) -> str:
        # Verify image integrity using Pillow if available
        if Image:
            try:
                img = Image.open(io.BytesIO(content_bytes))
                img.verify()
            except Exception as e:
                raise DocumentProcessingError(f"File '{filename}' is a corrupted or unreadable image: {e}") from e

        if not mime_type:
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".png":
                mime_type = "image/png"
            elif ext in {".jpg", ".jpeg"}:
                mime_type = "image/jpeg"
            else:
                mime_type = "image/png"

        return self._extract_multimodal_document(filename, content_bytes, mime_type)

    def _extract_multimodal_document(self, filename: str, content_bytes: bytes, mime_type: str) -> str:
        """
        Uses Gemini multimodal capabilities to extract structured text content from images or scanned PDFs.
        """
        prompt = (
            f"You are a document transcription assistant. Extract all visible text, line items, tables, "
            f"numbers, dates, and identifiers from this document ('{filename}'). "
            f"Transcribe the content accurately and preserve all labels and values."
        )

        try:
            current_key = self.cred_manager.get_current_key()
            client = genai.Client(api_key=current_key)
            part = types.Part.from_bytes(data=content_bytes, mime_type=mime_type)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[part, prompt]
            )
            extracted_text = response.text.strip() if response.text else ""
            if not extracted_text:
                raise DocumentProcessingError(f"No readable content could be extracted from '{filename}'.")
            return f"=== DOCUMENT: {filename} (Format: {mime_type}) ===\n{extracted_text}"
        except RetrySignal:
            raise
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                self.cred_manager.mark_cooldown(60.0)
                raise RetrySignal(f"Key rate limited during document processing: {err_str}") from e
            raise DocumentProcessingError(f"Failed to process document '{filename}': {err_str}") from e

    def process_bundle(self, files: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Processes a collection of uploaded files into a normalized evidence bundle string.
        files: list of dicts with keys: 'name', 'data' (bytes or base64 str), 'type' (optional)
        """
        if not files:
            raise DocumentProcessingError("No documents provided in upload bundle.")

        combined_texts = []
        metadata_list = []

        for f in files:
            name = f.get("name", "document")
            data = f.get("data")
            mime_type = f.get("type") or mimetypes.guess_type(name)[0]

            if isinstance(data, str):
                # Handle base64 encoded strings
                if data.startswith("data:") and "," in data:
                    # Strip data URL prefix (e.g. data:application/pdf;base64,...)
                    header, b64_str = data.split(",", 1)
                    if not mime_type and ":" in header and ";" in header:
                        mime_type = header.split(":")[1].split(";")[0]
                    content_bytes = base64.b64decode(b64_str)
                else:
                    try:
                        content_bytes = base64.b64decode(data)
                    except Exception:
                        content_bytes = data.encode("utf-8")
            elif isinstance(data, bytes):
                content_bytes = data
            elif isinstance(data, dict):
                content_bytes = json.dumps(data).encode("utf-8")
            else:
                content_bytes = str(data).encode("utf-8")

            doc_text = self.process_file(name, content_bytes, mime_type)
            combined_texts.append(doc_text)
            metadata_list.append({
                "name": name,
                "type": mime_type or "unknown",
                "size_bytes": len(content_bytes)
            })

        normalized_bundle_str = "\n\n" + ("=" * 60) + "\n\n".join([""] + combined_texts) + "\n\n" + ("=" * 60)
        return normalized_bundle_str, metadata_list
