const express = require('express');
const router = express.Router();
const dbService = require('../../services/databaseService');
const fs = require('fs').promises;
const path = require('path');

// GET /api/transactions/:userId - Get all transactions for a user
router.get('/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const options = {
      startDate: req.query.startDate,
      endDate: req.query.endDate,
      category: req.query.category,
      type: req.query.type,
      minAmount: req.query.minAmount,
      maxAmount: req.query.maxAmount,
      limit: req.query.limit || 100,
      skip: req.query.skip || 0,
      sort: req.query.sortBy ? { [req.query.sortBy]: req.query.order === 'asc' ? 1 : -1 } : { date: -1 }
    };

    const result = await dbService.getTransactionsByUser(userId, options);

    if (result.success) {
      res.json({
        success: true,
        data: result.data,
        pagination: result.pagination
      });
    } else {
      res.status(500).json({ success: false, message: result.message });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// GET /api/transactions/:userId/month/:year/:month - Get transactions for a specific month
router.get('/:userId/month/:year/:month', async (req, res) => {
  try {
    const { userId, year, month } = req.params;
    const result = await dbService.getTransactionsByMonth(userId, parseInt(year), parseInt(month));

    if (result.success) {
      res.json({
        success: true,
        data: result.data,
        pagination: result.pagination
      });
    } else {
      res.status(500).json({ success: false, message: result.message });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// GET /api/transactions/:userId/category/:category - Get transactions by category
router.get('/:userId/category/:category', async (req, res) => {
  try {
    const { userId, category } = req.params;
    const options = {
      startDate: req.query.startDate,
      endDate: req.query.endDate,
      limit: req.query.limit || 100,
      skip: req.query.skip || 0
    };

    const result = await dbService.getTransactionsByCategory(userId, category, options);

    if (result.success) {
      res.json({
        success: true,
        data: result.data,
        pagination: result.pagination
      });
    } else {
      res.status(500).json({ success: false, message: result.message });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// GET /api/transactions/:userId/summary - Get summary statistics
router.get('/:userId/summary', async (req, res) => {
  try {
    const { userId } = req.params;
    const { startDate, endDate } = req.query;

    const result = await dbService.getSummary(userId, startDate, endDate);

    if (result.success) {
      res.json({
        success: true,
        data: result.data
      });
    } else {
      res.status(500).json({ success: false, message: result.message });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// GET /api/transactions/:userId/categories - Get all categories
router.get('/:userId/categories', async (req, res) => {
  try {
    const { userId } = req.params;
    const result = await dbService.getCategories(userId);

    if (result.success) {
      res.json({
        success: true,
        data: result.data
      });
    } else {
      res.status(500).json({ success: false, message: result.message });
    }
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// POST /api/transactions/import - Import transactions from JSON file
router.post('/import', async (req, res) => {
  const { filePath, userId } = req.body;

  if (!filePath || !userId) {
    return res.status(400).json({
      success: false,
      message: 'filePath and userId are required'
    });
  }

  let fullPath = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath);

  try {
    await fs.access(fullPath);
  } catch {
    return res.status(404).json({
      success: false,
      message: `File not found: ${fullPath}`
    });
  }

  let transactions;
  try {
    const fileContent = await fs.readFile(fullPath, 'utf-8');
    transactions = JSON.parse(fileContent);
  } catch (err) {
    return res.status(400).json({
      success: false,
      message: 'Failed to read or parse JSON file'
    });
  }

  // Assign userId safely
  transactions = transactions.map(t => ({ ...t, userId }));

  // Wrap db insertion in try-catch to prevent crash
  try {
    const result = await dbService.insertTransactions(transactions);
    res.json({
      success: true,
      message: 'Transactions imported successfully',
      stats: {
        inserted: result.inserted || 0,
        duplicates: result.duplicates || 0,
        errors: result.errors || 0,
        total: transactions.length
      }
    });
  } catch (err) {
    console.error('Database insert error:', err);
    res.status(500).json({
      success: false,
      message: 'Failed to import transactions, see server logs'
    });
  }
});
