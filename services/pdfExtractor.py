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
        """Extract structured data from tables if available.
        
        Handles:
        1. Merged cells where multiple transactions are concatenated with newlines
        2. Continuation pages that don't have header rows
        """
        structured_data = []
        
        # Known header patterns (used to detect if a row is headers vs data)
        header_patterns = ['date', 'narration', 'description', 'particulars', 'withdrawal', 'deposit', 'debit', 'credit', 'balance', 'amount', 'chq', 'ref']
        
        # Store headers - but reset per table if that table has its own headers
        known_headers = None
        
        for table in self.tables:
            if not table or len(table) < 1:
                continue
            
            # Check if first row looks like headers or data
            first_row = table[0]
            first_row_text = ' '.join(str(cell).lower() for cell in first_row if cell)
            
            # Count how many header keywords are in the first row
            header_matches = sum(1 for p in header_patterns if p in first_row_text)
            
            # Also check if first row contains dates (DD/MM/YY format) - indicates data, not headers
            has_date_pattern = bool(__import__('re').search(r'\d{2}[-/]\d{2}[-/]\d{2,4}', first_row_text))
            
            if header_matches >= 3 and not has_date_pattern:
                # This is a header row - extract headers from THIS table
                known_headers = [str(h).strip().lower() if h else '' for h in first_row]
                data_rows = table[1:]
            else:
                # This is a continuation page or table without headers
                if known_headers is None or len(known_headers) != len(first_row):
                    # Need to build headers based on column count and patterns
                    col_count = len(first_row)
                    
                    # Try to detect column types from content
                    if col_count == 6:
                        # BoB format: DATE, NARRATION, CHQ.NO., WITHDRAWAL, DEPOSIT, BALANCE
                        known_headers = ['date', 'narration', 'chq.no.', 'withdrawal (dr)', 'deposit (cr)', 'balance']
                    elif col_count == 7:
                        # HDFC format: DATE, NARRATION, CHQ, VALUEDT, WITHDRAWAL, DEPOSIT, BALANCE
                        known_headers = ['date', 'narration', 'chq./ref.no.', 'valuedt', 'withdrawalamt.', 'depositamt.', 'closingbalance']
                    else:
                        # Generic fallback based on column count
                        known_headers = [f'col{i}' for i in range(col_count)]
                        # Try to identify key columns
                        for i, cell in enumerate(first_row):
                            cell_text = str(cell).lower() if cell else ''
                            if __import__('re').search(r'\d{2}[-/]\d{2}[-/]\d{2,4}', cell_text):
                                known_headers[i] = 'date'
                
                data_rows = table  # ALL rows are data
            
            # Process data rows
            for row in data_rows:
                if not row or all(not cell for cell in row):
                    continue
                
                # Check if cells contain newlines (merged transactions)
                date_col = row[0] if row else ''
                if date_col:
                    date_lines = [d.strip() for d in str(date_col).strip().split('\n') if d.strip()]
                else:
                    date_lines = []
                
                if len(date_lines) > 1:
                    # SMART ALIGNMENT: Get all non-empty amounts and match them with dates
                    # Find column indices for amounts and other data
                    withdrawal_idx = None
                    deposit_idx = None
                    narration_idx = None
                    balance_idx = None
                    
                    for i, h in enumerate(known_headers):
                        if 'withdrawal' in h or h in ['dr', 'dr.']:
                            withdrawal_idx = i
                        elif 'deposit' in h or h in ['cr', 'cr.']:
                            deposit_idx = i
                        elif 'narration' in h or 'description' in h or 'particulars' in h:
                            narration_idx = i
                        elif 'balance' in h or 'closing' in h:
                            balance_idx = i
                    
                    # Helper function to safely get column value
                    def safe_get(r, idx):
                        if idx is not None and idx < len(r):
                            return r[idx]
                        return None
                    
                    # Extract all non-empty amounts with their types
                    withdrawals = []
                    deposits = []
                    
                    withdrawal_cell = safe_get(row, withdrawal_idx)
                    if withdrawal_cell:
                        withdrawals = [w.strip() for w in str(withdrawal_cell).split('\n') if w.strip()]
                    
                    deposit_cell = safe_get(row, deposit_idx)
                    if deposit_cell:
                        deposits = [d.strip() for d in str(deposit_cell).split('\n') if d.strip()]
                    
                    # Get other columns split by lines
                    narrations = []
                    narration_cell = safe_get(row, narration_idx)
                    if narration_cell:
                        narrations = [n.strip() for n in str(narration_cell).split('\n')]
                    
                    balances = []
                    balance_cell = safe_get(row, balance_idx)
                    if balance_cell:
                        balances = [b.strip() for b in str(balance_cell).split('\n')]
                    
                    # Now create transactions by matching dates with amounts sequentially
                    withdrawal_ptr = 0
                    deposit_ptr = 0
                    
                    for line_idx, date_val in enumerate(date_lines):
                        row_data = {}
                        row_data[known_headers[0]] = date_val  # Date
                        
                        # Get narration for this line (use line_idx, but cap at available)
                        if narration_idx and line_idx < len(narrations):
                            row_data[known_headers[narration_idx]] = narrations[line_idx]
                        
                        # Get balance for this line
                        if balance_idx is not None and line_idx < len(balances):
                            row_data[known_headers[balance_idx]] = balances[line_idx]
                        
                        # Try to assign an amount - check if this line should have withdrawal or deposit
                        # Strategy: If there are remaining withdrawals and we haven't consumed one recently,
                        # OR if no deposits left, use withdrawal. Otherwise use deposit.
                        amount_assigned = False
                        
                        # Simple approach: alternate based on what's available
                        # More robust: Check if withdrawal pointer matches expected count
                        if withdrawal_ptr < len(withdrawals):
                            row_data[known_headers[withdrawal_idx]] = withdrawals[withdrawal_ptr]
                            withdrawal_ptr += 1
                            amount_assigned = True
                            # Also set empty deposit
                            if deposit_idx is not None:
                                row_data[known_headers[deposit_idx]] = ''
                        elif deposit_ptr < len(deposits):
                            row_data[known_headers[deposit_idx]] = deposits[deposit_ptr]
                            deposit_ptr += 1
                            amount_assigned = True
                            # Also set empty withdrawal
                            if withdrawal_idx is not None:
                                row_data[known_headers[withdrawal_idx]] = ''
                        
                        # Fill any other columns
                        for col_idx, cell in enumerate(row):
                            header = known_headers[col_idx] if col_idx < len(known_headers) else ''
                            if header and header not in row_data:
                                if cell:
                                    cell_lines = str(cell).strip().split('\n')
                                    if line_idx < len(cell_lines):
                                        row_data[header] = cell_lines[line_idx].strip()
                                    else:
                                        row_data[header] = ''
                                else:
                                    row_data[header] = ''
                        
                        if row_data and amount_assigned:
                            structured_data.append(row_data)
                else:
                    # Normal single-line row
                    row_data = {}
                    for i, cell in enumerate(row):
                        if i < len(known_headers) and known_headers[i]:
                            row_data[known_headers[i]] = str(cell).strip() if cell else ''
                    
                    if row_data:
                        structured_data.append(row_data)
        
        print(f"[DEBUG] Extracted {len(structured_data)} rows from tables")
        return structured_data