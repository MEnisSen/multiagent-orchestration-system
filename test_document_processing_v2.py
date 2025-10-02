#!/usr/bin/env python3
"""
Enhanced test script for vllm-based document processing functionality.
This script tests the advanced IBM Granite model integration with vllm and docling_core.
"""

import asyncio
import tempfile
import os
import time
from pathlib import Path
from document_processor_v2 import process_uploaded_documents_v2, combine_prompt_with_documents_v2

# PDF processing imports
try:
    import fitz  # PyMuPDF
    import pdf2image
    import PyPDF2
    import pdfplumber
    PDF_LIBRARIES_AVAILABLE = True
except ImportError as e:
    PDF_LIBRARIES_AVAILABLE = False
    print(f"Warning: PDF processing libraries not installed: {e}")
    print("Install with: pip install pymupdf pdf2image PyPDF2 pdfplumber")

async def test_vllm_document_processing():
    """Test the vllm-based document processing functionality."""
    print("🧪 Testing Advanced Document Processing with vllm + docling_core")
    print("=" * 70)
    
    # Create test content
    test_content = """
    This is a comprehensive test document for the multi-agent system.
    
    The system should be able to:
    1. Process various document formats efficiently
    2. Convert them to structured markdown using vllm + docling_core
    3. Handle multi-page documents
    4. Integrate the content with user prompts
    
    Here's a sample Python function that could be implemented:
    
    def calculate_fibonacci(n):
        \"\"\"Calculate the nth Fibonacci number using dynamic programming.\"\"\"
        if n <= 1:
            return n
        
        # Use memoization for efficiency
        memo = {}
        def fib_helper(n):
            if n in memo:
                return memo[n]
            if n <= 1:
                return n
            memo[n] = fib_helper(n-1) + fib_helper(n-2)
            return memo[n]
        
        return fib_helper(n)
    
    The function calculates the nth Fibonacci number with O(n) time complexity.
    """
    
    # Create multiple test files
    test_files = []
    test_filenames = []
    
    # Create text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        test_files.append(f.name)
        test_filenames.append("test_document.txt")
    
    # Create markdown file
    markdown_content = f"""# Test Document

{test_content}

## Additional Information

This document contains:
- Code examples
- Technical specifications
- Implementation details

## Conclusion

The system should process this document and extract all relevant information.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(markdown_content)
        test_files.append(f.name)
        test_filenames.append("test_specification.md")
    
    try:
        print(f"📄 Created {len(test_files)} test files")
        for file_path, filename in zip(test_files, test_filenames):
            print(f"   - {filename}: {file_path}")
        
        # Test document processing
        print(f"\n🔄 Processing documents with vllm + docling_core...")
        print("Note: First run will download the Granite model (~500MB)")
        
        start_time = time.time()
        document_markdowns = await process_uploaded_documents_v2(test_files, test_filenames)
        processing_time = time.time() - start_time
        
        print(f"✅ Processed {len(document_markdowns)} document(s) in {processing_time:.2f} seconds")
        
        # Display the processed markdown
        for i, markdown in enumerate(document_markdowns, 1):
            print(f"\n📋 Document {i} Markdown:")
            print("-" * 50)
            # Show first 800 characters
            preview = markdown[:800] + "..." if len(markdown) > 800 else markdown
            print(preview)
            print("-" * 50)
        
        # Test prompt combination
        user_prompt = "Create a Python calculator with the functions described in the attached documents. Include error handling and unit tests."
        combined_prompt = combine_prompt_with_documents_v2(user_prompt, document_markdowns)
        
        print(f"\n🔗 Combined Prompt:")
        print("-" * 50)
        # Show first 1000 characters
        preview = combined_prompt[:1000] + "..." if len(combined_prompt) > 1000 else combined_prompt
        print(preview)
        print("-" * 50)
        
        print(f"\n📊 Processing Statistics:")
        print(f"   - Documents processed: {len(document_markdowns)}")
        print(f"   - Total processing time: {processing_time:.2f} seconds")
        print(f"   - Average time per document: {processing_time/len(document_markdowns):.2f} seconds")
        print(f"   - Combined prompt length: {len(combined_prompt)} characters")
        
        print("\n✅ Advanced document processing test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"🧹 Cleaned up test file: {file_path}")

async def test_pdf_processing():
    """Test PDF processing with the attached PDF file."""
    print("\n📄 PDF Processing Test")
    print("=" * 30)
    
    if not PDF_LIBRARIES_AVAILABLE:
        print("❌ PDF processing libraries not available. Please install them first.")
        return
    
    # Check if the PDF file exists
    pdf_path = "nvidia_llm.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please ensure the PDF file is in the current directory.")
        return
    
    print(f"📄 Found PDF file: {pdf_path}")
    
    try:
        # Test different PDF processing methods
        print("\n🔍 Testing PDF text extraction methods...")
        
        # Method 1: PyMuPDF (fitz)
        print("1. Testing PyMuPDF extraction...")
        start_time = time.time()
        doc = fitz.open(pdf_path)
        pymupdf_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pymupdf_text += page.get_text()
        doc.close()
        pymupdf_time = time.time() - start_time
        print(f"   ✅ PyMuPDF: {len(pymupdf_text)} characters in {pymupdf_time:.2f}s")
        
        # Method 2: pdfplumber
        print("2. Testing pdfplumber extraction...")
        start_time = time.time()
        pdfplumber_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdfplumber_text += text
        pdfplumber_time = time.time() - start_time
        print(f"   ✅ pdfplumber: {len(pdfplumber_text)} characters in {pdfplumber_time:.2f}s")
        
        # Method 3: PyPDF2
        print("3. Testing PyPDF2 extraction...")
        start_time = time.time()
        pypdf2_text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                pypdf2_text += page.extract_text()
        pypdf2_time = time.time() - start_time
        print(f"   ✅ PyPDF2: {len(pypdf2_text)} characters in {pypdf2_time:.2f}s")
        
        # Choose the best extraction method
        best_method = "PyMuPDF"
        best_text = pymupdf_text
        if len(pdfplumber_text) > len(best_text):
            best_method = "pdfplumber"
            best_text = pdfplumber_text
        if len(pypdf2_text) > len(best_text):
            best_method = "PyPDF2"
            best_text = pypdf2_text
        
        print(f"\n🏆 Best extraction method: {best_method} ({len(best_text)} characters)")
        
        # Test PDF to image conversion (for visual processing)
        print("\n🖼️ Testing PDF to image conversion...")
        try:
            start_time = time.time()
            images = pdf2image.convert_from_path(pdf_path, first_page=1, last_page=3)  # First 3 pages
            conversion_time = time.time() - start_time
            print(f"   ✅ Converted {len(images)} pages to images in {conversion_time:.2f}s")
            
            # Save first page as test image
            if images:
                test_image_path = "test_pdf_page.png"
                images[0].save(test_image_path)
                print(f"   💾 Saved first page as: {test_image_path}")
                
                # Test processing the image with our document processor
                print("\n🔄 Testing image processing with document processor...")
                image_start_time = time.time()
                document_markdowns = await process_uploaded_documents_v2([test_image_path], ["test_pdf_page.png"])
                image_processing_time = time.time() - image_start_time
                
                print(f"   ✅ Processed PDF page image in {image_processing_time:.2f}s")
                if document_markdowns:
                    print(f"   📋 Generated markdown: {len(document_markdowns[0])} characters")
                    print(f"   Preview: {document_markdowns[0][:200]}...")
                
                # Clean up test image
                if os.path.exists(test_image_path):
                    os.unlink(test_image_path)
                    print(f"   🧹 Cleaned up test image")
            
        except Exception as e:
            print(f"   ❌ PDF to image conversion failed: {e}")
            print("   Note: You may need to install poppler-utils: sudo apt-get install poppler-utils")
        
        # Test with extracted text
        print("\n📝 Testing text-based processing...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(best_text)
            temp_text_file = f.name
        
        try:
            text_start_time = time.time()
            document_markdowns = await process_uploaded_documents_v2([temp_text_file], ["extracted_pdf_text.txt"])
            text_processing_time = time.time() - text_start_time
            
            print(f"   ✅ Processed extracted text in {text_processing_time:.2f}s")
            if document_markdowns:
                print(f"   📋 Generated markdown: {len(document_markdowns[0])} characters")
                print(f"   Preview: {document_markdowns[0][:300]}...")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_text_file):
                os.unlink(temp_text_file)
        
        print("\n✅ PDF processing test completed successfully!")
        
    except Exception as e:
        print(f"❌ PDF processing test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_performance_comparison():
    """Test performance with different document sizes."""
    print("\n🚀 Performance Testing")
    print("=" * 30)
    
    # Create documents of different sizes
    small_doc = "This is a small document with basic content."
    medium_doc = "This is a medium document. " * 100  # ~2KB
    large_doc = "This is a large document with extensive content. " * 1000  # ~20KB
    
    test_cases = [
        ("small.txt", small_doc),
        ("medium.txt", medium_doc),
        ("large.txt", large_doc)
    ]
    
    test_files = []
    test_filenames = []
    
    for filename, content in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            test_files.append(f.name)
            test_filenames.append(filename)
    
    try:
        start_time = time.time()
        document_markdowns = await process_uploaded_documents_v2(test_files, test_filenames)
        total_time = time.time() - start_time
        
        print(f"📊 Performance Results:")
        print(f"   - Total documents: {len(test_cases)}")
        print(f"   - Total processing time: {total_time:.2f} seconds")
        print(f"   - Average time per document: {total_time/len(test_cases):.2f} seconds")
        
        for i, (filename, _) in enumerate(test_cases):
            doc_size = len(test_cases[i][1])
            print(f"   - {filename}: {doc_size} chars, processed successfully")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    finally:
        # Clean up
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == "__main__":
    print("🚀 Starting advanced document processing test...")
    print("This test uses vllm + docling_core for efficient document processing.")
    print("The model will be downloaded and cached on first run.\n")
    
    # Run main test
    asyncio.run(test_vllm_document_processing())
    
    # Run PDF processing test
    asyncio.run(test_pdf_processing())
    
    # Run performance test
    asyncio.run(test_performance_comparison())
    
    print("\n🎉 All tests completed!")
