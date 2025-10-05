import pdfplumber
import fitz  # PyMuPDF
import re
from datetime import datetime
import json

class PDFExtractor:
    def __init__(self):
        self.text_content = []
        self.tables = []
        
    def extract_text_pdfplumber(self, pdf_path):
        """Extract text using pdfplumber"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        self.text_content.append(text)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        self.tables.extend(tables)
            
            return True
        except Exception as e:
            print(f"Error extracting with pdfplumber: {e}")
            return False
    
    def extract_text_pymupdf(self, pdf_path):
        """Fallback: Extract text using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text:
                    self.text_content.append(text)
            
            doc.close()
            return True
        except Exception as e:
            print(f"Error extracting with PyMuPDF: {e}")
            return False
    
    def extract(self, pdf_path):
        """Main extraction method with fallback"""
        self.text_content = []
        self.tables = []
        
        # Try pdfplumber first
        success = self.extract_text_pdfplumber(pdf_path)
        
        # Fallback to PyMuPDF if pdfplumber fails
        if not success or not self.text_content:
            print("Falling back to PyMuPDF...")
            success = self.extract_text_pymupdf(pdf_path)
        
        if not success:
            raise Exception("Failed to extract PDF content")
        
        return {
            'text': '\n'.join(self.text_content),
            'tables': self.tables,
            'pages': len(self.text_content)
        }
    
    def get_text_lines(self):
        """Get all text lines from extracted content"""
        all_text = '\n'.join(self.text_content)
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        return lines
    
    def extract_from_tables(self):
        """Extract structured data from tables if available"""
        structured_data = []
        
        for table in self.tables:
            if not table or len(table) < 2:
                continue
            
            # Assume first row is header
            headers = [str(h).strip().lower() if h else '' for h in table[0]]
            
            # Process data rows
            for row in table[1:]:
                if not row or all(not cell for cell in row):
                    continue
                
                row_data = {}
                for i, cell in enumerate(row):
                    if i < len(headers) and headers[i]:
                        row_data[headers[i]] = str(cell).strip() if cell else ''
                
                if row_data:
                    structured_data.append(row_data)
        
        return structured_data