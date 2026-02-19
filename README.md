<div align="center">

# AI Financial PDF Extractor

**Transform bank statement PDFs into structured, queryable financial data.**

A full-stack system combining Python-based PDF parsing with a Node.js REST API and an interactive web dashboard — built for accuracy, multi-user isolation, and extensibility.

---

![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?style=flat-square&logo=node.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Express](https://img.shields.io/badge/Express-4.x-000000?style=flat-square&logo=express&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)

</div>

---

## Overview

This project automates the extraction and analysis of financial transactions from PDF bank statements. It uses dual extraction strategies (table-based and text-based) to handle varied PDF formats, classifies each transaction into a meaningful category, persists data in MongoDB, and surfaces everything through a REST API and a glassmorphism-styled web dashboard.

---

## Features

- **Dual PDF Extraction** — Attempts structured table extraction first via `pdfplumber`; falls back to regex-based text parsing for non-tabular PDFs
- **Smart Categorisation** — Automatically assigns categories (Shopping, Bills, Transfer, Education, etc.) based on transaction description patterns
- **Duplicate Detection** — MD5-based transaction IDs prevent re-importing the same data
- **Multi-User Isolation** — All data is scoped to a `userId`; users never see each other's transactions
- **REST API** — Full CRUD with filtering by date, category, type, and amount range
- **Interactive Dashboard** — Chart.js visualisations, category breakdown table, paginated transaction list, and date/category filters
- **Web Upload Interface** — Drag-and-drop PDF upload with real-time processing feedback

---

## Tech Stack

| Layer | Technology |
|---|---|
| PDF Parsing | Python, pdfplumber, PyMuPDF |
| NLP / ML | spaCy, scikit-learn, transformers |
| Backend API | Node.js, Express.js |
| Database | MongoDB (Mongoose ODM) |
| Frontend | Vanilla HTML/CSS/JS, Chart.js |
| Dev Tooling | nodemon, dotenv, multer |

---

## Project Structure

```
AI-financial-PDF-Extraction/
│
├── api/
│   ├── app.js                      # Express server entry point
│   └── routes/
│       ├── upload.js               # PDF upload & processing endpoints
│       └── transactions.js         # Transaction CRUD & analytics endpoints
│
├── services/
│   ├── pdfExtractor.py             # PDF text and table extraction
│   ├── transactionParser.py        # Transaction row parsing & date detection
│   ├── categoryClassifier.py       # Keyword-based category assignment
│   └── databaseService.js          # MongoDB query abstraction layer
│
├── models/
│   └── Transaction.js              # Mongoose schema & static methods
│
├── public/
│   ├── index.html                  # Upload interface
│   ├── dashboard.html              # Analytics dashboard
│   ├── css/style.css               # Design system (glassmorphism)
│   └── js/
│       ├── main.js                 # Upload page logic
│       ├── dashboard.js            # Dashboard data fetching & charts
│       └── cursor.js               # Custom cursor effect
│
├── config/
│   └── dbConfig.js                 # MongoDB connection handler
│
├── models/
│   └── Transaction.js              # MongoDB schema
│
├── tests/
│   ├── api-test.js                 # Automated API tests
│   └── postman_collection.json     # Postman collection
│
├── extracted/                      # Runtime output: extracted JSON files
├── uploads/                        # Temporary storage for uploaded PDFs
├── process_pdf.py                  # CLI entry point for PDF processing
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies
└── .env                            # Environment variables (not committed)
```

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- A MongoDB instance (local or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas))

---

### 1. Clone the Repository

```bash
git clone https://github.com/hetpatell5/AI-financial-PDF-Extraction.git
cd AI-financial-PDF-Extraction
```

---

### 2. Python Environment

```bash
# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm
```

---

### 3. Node.js Dependencies

```bash
npm install
```

---

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/financial_extraction
```

For MongoDB Atlas, use your connection string:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/financial_extraction
```

---

### 5. Run the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

---

## Usage

### Web Interface

1. Open `http://localhost:3000` in your browser
2. Enter a User ID (any string identifier, e.g. `john`)
3. Drag and drop a bank statement PDF or click **Browse Files**
4. Click **Process Documents**
5. After processing completes, you are automatically redirected to the dashboard

### CLI — Process a PDF Directly

```bash
python process_pdf.py path/to/statement.pdf <userId>
```

The extracted transactions are saved to `extracted/transactions_<userId>_<timestamp>.json`.

---

## API Reference

**Base URL:** `http://localhost:3000`

### Upload & Process

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a single PDF and process it |
| `POST` | `/api/upload/batch` | Upload and process multiple PDFs |

### Transactions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/transactions/:userId` | Get all transactions for a user |
| `GET` | `/api/transactions/:userId/summary` | Get financial summary and category breakdown |
| `GET` | `/api/transactions/:userId/categories` | Get all distinct categories for a user |
| `GET` | `/api/transactions/:userId/category/:category` | Filter transactions by category |
| `GET` | `/api/transactions/:userId/month/:year/:month` | Filter transactions by month |
| `POST` | `/api/transactions/import` | Import transactions from a JSON file |
| `DELETE` | `/api/transactions/:userId` | Delete all transactions for a user |

