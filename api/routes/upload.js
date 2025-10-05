const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const { spawn } = require('child_process');
const dbService = require('../../services/databaseService');

// Configure multer for file upload
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = 'uploads';
    try {
      await fs.mkdir(uploadDir, { recursive: true });
      cb(null, uploadDir);
    } catch (error) {
      cb(error);
    }
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
  fileFilter: (req, file, cb) => {
    if (path.extname(file.originalname).toLowerCase() === '.pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed!'));
    }
  }
});

// POST /api/upload - Upload and process PDF
router.post('/', upload.single('pdf'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded' });
    }

    const { userId } = req.body;
    if (!userId) {
      return res.status(400).json({ success: false, message: 'userId is required' });
    }

    const filePath = req.file.path;
    const fileName = req.file.originalname;

    console.log(`Processing uploaded file: ${fileName} for user: ${userId}`);

    // Process PDF using Python script
    const transactions = await processPDF(filePath, userId);

    if (!transactions || transactions.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No transactions found in the PDF. The format may not be recognized.'
      });
    }

    // Import transactions to database
    const result = await dbService.insertTransactions(transactions);

    // Clean up uploaded file
    try {
      await fs.unlink(filePath);
    } catch (err) {
      console.error('Error deleting file:', err);
    }

    // Calculate statistics
    const stats = calculateStats(transactions);

    res.json({
      success: true,
      message: 'PDF processed successfully',
      data: {
        fileName: fileName,
        totalTransactions: transactions.length,
        inserted: result.inserted,
        duplicates: result.duplicates,
        errors: result.errors,
        statistics: stats,
        transactions: transactions.slice(0, 10) // Return first 10
      }
    });

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
});

// POST /api/upload/batch - Upload multiple PDFs
router.post('/batch', upload.array('pdfs', 10), async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ success: false, message: 'No files uploaded' });
    }

    const { userId } = req.body;
    if (!userId) {
      return res.status(400).json({ success: false, message: 'userId is required' });
    }

    const results = [];
    let allTransactions = [];

    for (const file of req.files) {
      try {
        console.log(`Processing: ${file.originalname}`);
        const transactions = await processPDF(file.path, userId);

        results.push({
          fileName: file.originalname,
          success: true,
          transactionCount: transactions ? transactions.length : 0
        });

        if (transactions) {
          allTransactions = allTransactions.concat(transactions);
        }

        // Clean up
        await fs.unlink(file.path);
      } catch (error) {
        results.push({
          fileName: file.originalname,
          success: false,
          error: error.message
        });
      }
    }

    // Remove duplicates
    const uniqueTransactions = {};
    allTransactions.forEach(t => {
      uniqueTransactions[t.id] = t;
    });
    allTransactions = Object.values(uniqueTransactions);

    // Import to database
    const importResult = await dbService.insertTransactions(allTransactions);

    res.json({
      success: true,
      message: 'Batch processing completed',
      data: {
        filesProcessed: results.length,
        totalTransactions: allTransactions.length,
        inserted: importResult.inserted,
        duplicates: importResult.duplicates,
        results: results,
        statistics: calculateStats(allTransactions)
      }
    });

  } catch (error) {
    console.error('Batch upload error:', error);
    res.status(500).json({ success: false, message: error.message });
  }
});

// Helper function to process PDF using Python script
function processPDF(filePath, userId) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python', ['process_pdf.py', filePath, userId]);

    let output = '';
    let errorOutput = '';
    let transactions = [];

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
      console.log(data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
      console.error(data.toString());
    });

    pythonProcess.on('close', async (code) => {
      if (code !== 0) {
        reject(new Error(`PDF processing failed: ${errorOutput}`));
        return;
      }

      try {
        // Find the generated JSON file
        const extractedDir = 'extracted';
        const files = await fs.readdir(extractedDir);
        
        // Find the most recent file for this user
        const userFiles = files.filter(f => 
          f.startsWith(`transactions_${userId}`) && f.endsWith('.json')
        );
        
        if (userFiles.length === 0) {
          reject(new Error('No transaction file generated'));
          return;
        }

        // Sort by timestamp (newest first)
        userFiles.sort().reverse();
        const latestFile = path.join(extractedDir, userFiles[0]);

        // Read and parse the JSON file
        const fileContent = await fs.readFile(latestFile, 'utf-8');
        transactions = JSON.parse(fileContent);

        resolve(transactions);
      } catch (error) {
        reject(error);
      }
    });
  });
}

// Helper function to calculate statistics
function calculateStats(transactions) {
  const stats = {
    totalDebit: 0,
    totalCredit: 0,
    debitCount: 0,
    creditCount: 0,
    categories: {}
  };

  transactions.forEach(t => {
    if (t.type === 'Debit') {
      stats.totalDebit += t.amount;
      stats.debitCount++;
    } else {
      stats.totalCredit += t.amount;
      stats.creditCount++;
    }

    if (!stats.categories[t.category]) {
      stats.categories[t.category] = { count: 0, amount: 0 };
    }
    stats.categories[t.category].count++;
    stats.categories[t.category].amount += t.amount;
  });

  stats.netAmount = stats.totalCredit - stats.totalDebit;

  return stats;
}

module.exports = router;