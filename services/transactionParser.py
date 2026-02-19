import re
from datetime import datetime
# Removing spaCy dependency
# import spacy
from dateutil import parser as date_parser
import hashlib

class TransactionParser:
    def __init__(self):
        # Removed spaCy dependency
        self.nlp = None
        print("Using simplified text processing without spaCy")
        
        # Common transaction keywords
        self.debit_keywords = ['debit', 'withdrawal', 'payment', 'paid', 'purchase', 'transfer to', 'atm', 'dr', 'dr.']
        self.credit_keywords = ['credit', 'deposit', 'received', 'transfer from', 'salary', 'refund', 'by ', 'rev', 'interest']
        
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
        
        # Prepare a list of transaction blocks
        transaction_blocks = []
        current_block = []
        
        for line in text_lines:
            if not line.strip(): 
                continue
            if self._is_header_line(line):
                continue
                
            # Check if this line starts a new transaction (has a Date)
            date = self._extract_date(line)
            
            if date:
                # If we have a current block accumulated, save it
                if current_block:
                    transaction_blocks.append(current_block)
                # Start new block
                current_block = [line]
            else:
                # Append to current block if it exists
                if current_block:
                    current_block.append(line)
        
        # Add the last block
        if current_block:
            transaction_blocks.append(current_block)
            
        # Process each block
        for block in transaction_blocks:
            # Combine block lines into one text for context
            full_text = " ".join(block)
            
            # Use the first line for primary date extraction (though we already know it has a date)
            # Use the FULL text for Amount and Description extraction
            transaction = self._extract_transaction_from_block(block, user_id)
            if transaction:
                transactions.append(transaction)
                
        return transactions
        
        return transactions
    
    def parse_transactions_from_table(self, table_data, user_id):
        """Parse transactions from structured table data"""
        transactions = []
        
        # DEBUG: Count statistics
        total_rows = len(table_data)
        no_date_count = 0
        no_amount_count = 0
        success_count = 0
        failed_samples = []  # Store a few failed rows for debugging
        
        for i, row in enumerate(table_data):
            transaction = self._extract_transaction_from_dict(row, user_id, i)
            if transaction:
                transactions.append(transaction)
                success_count += 1
            else:
                # Debug: Why did it fail?
                date_field = None
                for key in row.keys():
                    if 'date' in key.lower():
                        date_field = row.get(key)
                        break
                if not date_field:
                    no_date_count += 1
                    # Capture "no date" failures
                    if len(failed_samples) < 10:
                        failed_samples.append(f"NO DATE KEY (keys={list(row.keys())}): {row}")
                else:
                    no_amount_count += 1
                    # Capture first 10 failed rows for debugging
                    if len(failed_samples) < 10:
                        failed_samples.append(row)
        
        print(f"\n[DEBUG] Transaction parsing stats:")
        print(f"  Total rows received: {total_rows}")
        print(f"  Successfully parsed: {success_count}")
        print(f"  Skipped - no date: {no_date_count}")
        print(f"  Skipped - no amount: {no_amount_count}")
        
        if failed_samples:
            print(f"\n[DEBUG] Sample failed rows:")
            for idx, row in enumerate(failed_samples):
                print(f"  Failed {idx}: {row}")
        
        # Debug: Check for high value debits to find the 40k discrepancy
        print("\n[DEBUG] High Value Debits (> 10000):")
        debit_sum = 0
        for t in transactions:
            if t['type'] == 'Debit':
                debit_sum += t['amount']
                if t['amount'] > 10000:
                    print(f"  Dr {t['amount']}: {t['date']} - {t['description'][:30]}")
        print(f"[DEBUG] Calculated Total Debit: {debit_sum}")
        
        return transactions
    
    def _extract_transaction_from_block(self, block, user_id):
        """Extract transaction details from a block of lines"""
        try:
            full_text = " ".join(block)
            first_line = block[0]
            
            # Extract date (from first line usually)
            date = self._extract_date(first_line)
            if not date:
                # Try finding date in full text if first line failed (unlikely given logic)
                date = self._extract_date(full_text)
            
            if not date:
                return None
            
            # Extract amount from FULL text
            # We prioritize explicit amount columns if they were somehow preserved, but here we just regex the blob
            amount_info = self._extract_amount(full_text)
            if not amount_info:
                return None
            
            # Extract description
            description = self._extract_description(full_text)
            
            # Determine transaction type using FULL text context
            trans_type = self._determine_transaction_type(full_text, amount_info['type'])
            
            # Extract balance
            balance = self._extract_balance(full_text)
            
            # Generate unique ID
            transaction_id = self._generate_transaction_id(user_id, date, amount_info['amount'], description, balance)
            
            # Determine category
            category = self._categorize_transaction(description, trans_type)
            
            return {
                'id': transaction_id,
                'userId': user_id,
                'date': date,
                'description': description, # Truncate description further if needed
                'amount': amount_info['amount'],
                'type': trans_type,
                'category': category,
                'balance': balance,
                'raw_line': full_text[:200]
            }
        except Exception as e:
            print(f"Error parsing block: {e}")
            return None        

    def _extract_transaction_from_line(self, line, user_id, index):
        # Wraps block parser for single line
        return self._extract_transaction_from_block([line], user_id)
    
    def _extract_transaction_from_dict(self, row_dict, user_id, index):
        """Extract transaction from dictionary (table row)"""
        try:
            # Normalize all keys to lowercase for matching
            normalized_row = {k.lower().strip(): v for k, v in row_dict.items()}
            
            # Helper function for flexible key matching
            def find_value(keys_to_check):
                for k in keys_to_check:
                    # Direct match
                    if k in normalized_row and normalized_row[k]:
                        return normalized_row[k]
                    # Partial match (key contains or is contained by)
                    for row_key, row_val in normalized_row.items():
                        if row_val and (k in row_key or row_key in k):
                            return row_val
                return None
            
            # Try to find date field
            date_field = find_value(['date', 'post date', 'transaction date', 'txn date', 'value date', 'value dt', 'posting date'])
            
            if not date_field:
                return None
            
            date = self._parse_date(date_field)
            if not date:
                return None
            
            # Find description
            description = find_value(['description', 'particulars', 'narration', 'details', 'remarks', 'transaction details']) or ''
            
            # Find amount - Now with FLEXIBLE matching for column names
            amount = 0
            trans_type = 'Debit'
            
            # Check for Debit/Withdrawal columns (flexible matching)
            debit_keys = ['debit', 'withdrawal', 'withdrawal amt', 'withdrawal amt.', 'debit amount', 'dr', 'dr.', 'paid out', 'money out']
            debit_val = find_value(debit_keys)
            if debit_val:
                amount = self._clean_amount(debit_val)
                # Handle reversals: negative amount in debit column = Credit (money returned)
                if amount < 0:
                    amount = abs(amount)
                    trans_type = 'Credit'
                else:
                    trans_type = 'Debit'
            
            # If no debit, check Credit/Deposit columns
            if amount == 0:
                credit_keys = ['credit', 'deposit', 'deposit amt', 'deposit amt.', 'credit amount', 'cr', 'cr.', 'paid in', 'money in']
                credit_val = find_value(credit_keys)
                if credit_val:
                    amount = self._clean_amount(credit_val)
                    # Handle reversals: negative amount in credit column = Debit (money taken back)
                    if amount < 0:
                        amount = abs(amount)
                        trans_type = 'Debit'
                    else:
                        trans_type = 'Credit'
            
            # If still no amount, try generic 'amount' column and determine type from description
            if amount == 0:
                amount_val = find_value(['amount', 'txn amount', 'transaction amount'])
                if amount_val:
                    amount = self._clean_amount(amount_val)
                    trans_type = self._determine_transaction_type(description, None)
            
            if amount == 0:
                return None
            
            # Find balance
            balance = None
            balance_val = find_value(['balance', 'closing balance', 'available balance', 'running balance'])
            if balance_val:
                balance = self._clean_amount(balance_val)
            
            # Generate unique ID
            transaction_id = self._generate_transaction_id(user_id, date, amount, description, balance)
            
            # Determine category
            category = self._categorize_transaction(description, trans_type)
            
            return {
                'id': transaction_id,
                'userId': user_id,
                'date': date,
                'description': description,
                'amount': amount,
                'type': trans_type,
                'category': category,
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
            # Reject obvious non-date strings
            date_str_lower = str(date_str).lower().strip()
            reject_patterns = ['date', 'narration', 'balance', 'withdrawal', 'deposit', 
                             'credit', 'debit', 'description', 'particulars', 'amount',
                             'opening', 'closing', 'account', 'savings', 'current', 'generated']
            
            # Check if it's obviously not a date
            for pattern in reject_patterns:
                if date_str_lower.startswith(pattern) or date_str_lower == pattern:
                    return None
            
            # Must contain at least one digit to be a date
            if not any(c.isdigit() for c in date_str):
                return None
            
            # Try multiple date formats
            dt = date_parser.parse(date_str, dayfirst=True)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    
    def _extract_amount(self, text):
        """Extract amount and type from text"""
        
        # First, try to extract non-balance amounts (amounts NOT followed by Cr/Dr)
        # This prevents picking up balance column values as transaction amounts
        
        # Pattern for amounts that are NOT part of a balance (not followed by Cr/Dr)
        non_balance_amounts = []
        balance_amounts = []
        
        for pattern in self.amount_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                amount_str = match.group()
                amount_val = self._clean_amount(amount_str)
                
                if amount_val > 0:
                    # Check what follows this amount
                    end_pos = match.end()
                    following_text = text[end_pos:end_pos + 10].strip().lower()
                    
                    # If followed by Cr or Dr, it's a balance amount
                    if following_text.startswith('cr') or following_text.startswith('dr'):
                        balance_amounts.append((amount_val, 'Balance', match.start()))
                    else:
                        non_balance_amounts.append((amount_val, amount_str, match.start()))
        
        # Prefer non-balance amounts (actual transaction amounts)
        if non_balance_amounts:
            # Sort by position - take the first valid transaction amount
            non_balance_amounts.sort(key=lambda x: x[2])
            amount = non_balance_amounts[0][0]
        elif balance_amounts:
            # Fallback to balance amounts if no transaction amounts found
            # This might be for special rows like Opening/Closing balance
            balance_amounts.sort(key=lambda x: x[2])
            amount = balance_amounts[0][0]
        else:
            return None
        
        # Determine transaction type from context
        text_lower = text.lower()
        
        # Remove any balance parts from classification
        text_without_balance = re.sub(r'[\d,]+\.?\d*\s*(cr|dr)\.?\s*$', '', text_lower)
        
        if 'dr' in text_without_balance or 'debit' in text_without_balance:
            trans_type = 'Debit'
        elif 'credit' in text_without_balance:
            trans_type = 'Credit'
        else:
            trans_type = None
            
        return {'amount': amount, 'type': trans_type}
    
    def _clean_amount(self, amount_str):
        """Clean and convert amount string to float"""
        try:
            # Remove currency symbols and spaces
            cleaned = re.sub(r'[₹Rs\s]', '', str(amount_str))
            
            # Check if this is a negative amount (reversal)
            is_negative = cleaned.startswith('-') or '(-' in cleaned or cleaned.endswith('-')
            
            # Remove commas (assuming standard comma separation for thousands/lakhs)
            cleaned = cleaned.replace(',', '')
            
            # Keep only digits and decimal point
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            
            # Check for multiple dots and handle them (keep only the last one if multiple)
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            
            amount = float(cleaned) if cleaned else 0
            
            # Apply negative sign for reversals
            if is_negative:
                amount = -amount
            
            return amount
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
        
        # Check for explicit indicators in the FULL text (careful about "Cr" at end)
        
        # Remove the Balance part (last amount + Cr) to avoid false positive
        clean_text_lower = re.sub(r'[\d,]+\.?\d*\s*(cr|dr)\.?\s*$', '', text_lower)
        
        # 1. Start-of-line heuristics (Strongest)
        if clean_text_lower.startswith('by ') or 'credit' in clean_text_lower or 'deposit' in clean_text_lower:
             return 'Credit'
        if clean_text_lower.startswith('to ') or 'debit' in clean_text_lower or 'withdrawal' in clean_text_lower:
             return 'Debit'
        
        # 2. Check for explicit keywords
        if any(keyword in clean_text_lower for keyword in self.debit_keywords):
            return 'Debit'
        
        # For credit keywords, ensure we don't match "Cr" if it was removed or if it's just part of a word
        # We already checked 'credit' and 'deposit' above.
        for keyword in self.credit_keywords:
            if keyword in clean_text_lower:
                return 'Credit'
        
        # 3. Use hint from amount extraction
        if hint_type:
             return hint_type.title()
             
        # 4. Fallback Default
        # For bank statements, ambiguity usually means Debit (spending/transfer out)
        # UPI without "CREDIT" or "BY" is usually a payment.
        return 'Debit'

    def _categorize_transaction(self, description, trans_type):
        """Categorize transaction based on description and type"""
        desc = description.lower()
        
        if trans_type == 'Credit':
            if 'salary' in desc: return 'Salary'
            if 'refund' in desc or 'reversal' in desc: return 'Refund'
            if 'interest' in desc: return 'Interest'
            if 'upi' in desc: return 'UPI Received'
            if 'imps' in desc or 'neft' in desc or 'rtgs' in desc: return 'Bank Transfer In'
            if 'deposit' in desc or 'cash' in desc: return 'Cash Deposit'
            return 'Income'
            
        # Debit Categories
        if 'upi' in desc: return 'UPI'
        if 'atm' in desc or 'cash' in desc and 'withdrawal' in desc: return 'Cash Withdrawal'
        if 'pos' in desc or 'card' in desc or 'purchase' in desc: return 'Card Purchase'
        if 'imps' in desc or 'neft' in desc or 'rtgs' in desc: return 'Bank Transfer'
        if 'charge' in desc or 'fee' in desc: return 'Bank Charges'
        if 'bill' in desc or 'recharge' in desc: return 'Bills & Utilities'
        if 'food' in desc or 'zomato' in desc or 'swiggy' in desc: return 'Food & Dining'
        if 'uber' in desc or 'ola' in desc or 'travel' in desc: return 'Travel'
        if 'shop' in desc or 'amazon' in desc or 'flipkart' in desc: return 'Shopping'
        if 'investment' in desc or 'sip' in desc or 'mutual' in desc: return 'Investment'
        
        return 'General'
    
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
    
    def _generate_transaction_id(self, user_id, date, amount, description, balance=None):
        """Generate unique transaction ID"""
        # Include more of the description and balance for uniqueness
        # This prevents collision when same-day transactions have similar descriptions
        desc_part = description[:100] if description else ''
        balance_part = str(balance) if balance else ''
        unique_string = f"{user_id}_{date}_{amount}_{desc_part}_{balance_part}"
        return hashlib.md5(unique_string.encode()).hexdigest()