### Query Parameters for `GET /api/transactions/:userId`

| Parameter | Type | Description |
|---|---|---|
| `startDate` | `YYYY-MM-DD` | Filter from this date |
| `endDate` | `YYYY-MM-DD` | Filter up to this date |
| `category` | `string` | Filter by category name |
| `type` | `Debit` \| `Credit` | Filter by transaction type |
| `minAmount` | `number` | Minimum transaction amount |
| `maxAmount` | `number` | Maximum transaction amount |
| `limit` | `number` | Number of results (default: 100) |
| `skip` | `number` | Offset for pagination |

### Example Requests

```bash
# Get a user's last 10 transactions
curl "http://localhost:3000/api/transactions/john?limit=10"

# Get financial summary
curl "http://localhost:3000/api/transactions/john/summary"

# Filter debits in October 2025
curl "http://localhost:3000/api/transactions/john?type=Debit&startDate=2025-10-01&endDate=2025-10-31"

# Import from an extracted JSON file
curl -X POST http://localhost:3000/api/transactions/import \
  -H "Content-Type: application/json" \
  -d '{"filePath": "extracted/transactions_john_20251001_120000.json", "userId": "john"}'
```

### Summary Response Schema

```json
{
  "success": true,
  "data": {
    "overview": {
      "totalCredit": 482981.00,
      "totalDebit": 482887.14,
      "creditCount": 20,
      "debitCount": 25,
      "netAmount": 93.86
    },
    "categories": [
      {
        "_id": "Other",
        "debit": 298487.14,
        "credit": 250701.00,
        "count": 28
      }
    ]
  }
}
```

---

## Transaction Data Model

```json
{
  "id":          "5b29ac34670e7cc96ba6cb44eaf7c74f",
  "userId":      "john",
  "date":        "2025-10-30",
  "description": "IMPS-528918133329-BMAPEDUSERVICES",
  "amount":      11000.00,
  "type":        "Credit",
  "category":    "Transfer",
  "balance":     118493.86
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | MD5 hash — unique fingerprint per transaction |
| `userId` | `string` | Owning user identifier |
| `date` | `Date` | Transaction date |
| `description` | `string` | Raw narration from the bank statement |
| `amount` | `number` | Transaction amount (always positive) |
| `type` | `Debit` \| `Credit` | Direction of the transaction |
| `category` | `string` | Auto-assigned category |
| `balance` | `number` | Closing balance after transaction |

---

## Supported Categories

| Category | Typical Matches |
|---|---|
| Food | Swiggy, Zomato, restaurants |
| Shopping | Amazon, Flipkart, retail |
| Bills | Electricity, mobile recharge, broadband |
| Transportation | Uber, Ola, fuel, parking |
| Entertainment | Netflix, Spotify, movies |
| Healthcare | Hospitals, pharmacies |
| Education | Courses, books, school fees |
| Investment | Mutual funds, stocks, trading |
| Transfer | UPI, IMPS, NEFT, RTGS |
| ATM | Cash withdrawals |
| Salary | Payroll, salary credits |
| Other | Anything not matched above |

To add a custom category, edit the `categories` dictionary in `services/categoryClassifier.py`.

---

## Troubleshooting

**No transactions extracted from a PDF**

The PDF may use a non-standard layout. Run the extraction in isolation to inspect the raw text:

```bash
python -c "import pdfplumber; pdf = pdfplumber.open('your.pdf'); print(pdf.pages[0].extract_text())"
```

If the text looks structured, the issue is likely in the date/amount regex patterns in `services/transactionParser.py`.

---

**MongoDB connection failure**

Verify that your `MONGODB_URI` in `.env` is correct, that your IP is whitelisted in Atlas, and that the cluster is active.

---

**Port 3000 already in use**

Change the port in `.env`:

```env
PORT=3001
```

---

**0 transactions inserted after a successful upload**

This can happen if the same transactions were uploaded previously (duplicate detection via MD5 IDs). The server will log `[DB] Insert result:` lines showing the exact inserted/duplicates/errors counts.

---

## Security

- The `.env` file is excluded from version control — never commit credentials
- Uploaded PDFs are deleted from the server immediately after processing
- Account numbers and sensitive identifiers are not stored; only transaction metadata is persisted
- Each user's data is fully isolated by `userId` at the database query level

---

## Running Tests

```bash
# Automated API test suite
npm test

# Health check
curl http://localhost:3000/health
```

For manual testing, import `tests/postman_collection.json` into Postman and set:
- `base_url` → `http://localhost:3000`
- `user_id` → your chosen user identifier

---

## License

Released under the [MIT License](LICENSE).
