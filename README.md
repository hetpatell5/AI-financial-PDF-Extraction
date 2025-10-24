# AI-Powered Financial PDF Data Extraction System

An intelligent system that extracts transaction data from bank statement PDFs using Machine Learning and Natural Language Processing, stores them in a database, and provides a REST API for querying.

## 🎯 Features

- **PDF Extraction**: Parses bank statements using multiple extraction strategies (pdfplumber + PyMuPDF)
- **ML/NLP Processing**: Uses spaCy for intelligent transaction parsing
- **Smart Classification**: Automatically categorizes transactions (Food, Shopping, Bills, etc.)
- **Database Storage**: MongoDB with efficient indexing for fast queries
- **REST API**: Full-featured API for transaction queries and analytics
- **Duplicate Detection**: Prevents duplicate transaction entries
- **Multi-User Support**: Isolates transactions by user

## 📁 Project Structure

```
financial-pdf-extraction/
├── data/
│   └── sample_pdfs/              # Place your PDF bank statements here
├── extracted/                     # Extracted JSON files
├── api/
│   ├── app.js                    # Main API server
│   └── routes/
│       └── transactions.js       # API endpoints
├── services/
│   ├── pdfExtractor.py           # PDF parsing logic
│   ├── transactionParser.py     # ML/NLP extraction
│   ├── categoryClassifier.py    # Category assignment
│   └── databaseService.js        # Database operations
├── models/
│   └── Transaction.js            # MongoDB schema
├── config/
│   └── dbConfig.js               # Database configuration
├── tests/
│   ├── api-test.js               # Automated tests
│   └── postman_collection.json   # Postman collection
├── process_pdf.py                # Main processing script
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js dependencies
├── .env                          # Environment variables
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (local or Atlas)
- Git

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd financial-pdf-extraction
```

### Step 2: Python Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Step 3: Node.js Setup

```bash
# Install dependencies
npm install
```

### Step 4: MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB locally
# Start MongoDB service
mongod
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get connection string

### Step 5: Environment Configuration

Create `.env` file in root directory:

```bash
PORT=3000
MONGODB_URI=mongodb://localhost:27017/financial_extraction
# Or for Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/financial_extraction
```

### Step 6: Place PDF Files

```bash
# Copy your bank statement PDFs to:
cp your-bank-statement.pdf data/sample_pdfs/
```

## 📊 Usage

### Step 1: Process PDF Files

Process a single PDF:
```bash
python process_pdf.py data/sample_pdfs/hdfc-demo.pdf user123
```

Process all PDFs in directory:
```bash
python process_pdf.py data/sample_pdfs user123 --dir
```

This will:
- Extract text and tables from PDFs
- Parse transactions using ML/NLP
- Classify transactions into categories
- Save to `extracted/transactions_*.json`

### Step 2: Start API Server

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

Server will start at `http://localhost:3000`

### Step 3: Import Transactions to Database

```bash
curl -X POST http://localhost:3000/api/transactions/import \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "extracted/transactions_user123_20241005_120000.json",
    "userId": "user123"
  }'
```

## 🔌 API Endpoints

### Base URL: `http://localhost:3000`

### 1. Get All Transactions
```bash
GET /api/transactions/:userId
Query params: limit, skip, startDate, endDate, category, type, minAmount, maxAmount

# Example
curl "http://localhost:3000/api/transactions/user123?limit=10"
```

### 2. Get Transactions by Month
```bash
GET /api/transactions/:userId/month/:year/:month

# Example
curl "http://localhost:3000/api/transactions/user123/month/2024/10"
```

### 3. Get Transactions by Category
```bash
GET /api/transactions/:userId/category/:category

# Example
curl "http://localhost:3000/api/transactions/user123/category/Food"
```

### 4. Get Summary Statistics
```bash
GET /api/transactions/:userId/summary
Query params: startDate, endDate

# Example
curl "http://localhost:3000/api/transactions/user123/summary"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "totalCredit": 50000,
      "totalDebit": 35000,
      "creditCount": 5,
      "debitCount": 25,
      "netAmount": 15000
    },
    "categories": [
      {
        "_id": "Food",
        "debit": 5000,
        "credit": 0,
        "count": 10
      }
    ]
  }
}
```

### 5. Get All Categories
```bash
GET /api/transactions/:userId/categories

# Example
curl "http://localhost:3000/api/transactions/user123/categories"
```

### 6. Filter by Date Range
```bash
GET /api/transactions/:userId?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD

# Example
curl "http://localhost:3000/api/transactions/user123?startDate=2024-01-01&endDate=2024-12-31"
```

