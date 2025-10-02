"""
Advanced document processing module using vllm and docling_core for multi-page document conversion.
Supports various file formats with proper document structure handling and batch processing.
"""

import os
import tempfile
import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import shutil

# Document processing imports
try:
    from vllm import LLM, SamplingParams
    from transformers import AutoProcessor
    from PIL import Image
    from docling_core.types.doc import DoclingDocument
    from docling_core.types.doc.document import DocTagsDocument
    VLLM_AVAILABLE = True
except ImportError as e:
    VLLM_AVAILABLE = False
    print(f"Warning: Required packages not installed: {e}")
    print("Install with: pip install vllm docling-core transformers torch")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedDocumentProcessor:
    """
    Advanced document processor using vllm and docling_core for converting documents to markdown.
    Supports multi-page documents, various formats, and batch processing.
    """
    
    def __init__(self, model_name: str = "ibm-granite/granite-docling-258M", device: str = "auto"):
        """
        Initialize the advanced document processor.
        
        Args:
            model_name: Hugging Face model name for Granite
            device: Device to use ('auto', 'cuda', 'cpu')
        """
        self.model_name = model_name
        self.device = device
        self.llm = None
        self.processor = None
        self._model_loaded = False
        
        # Supported file extensions
        self.supported_extensions = {
            '.pdf', '.docx', '.doc', '.txt', '.md', '.rtf',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',
            '.html', '.htm', '.xml'
        }
        
        # Prompt for document conversion
        self.prompt_text = "Convert this page to docling."
        self.messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": self.prompt_text},
                ],
            },
        ]
    
    async def load_model(self):
        """Load the vllm model and processor."""
        if not VLLM_AVAILABLE:
            raise ImportError("Required packages not installed. Install with: pip install vllm docling-core transformers torch")
        
        if self._model_loaded:
            return
        
        try:
            logger.info(f"Loading vllm model: {self.model_name}")
            
            # Initialize vllm LLM with proper configuration
            self.llm = LLM(
                model=self.model_name, 
                revision="untied", 
                limit_mm_per_prompt={"image": 1},
                gpu_memory_utilization=0.8,  # Use 80% of GPU memory
                max_model_len=8192,
                dtype="float16" if self.device == "cuda" else "float32"
            )
            
            # Initialize processor
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            self._model_loaded = True
            logger.info(f"vllm model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load vllm model: {e}")
            raise
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file extension is supported."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_extensions
    
    async def process_document(self, file_path: str, filename: str) -> str:
        """
        Process a single document and convert to markdown.
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Markdown content of the document
        """
        if not self._model_loaded:
            await self.load_model()
        
        try:
            # Determine file type and process accordingly
            ext = Path(filename).suffix.lower()
            
            if ext in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}:
                # Single image processing
                return await self._process_single_image(file_path, filename)
            elif ext in {'.pdf', '.docx', '.doc', '.rtf'}:
                # Multi-page document processing
                return await self._process_multi_page_document(file_path, filename)
            else:
                # Text-based files
                return await self._process_text_file(file_path, filename)
                
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return f"Error processing document {filename}: {str(e)}"
    
    async def _process_single_image(self, image_path: str, filename: str) -> str:
        """Process a single image file using vllm and docling."""
        try:
            # Load and prepare image
            with Image.open(image_path) as im:
                image = im.convert("RGB")
            
            # Prepare prompt
            prompt = self.processor.apply_chat_template(self.messages, add_generation_prompt=True)
            
            # Prepare input for vllm
            batched_input = [{"prompt": prompt, "multi_modal_data": {"image": image}}]
            
            # Sampling parameters
            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=8192,
                skip_special_tokens=False,
            )
            
            # Run inference
            start_time = time.time()
            outputs = self.llm.generate(batched_input, sampling_params=sampling_params)
            processing_time = time.time() - start_time
            
            logger.info(f"Processed {filename} in {processing_time:.2f} seconds")
            
            # Extract doctags
            doctags = outputs[0].outputs[0].text
            
            # Convert to DoclingDocument and save as markdown
            doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([doctags], [image])
            doc = DoclingDocument.load_from_doctags(doctags_doc, document_name=filename)
            
            # Get markdown content
            markdown_content = doc.export_to_markdown()
            
            return f"# Document: {filename}\n\n{markdown_content}"
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            return f"Error processing image {filename}: {str(e)}"
    
    async def _process_multi_page_document(self, file_path: str, filename: str) -> str:
        """Process multi-page documents (PDF, DOCX, etc.)."""
        try:
            ext = Path(filename).suffix.lower()
            
            if ext == '.pdf':
                return await self._process_pdf_document(file_path, filename)
            else:
                # For other document types, return a placeholder
                return f"# Document: {filename}\n\n*Document processing for {ext} files requires additional libraries. This would convert the document to images and process them with the Granite model.*"
            
        except Exception as e:
            logger.error(f"Error processing multi-page document {filename}: {e}")
            return f"Error processing multi-page document {filename}: {str(e)}"
    
    async def _process_pdf_document(self, file_path: str, filename: str) -> str:
        """Process PDF documents by converting to images and processing with vllm."""
        try:
            # Import PDF processing libraries
            try:
                import fitz  # PyMuPDF
                import pdf2image
                PDF_AVAILABLE = True
            except ImportError:
                PDF_AVAILABLE = False
            
            if not PDF_AVAILABLE:
                return f"# Document: {filename}\n\n*PDF processing requires pymupdf and pdf2image libraries. Install with: pip install pymupdf pdf2image*"
            
            # Extract text first as fallback
            doc = fitz.open(file_path)
            text_content = ""
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text_content += page.get_text()
            doc.close()
            
            # Try to convert to images for better processing
            try:
                # Convert first few pages to images
                images = pdf2image.convert_from_path(file_path, first_page=1, last_page=min(3, doc.page_count))
                
                if images:
                    # Process images with vllm
                    batched_inputs = []
                    for i, image in enumerate(images):
                        prompt = self.processor.apply_chat_template(self.messages, add_generation_prompt=True)
                        batched_inputs.append({"prompt": prompt, "multi_modal_data": {"image": image}})
                    
                    # Run batch inference
                    sampling_params = SamplingParams(
                        temperature=0.0,
                        max_tokens=8192,
                        skip_special_tokens=False,
                    )
                    
                    outputs = self.llm.generate(batched_inputs, sampling_params=sampling_params)
                    
                    # Combine results
                    combined_markdown = f"# Document: {filename}\n\n"
                    for i, output in enumerate(outputs):
                        doctags = output.outputs[0].text
                        doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([doctags], [images[i]])
                        doc = DoclingDocument.load_from_doctags(doctags_doc, document_name=f"{filename}_page_{i+1}")
                        page_markdown = doc.export_to_markdown()
                        combined_markdown += f"## Page {i+1}\n\n{page_markdown}\n\n"
                    
                    return combined_markdown
                else:
                    # Fallback to text processing
                    return f"# Document: {filename}\n\n{text_content}"
                    
            except Exception as e:
                logger.warning(f"PDF to image conversion failed: {e}, falling back to text extraction")
                return f"# Document: {filename}\n\n{text_content}"
                
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {e}")
            return f"Error processing PDF {filename}: {str(e)}"
    
    async def _process_text_file(self, file_path: str, filename: str) -> str:
        """Process text-based files."""
        try:
            # Read text content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            
            # For text files, we can return them directly or with minimal processing
            return f"# Document: {filename}\n\n{text_content}"
            
        except Exception as e:
            logger.error(f"Error processing text file {filename}: {e}")
            return f"Error processing text file {filename}: {str(e)}"
    
    async def process_multiple_documents(self, file_paths: List[str], filenames: List[str]) -> List[str]:
        """
        Process multiple documents and return markdown for each.
        Uses batch processing for efficiency when possible.
        
        Args:
            file_paths: List of file paths
            filenames: List of original filenames
            
        Returns:
            List of markdown content for each document
        """
        if not self._model_loaded:
            await self.load_model()
        
        results = []
        
        # Group documents by type for batch processing
        image_files = []
        other_files = []
        
        for file_path, filename in zip(file_paths, filenames):
            if not self.is_supported_file(filename):
                results.append(f"# Document: {filename}\n\n*Unsupported file type: {Path(filename).suffix}*")
                continue
            
            ext = Path(filename).suffix.lower()
            if ext in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}:
                image_files.append((file_path, filename))
            else:
                other_files.append((file_path, filename))
        
        # Process images in batch for efficiency
        if image_files:
            batch_results = await self._process_image_batch(image_files)
            results.extend(batch_results)
        
        # Process other files individually
        for file_path, filename in other_files:
            markdown_content = await self.process_document(file_path, filename)
            results.append(markdown_content)
        
        return results
    
    async def _process_image_batch(self, image_files: List[Tuple[str, str]]) -> List[str]:
        """Process multiple images in a single batch for efficiency."""
        try:
            # Prepare batch inputs
            batched_inputs = []
            image_names = []
            images = []
            
            for file_path, filename in image_files:
                with Image.open(file_path) as im:
                    image = im.convert("RGB")
                
                prompt = self.processor.apply_chat_template(self.messages, add_generation_prompt=True)
                batched_inputs.append({"prompt": prompt, "multi_modal_data": {"image": image}})
                image_names.append(filename)
                images.append(image)
            
            # Run batch inference
            start_time = time.time()
            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=8192,
                skip_special_tokens=False,
            )
            
            outputs = self.llm.generate(batched_inputs, sampling_params=sampling_params)
            processing_time = time.time() - start_time
            
            logger.info(f"Processed {len(image_files)} images in {processing_time:.2f} seconds")
            
            # Process results
            results = []
            for filename, output, image in zip(image_names, outputs, images):
                try:
                    doctags = output.outputs[0].text
                    
                    # Convert to DoclingDocument
                    doctags_doc = DocTagsDocument.from_doctags_and_image_pairs([doctags], [image])
                    doc = DoclingDocument.load_from_doctags(doctags_doc, document_name=filename)
                    
                    # Get markdown content
                    markdown_content = doc.export_to_markdown()
                    
                    results.append(f"# Document: {filename}\n\n{markdown_content}")
                    
                except Exception as e:
                    logger.error(f"Error processing image {filename}: {e}")
                    results.append(f"# Document: {filename}\n\nError processing image: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            # Fallback to individual processing
            results = []
            for file_path, filename in image_files:
                try:
                    markdown_content = await self._process_single_image(file_path, filename)
                    results.append(markdown_content)
                except Exception as e:
                    results.append(f"# Document: {filename}\n\nError processing: {str(e)}")
            return results

# Global document processor instance
document_processor_v2 = AdvancedDocumentProcessor()

async def process_uploaded_documents_v2(file_paths: List[str], filenames: List[str]) -> List[str]:
    """
    Process uploaded documents using the advanced vllm-based processor.
    
    Args:
        file_paths: List of temporary file paths
        filenames: List of original filenames
        
    Returns:
        List of markdown content for each document
    """
    return await document_processor_v2.process_multiple_documents(file_paths, filenames)

def combine_prompt_with_documents_v2(user_prompt: str, document_markdowns: List[str]) -> str:
    """
    Combine user prompt with processed document markdowns.
    
    Args:
        user_prompt: Original user text prompt
        document_markdowns: List of markdown content from documents
        
    Returns:
        Combined prompt with documents
    """
    if not document_markdowns:
        return user_prompt
    
    combined_prompt = user_prompt
    
    for i, doc_markdown in enumerate(document_markdowns, 1):
        combined_prompt += f"\n\n---\n\n**Attached Document {i}:**\n\n{doc_markdown}"
    
    return combined_prompt
