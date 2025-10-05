#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Financial PDF Processing Script
Extracts transaction data from bank statement PDFs using ML/NLP
"""

import sys
import os
import json
from datetime import datetime
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdfExtractor import PDFExtractor
from services.transactionParser import TransactionParser
from services.categoryClassifier import CategoryClassifier


def process_pdf(pdf_path, user_id):
    """
    Main function to process a single PDF and extract transactions
    
    Args:
        pdf_path (str): Path to the PDF file
        user_id (str): User identifier
    
    Returns:
        list: Extracted transactions or None if failed
    """
    
    print(f"\n{'='*60}")
    print(f"Processing PDF: {pdf_path}")
    print(f"User ID: {user_id}")
    print(f"{'='*60}\n")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"[ERROR] File not found - {pdf_path}")
        return None
    
    try:
        # Step 1: Extract text and tables from PDF
        print("Step 1: Extracting PDF content...")
        print("-" * 60)
        
        extractor = PDFExtractor()
        extracted_data = extractor.extract(pdf_path)
        
        print(f"[OK] Extracted {extracted_data['pages']} pages")
        print(f"[OK] Found {len(extracted_data['tables'])} tables")
        print(f"[OK] Text length: {len(extracted_data['text'])} characters")
        
        # Step 2: Parse transactions
        print("\nStep 2: Parsing transactions...")
        print("-" * 60)
        
        parser = TransactionParser()
        transactions = []
        
        # Try table-based extraction first
        if extracted_data['tables']:
            print("-> Attempting table-based extraction...")
            table_data = extractor.extract_from_tables()
            
            if table_data:
                print(f"  Found {len(table_data)} rows in tables")
                table_transactions = parser.parse_transactions_from_table(table_data, user_id)
                transactions.extend(table_transactions)
                print(f"[OK] Extracted {len(table_transactions)} transactions from tables")
            else:
                print("  No structured table data found")
        
        # Also try text-based extraction
        print("-> Attempting text-based extraction...")
        text_lines = extractor.get_text_lines()
        print(f"  Processing {len(text_lines)} text lines")
        
        text_transactions = parser.parse_transactions_from_text(text_lines, user_id)
        
        # Merge and deduplicate transactions
        existing_ids = {t['id'] for t in transactions}
        new_count = 0
        
        for trans in text_transactions:
            if trans['id'] not in existing_ids:
                transactions.append(trans)
                existing_ids.add(trans['id'])
                new_count += 1
        
        print(f"[OK] Extracted {len(text_transactions)} transactions from text ({new_count} unique)")
        print(f"[OK] Total unique transactions: {len(transactions)}")
        
        # Check if we found any transactions
        if not transactions:
            print("\n[WARNING] No transactions found!")
            print("\nPossible reasons:")
            print("  1. The PDF format is not recognized")
            print("  2. The PDF doesn't contain transaction data")
            print("  3. The extraction patterns need adjustment")
            print("\nTip: Check the first few lines of extracted text:")
            print("-" * 60)
            for i, line in enumerate(text_lines[:10]):
                print(f"{i+1}. {line[:80]}")
            print("-" * 60)
            return None
        
        # Step 3: Classify transactions into categories
        print("\nStep 3: Classifying transactions...")
        print("-" * 60)
        
        classifier = CategoryClassifier()
        transactions = classifier.classify_transactions(transactions)
        print("[OK] Categories assigned to all transactions")
        
        # Step 4: Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        print("[OK] Transactions sorted by date")
        
        # Step 5: Save to JSON file
        print("\nStep 4: Saving extracted data...")
        print("-" * 60)
        
        output_dir = 'extracted'
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = os.path.join(
            output_dir, 
            f'transactions_{user_id}_{pdf_filename}_{timestamp}.json'
        )
        
        # Save transactions to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Transactions saved to: {output_file}")
        
        # Step 6: Print summary statistics
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        
        print(f"\n[STATS] Overall Statistics:")
        print(f"  Total Transactions: {len(transactions)}")
        print(f"  Date Range: {transactions[-1]['date']} to {transactions[0]['date']}")
        
        # Calculate totals
        total_debit = sum(t['amount'] for t in transactions if t['type'] == 'Debit')
        total_credit = sum(t['amount'] for t in transactions if t['type'] == 'Credit')
        debit_count = sum(1 for t in transactions if t['type'] == 'Debit')
        credit_count = sum(1 for t in transactions if t['type'] == 'Credit')
        
        print(f"\n[STATS] Financial Summary:")
        print(f"  Total Debits:  Rs.{total_debit:,.2f} ({debit_count} transactions)")
        print(f"  Total Credits: Rs.{total_credit:,.2f} ({credit_count} transactions)")
        print(f"  Net Amount:    Rs.{(total_credit - total_debit):,.2f}")
        
        # Category breakdown
        print(f"\n[STATS] Category Breakdown:")
        category_stats = classifier.get_category_stats(transactions)
        
        # Sort categories by transaction count
        sorted_categories = sorted(
            category_stats.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        for category, stats in sorted_categories:
            print(f"  {category:15} : {stats['count']:3} transactions | "
                  f"Debit: Rs.{stats['total_debit']:>10,.2f} | "
                  f"Credit: Rs.{stats['total_credit']:>10,.2f}")
        
        print("="*60 + "\n")
        
        return transactions
        
    except Exception as e:
        print(f"\n[ERROR] Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_multiple_pdfs(pdf_directory, user_id):
    """
    Process all PDF files in a directory
    
    Args:
        pdf_directory (str): Directory containing PDF files
        user_id (str): User identifier
    
    Returns:
        list: All extracted transactions or None if failed
    """
    
    print("\n" + "="*60)
    print("BATCH PDF PROCESSING")
    print("="*60)
    
    # Check if directory exists
    if not os.path.exists(pdf_directory):
        print(f"[ERROR] Directory not found - {pdf_directory}")
        return None
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {pdf_directory}")
        return None
    
    print(f"\n[INFO] Found {len(pdf_files)} PDF file(s) to process:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print()
    
    all_transactions = []
    success_count = 0
    fail_count = 0
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'#'*60}")
        print(f"Processing file {i}/{len(pdf_files)}: {pdf_file}")
        print(f"{'#'*60}")
        
        pdf_path = os.path.join(pdf_directory, pdf_file)
        transactions = process_pdf(pdf_path, user_id)
        
        if transactions:
            all_transactions.extend(transactions)
            success_count += 1
            print(f"[SUCCESS] Successfully processed {pdf_file}")
        else:
            fail_count += 1
            print(f"[WARNING] Failed to process {pdf_file}")
    
    # Remove duplicate transactions based on transaction ID
    print("\n" + "="*60)
    print("DEDUPLICATION")
    print("="*60)
    
    original_count = len(all_transactions)
    unique_transactions = {}
    
    for trans in all_transactions:
        unique_transactions[trans['id']] = trans
    
    all_transactions = list(unique_transactions.values())
    duplicate_count = original_count - len(all_transactions)
    
    print(f"Original transactions: {original_count}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Unique transactions: {len(all_transactions)}")
    
    # Save combined file
    if all_transactions:
        # Sort by date
        all_transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Save combined JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join('extracted', f'transactions_all_{user_id}_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_transactions, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Combined transactions saved to: {output_file}")
        
        # Final summary
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Files processed successfully: {success_count}/{len(pdf_files)}")
        print(f"Files failed: {fail_count}/{len(pdf_files)}")
        print(f"Total unique transactions: {len(all_transactions)}")
        
        # Calculate totals
        total_debit = sum(t['amount'] for t in all_transactions if t['type'] == 'Debit')
        total_credit = sum(t['amount'] for t in all_transactions if t['type'] == 'Credit')
        
        print(f"\nTotal Debits: Rs.{total_debit:,.2f}")
        print(f"Total Credits: Rs.{total_credit:,.2f}")
        print(f"Net Amount: Rs.{(total_credit - total_debit):,.2f}")
        print("="*60 + "\n")
    
    return all_transactions


def print_usage():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("Financial PDF Processing Script")
    print("="*60)
    print("\nUsage:")
    print("  Process single PDF:")
    print("    python process_pdf.py <pdf_path> <user_id>")
    print("\n  Process directory:")
    print("    python process_pdf.py <pdf_directory> <user_id> --dir")
    print("\nExamples:")
    print("  python process_pdf.py data/sample_pdfs/hdfc-demo.pdf user123")
    print("  python process_pdf.py data/sample_pdfs user123 --dir")
    print("\nArguments:")
    print("  pdf_path       : Path to PDF file")
    print("  pdf_directory  : Directory containing PDF files")
    print("  user_id        : User identifier (e.g., user123)")
    print("  --dir          : Flag to process entire directory")
    print("\nOutput:")
    print("  Extracted transactions are saved to: extracted/")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    
    # Check arguments
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    # Parse arguments
    path_arg = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "user123"
    is_directory = len(sys.argv) > 3 and sys.argv[3] == '--dir'
    
    # Process based on mode
    if is_directory:
        # Process directory
        result = process_multiple_pdfs(path_arg, user_id)
    else:
        # Process single file
        result = process_pdf(path_arg, user_id)
    
    # Exit with appropriate code
    if result is not None:
        print("[SUCCESS] Processing completed successfully!")
        sys.exit(0)
    else:
        print("[FAILED] Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()