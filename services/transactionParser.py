import re
from datetime import datetime
import spacy
from dateutil import parser as date_parser
import hashlib

class TransactionParser:
    def __init__(self):
        # Load spaCy model for NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Warning: spaCy model not loaded. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Common transaction keywords
        self.debit_keywords = ['debit', 'withdrawal', 'payment', 'paid', 'purchase', 'transfer to', 'atm']
        self.credit_keywords = ['credit', 'deposit', 'received', 'transfer from', 'salary', 'refund']
        
        # Date patterns
        self.date_patterns = [
            r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',  # DD-MM-YYYY or DD/MM/YYYY
            r'\b\d{2}[-/]\d{2}[-/]\d{2}\b',   # DD-MM-YY or DD/MM/YY
            r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',   # YYYY-MM-DD
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b'  # DD Mon YYYY
        ]
        
        # Amount patterns
        self.amount_patterns = [
            r'₹\s*[\d,]+\.?\d*',  # ₹1,234.56
            r'Rs\.?\s*[\d,]+\.?\d*',  # Rs.1234.56
            r'\b[\d,]+\.\d{2}\b',  # 1234.56
            r'\b[\d,]+\b(?=\s*(?:Dr|Cr|debit|credit))',  # Amount before Dr/Cr
        ]
    
    def parse_transactions_from_text(self, text_lines, user_id):
        """Parse transactions from text lines using NLP and pattern matching"""
        transactions = []
        
        for i, line in enumerate(text_lines):
            # Skip header lines and empty lines
            if self._is_header_line(line) or len(line) < 10:
                continue
            
            transaction = self._extract_transaction_from_line(line, user_id, i)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def parse_transactions_from_table(self, table_data, user_id):
        """Parse transactions from structured table data"""
        transactions = []
        
        for i, row in enumerate(table_data):
            transaction = self._extract_transaction_from_dict(row, user_id, i)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def _extract_transaction_from_line(self, line, user_id, index):
        """Extract transaction details from a single line"""
        try:
            # Extract date
            date = self._extract_date(line)
            if not date:
                return None
            
            # Extract amount
            amount_info = self._extract_amount(line)
            if not amount_info:
                return None
            
            # Extract description
            description = self._extract_description(line)
            
            # Determine transaction type
            trans_type = self._determine_transaction_type(line, amount_info['type'])
            
            # Extract balance if available
            balance = self._extract_balance(line)
            
            # Generate unique ID
            transaction_id = self._generate_transaction_id(user_id, date, amount_info['amount'], description)
            
            return {
                'id': transaction_id,
                'userId': user_id,
                'date': date,
                'description': description,
                'amount': amount_info['amount'],
                'type': trans_type,
                'balance': balance,
                'raw_line': line
            }
        except Exception as e:
            print(f"Error parsing line: {e}")
            return None
    
    def _extract_transaction_from_dict(self, row_dict, user_id, index):
        """Extract transaction from dictionary (table row)"""
        try:
            # Try to find date field
            date_field = None
            for key in ['date', 'transaction date', 'txn date', 'value date']:
                if key in row_dict and row_dict[key]:
                    date_field = row_dict[key]
                    break
            
            if not date_field:
                return None
            
            date = self._parse_date(date_field)
            if not date:
                return None
            
            # Find description
            description = ''
            for key in ['description', 'particulars', 'narration', 'details', 'remarks']:
                if key in row_dict and row_dict[key]:
                    description = row_dict[key]
                    break
            
            # Find amount
            amount = 0
            trans_type = 'Debit'
            
            for key in ['debit', 'withdrawal', 'debit amount']:
                if key in row_dict and row_dict[key]:
                    amount = self._clean_amount(row_dict[key])
                    trans_type = 'Debit'
                    break
            
            if amount == 0:
                for key in ['credit', 'deposit', 'credit amount']:
                    if key in row_dict and row_dict[key]:
                        amount = self._clean_amount(row_dict[key])
                        trans_type = 'Credit'
                        break
            
            if amount == 0:
                return None
            
            # Find balance
            balance = None
            for key in ['balance', 'closing balance', 'available balance']:
                if key in row_dict and row_dict[key]:
                    balance = self._clean_amount(row_dict[key])
                    break
            
            # Generate unique ID
            transaction_id = self._generate_transaction_id(user_id, date, amount, description)
            
            return {
                'id': transaction_id,
                'userId': user_id,
                'date': date,
                'description': description,
                'amount': amount,
                'type': trans_type,
                'balance': balance
            }
        except Exception as e:
            print(f"Error parsing row: {e}")
            return None
    
    def _extract_date(self, text):
        """Extract date from text"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group())
        return None
    
    def _parse_date(self, date_str):
        """Parse date string to ISO format"""
        try:
            # Try multiple date formats
            dt = date_parser.parse(date_str, dayfirst=True)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    
    def _extract_amount(self, text):
        """Extract amount and type from text"""
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Get the first valid amount
                for match in matches:
                    amount = self._clean_amount(match)
                    if amount > 0:
                        # Check if it's near Dr/Cr indicator
                        trans_type = 'Debit' if 'dr' in text.lower() or 'debit' in text.lower() else 'Credit'
                        return {'amount': amount, 'type': trans_type}
        return None
    
    def _clean_amount(self, amount_str):
        """Clean and convert amount string to float"""
        try:
            # Remove currency symbols and extra spaces
            cleaned = re.sub(r'[₹Rs.,\s]', '', str(amount_str))
            # Keep only digits and decimal point
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            return float(cleaned) if cleaned else 0
        except:
            return 0
    
    def _extract_description(self, text):
        """Extract transaction description"""
        # Remove date and amount patterns
        desc = text
        for pattern in self.date_patterns + self.amount_patterns:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
        
        # Remove common noise words
        desc = re.sub(r'\b(Dr|Cr|debit|credit)\b', '', desc, flags=re.IGNORECASE)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        return desc[:200] if desc else 'Transaction'
    
    def _determine_transaction_type(self, text, hint_type):
        """Determine if transaction is debit or credit"""
        text_lower = text.lower()
        
        # Check for explicit indicators
        if any(keyword in text_lower for keyword in self.debit_keywords):
            return 'Debit'
        if any(keyword in text_lower for keyword in self.credit_keywords):
            return 'Credit'
        
        # Use hint from amount extraction
        return hint_type
    
    def _extract_balance(self, text):
        """Extract balance from text"""
        # Look for balance indicators
        balance_pattern = r'balance[:\s]*₹?\s*[\d,]+\.?\d*'
        match = re.search(balance_pattern, text, re.IGNORECASE)
        if match:
            return self._clean_amount(match.group())
        return None
    
    def _is_header_line(self, line):
        """Check if line is a header"""
        header_keywords = ['date', 'description', 'debit', 'credit', 'balance', 'transaction', 'particulars']
        line_lower = line.lower()
        keyword_count = sum(1 for keyword in header_keywords if keyword in line_lower)
        return keyword_count >= 2
    
    def _generate_transaction_id(self, user_id, date, amount, description):
        """Generate unique transaction ID"""
        unique_string = f"{user_id}_{date}_{amount}_{description[:50]}"
        return hashlib.md5(unique_string.encode()).hexdigest()