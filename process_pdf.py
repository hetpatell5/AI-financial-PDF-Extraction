import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdfExtractor import PDFExtractor
from services.transactionParser import TransactionParser
from services.categoryClassifier import CategoryClassifier

def process_pdf(pdf_path, user_id):
    """Main function to process PDF and extract transactions"""
    
    print(f"\n{'='*60}")
    print(f"Processing PDF: {pdf_path}")
    print(f"User ID: {user_id}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Extract text and tables from PDF
        print("Step 1: Extracting PDF content...")
        extractor = PDFExtractor()
        extracted_data = extractor.extract(pdf_path)
        
        print(f"✓ Extracted {extracted_data['pages']} pages")
        print(f"✓ Found {len(extracted_data['tables'])} tables")
        
        # Step 2: Parse transactions
        print("\nStep 2: Parsing transactions...")
        parser = TransactionParser()
        transactions = []
        
        # Try table-based extraction first
        if extracted_data['tables']:
            print("Attempting table-based extraction...")
            table_data = extractor.extract_from_tables()
            table_transactions = parser.parse_transactions_from_table(table_data, user_id)
            transactions.extend(table_transactions)
            print(f"✓ Extracted {len(table_transactions)} transactions from tables")
        
        # Also try text-based extraction
        print("Attempting text-based extraction...")
        text_lines = extractor.get_text_lines()
        text_transactions = parser.parse_transactions_from_text(text_lines, user_id)
        
        # Merge and deduplicate
        existing_ids = {t['id'] for t in transactions}
        for trans in text_transactions:
            if trans['id'] not in existing_ids:
                transactions.append(trans)
                existing_ids.add(trans['id'])
        
        print(f"✓ Total unique transactions: {len(transactions)}")
        
        if not transactions:
            print("\n⚠ Warning: No transactions found!")
            print("This could mean:")
            print("  - The PDF format is not recognized")
            print("  - The PDF doesn't contain transaction data")
            print("  - The extraction patterns need adjustment")
            return None
        
        # Step 3: Classify transactions
        print("\nStep 3: Classifying transactions...")
        classifier = CategoryClassifier()
        transactions = classifier.classify_transactions(transactions)
        print("✓ Categories assigned")
        
        # Step 4: Sort by date
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Step 5: Save to JSON
        output_dir = 'extracted'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'transactions_{user_id}_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Transactions saved to: {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total Transactions: {len(transactions)}")
        
        total_debit = sum(t['amount'] for t in transactions if t['type'] == 'Debit')
        total_credit = sum(t['amount'] for t in transactions if t['type'] == 'Credit')
        
        print(f"Total Debits: ₹{total_debit:,.2f}")
        print(f"Total Credits: ₹{total_credit:,.2f}")
        print(f"Net: ₹{(total_credit - total_debit):,.2f}")
        
        # Category breakdown
        print("\nCategory Breakdown:")
        category_stats = classifier.get_category_stats(transactions)
        for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {category}: {stats['count']} transactions")
        
        print("="*60 + "\n")
        
        return transactions
        
    except Exception as e:
        print(f"\n❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_multiple_pdfs(pdf_directory, user_id):
    """Process all PDFs in a directory"""
    all_transactions = []
    
    if not os.path.exists(pdf_directory):
        print(f"Error: Directory {pdf_directory} not found")
        return None
    
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return None
    
    print(f"\nFound {len(pdf_files)} PDF file(s) to process\n")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        transactions = process_pdf(pdf_path, user_id)
        
        if transactions:
            all_transactions.extend(transactions)
    
    # Remove duplicates based on transaction ID
    unique_transactions = {}
    for trans in all_transactions:
        unique_transactions[trans['id']] = trans
    
    all_transactions = list(unique_transactions.values())
    
    # Save combined file
    if all_transactions:
        output_file = os.path.join('extracted', f'transactions_all_{user_id}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_transactions, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Combined transactions saved to: {output_file}")
        print(f"Total unique transactions: {len(all_transactions)}")
    
    return all_transactions

def print_usage():
    """Print usage instructions"""
    print("\nUsage:")
    print("  Process single PDF:")
    print("    python process_pdf.py <pdf_path> <user_id>")
    print("\n  Process directory:")
    print("    python process_pdf.py <pdf_directory> <user_id> --dir")
    print("\nExamples:")
    print("  python process_pdf.py data/sample_pdfs/hdfc-demo.pdf user123")
    print("  python process_pdf.py data/sample_pdfs user123 --dir\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    path_arg = sys.argv[1]
    user_id = sys.argv[2]
    is_dir = len(sys.argv) > 3 and sys.argv[3] == "--dir"
    
    if is_dir:
        process_multiple_pdfs(path_arg, user_id)
    else:
        process_pdf(path_arg, user_id)