### 7. Filter by Transaction Type
```bash
GET /api/transactions/:userId?type=Debit

# Example - Get only debits
curl "http://localhost:3000/api/transactions/user123?type=Debit&limit=20"

# Example - Get only credits
curl "http://localhost:3000/api/transactions/user123?type=Credit"
```

### 8. Filter by Amount Range
```bash
GET /api/transactions/:userId?minAmount=1000&maxAmount=5000

# Example
curl "http://localhost:3000/api/transactions/user123?minAmount=1000&maxAmount=5000"
```

### 9. Import Transactions
```bash
POST /api/transactions/import
Body: { "filePath": "path/to/file.json", "userId": "user123" }

# Example
curl -X POST http://localhost:3000/api/transactions/import \
  -H "Content-Type: application/json" \
  -d '{"filePath": "extracted/transactions_user123.json", "userId": "user123"}'
```

### 10. Add Transaction(s)
```bash
POST /api/transactions
Body: Single transaction object or array of transactions

# Example
curl -X POST http://localhost:3000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "unique123",
    "userId": "user123",
    "date": "2024-10-05",
    "description": "Swiggy Order",
    "amount": 450,
    "type": "Debit",
    "category": "Food"
  }'
```

### 11. Delete User Transactions
```bash
DELETE /api/transactions/:userId

# Example
curl -X DELETE http://localhost:3000/api/transactions/user123
```

## 🧪 Testing

### Automated Tests

```bash
# Run test suite
npm test
```

### Manual Testing with Postman

1. Import `tests/postman_collection.json` into Postman
2. Set variables:
   - `base_url`: http://localhost:3000
   - `user_id`: user123
3. Run collection

### cURL Examples

```bash
# Health check
curl http://localhost:3000/health

# Get transactions
curl "http://localhost:3000/api/transactions/user123?limit=5"

# Get summary
curl "http://localhost:3000/api/transactions/user123/summary"

# Filter by category
curl "http://localhost:3000/api/transactions/user123/category/Shopping"
```

## 📦 Transaction Data Structure

```json
{
  "id": "abc123...",
  "userId": "user123",
  "date": "2024-10-05",
  "description": "UPI payment to Swiggy",
  "amount": 450.50,
  "type": "Debit",
  "category": "Food",
  "balance": 12500.00
}
```

## 🏷️ Supported Categories

- **Food**: Swiggy, Zomato, restaurants
- **Shopping**: Amazon, Flipkart, retail stores
- **Bills**: Electricity, water, mobile recharge
- **Transportation**: Uber, Ola, fuel, parking
- **Entertainment**: Netflix, movies, gaming
- **Healthcare**: Hospitals, pharmacies, medical
- **Education**: Schools, courses, books
- **Investment**: Mutual funds, stocks, trading
- **Transfer**: UPI, IMPS, NEFT, RTGS
- **ATM**: Cash withdrawals
- **Salary**: Income, payroll
- **Other**: Uncategorized transactions

## 🔧 Troubleshooting

### PDF Extraction Issues

**Problem**: No transactions found
```bash
# Check PDF content
python -c "import pdfplumber; pdf = pdfplumber.open('your.pdf'); print(pdf.pages[0].extract_text())"
```

**Solution**: PDFs may have non-standard formats. Check the output and adjust patterns in `transactionParser.py`

### Database Connection Issues

**Problem**: MongoDB connection failed
```bash
# Check if MongoDB is running
mongod --version
# or
mongo --eval "db.version()"
```

**Solution**: Ensure MongoDB is running or check connection string in `.env`

### Port Already in Use

**Problem**: Port 3000 is already in use
```bash
# Change port in .env
PORT=3001
```

## 📈 Performance Tips

1. **Batch Processing**: Process multiple PDFs together for efficiency
2. **Indexing**: MongoDB indexes are created automatically for fast queries
3. **Pagination**: Use `limit` and `skip` for large result sets
4. **Date Filters**: Always use date filters for better performance

## 🔐 Security Notes

- **Sensitive Data**: Account numbers are not stored in the database
- **User Isolation**: Each user's transactions are completely isolated
- **Unique IDs**: Transactions use MD5 hashes to prevent duplicates

## 📝 Development Notes

### Adding New Categories

Edit `services/categoryClassifier.py`:
```python
self.categories = {
    'NewCategory': ['keyword1', 'keyword2', 'keyword3'],
    # ...
}
```

### Custom Date Patterns

Edit `services/transactionParser.py`:
```python
self.date_patterns = [
    r'your-custom-pattern',
    # ...
]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.
