const Transaction = require('../models/Transaction');

class DatabaseService {
  // Insert single transaction
  async insertTransaction(transactionData) {
    try {
      // Check for duplicate
      const exists = await Transaction.isDuplicate(transactionData.id);
      if (exists) {
        return { success: false, message: 'Transaction already exists', duplicate: true };
      }

      const transaction = new Transaction(transactionData);
      await transaction.save();
      
      return { success: true, data: transaction };
    } catch (error) {
      console.error('Error inserting transaction:', error);
      return { success: false, message: error.message };
    }
  }

  // Insert multiple transactions
  async insertTransactions(transactions) {
    try {
      const results = {
        inserted: 0,
        duplicates: 0,
        errors: 0,
        transactions: []
      };

      for (const transData of transactions) {
        const result = await this.insertTransaction(transData);
        
        if (result.success) {
          results.inserted++;
          results.transactions.push(result.data);
        } else if (result.duplicate) {
          results.duplicates++;
        } else {
          results.errors++;
        }
      }

      return results;
    } catch (error) {
      console.error('Error inserting transactions:', error);
      throw error;
    }
  }

  // Get transactions by user
  async getTransactionsByUser(userId, options = {}) {
    try {
      const query = { userId };
      
      // Build query based on options
      if (options.startDate || options.endDate) {
        query.date = {};
        if (options.startDate) {
          query.date.$gte = new Date(options.startDate);
        }
        if (options.endDate) {
          query.date.$lte = new Date(options.endDate);
        }
      }

      if (options.category) {
        query.category = options.category;
      }

      if (options.type) {
        query.type = options.type;
      }

      if (options.minAmount || options.maxAmount) {
        query.amount = {};
        if (options.minAmount) {
          query.amount.$gte = parseFloat(options.minAmount);
        }
        if (options.maxAmount) {
          query.amount.$lte = parseFloat(options.maxAmount);
        }
      }

      // Execute query with pagination
      const limit = parseInt(options.limit) || 100;
      const skip = parseInt(options.skip) || 0;
      const sort = options.sort || { date: -1 };

      const transactions = await Transaction.find(query)
        .sort(sort)
        .limit(limit)
        .skip(skip)
        .lean();

      const total = await Transaction.countDocuments(query);

      return {
        success: true,
        data: transactions,
        pagination: {
          total,
          limit,
          skip,
          hasMore: skip + transactions.length < total
        }
      };
    } catch (error) {
      console.error('Error fetching transactions:', error);
      return { success: false, message: error.message };
    }
  }

  // Get transactions by month
  async getTransactionsByMonth(userId, year, month) {
    try {
      const startDate = new Date(year, month - 1, 1);
      const endDate = new Date(year, month, 0, 23, 59, 59, 999);

      return await this.getTransactionsByUser(userId, {
        startDate,
        endDate
      });
    } catch (error) {
      console.error('Error fetching monthly transactions:', error);
      return { success: false, message: error.message };
    }
  }

  // Get transactions by category
  async getTransactionsByCategory(userId, category, options = {}) {
    try {
      return await this.getTransactionsByUser(userId, {
        ...options,
        category
      });
    } catch (error) {
      console.error('Error fetching category transactions:', error);
      return { success: false, message: error.message };
    }
  }

  // Get summary statistics
  async getSummary(userId, startDate, endDate) {
    try {
      const stats = await Transaction.getUserStats(userId, startDate, endDate);

      // Get category breakdown
      const match = { userId };
      if (startDate || endDate) {
        match.date = {};
        if (startDate) match.date.$gte = new Date(startDate);
        if (endDate) match.date.$lte = new Date(endDate);
      }

      const categoryStats = await Transaction.aggregate([
        { $match: match },
        {
          $group: {
            _id: { category: '$category', type: '$type' },
            total: { $sum: '$amount' },
            count: { $sum: 1 }
          }
        },
        {
          $group: {
            _id: '$_id.category',
            debit: {
              $sum: {
                $cond: [{ $eq: ['$_id.type', 'Debit'] }, '$total', 0]
              }
            },
            credit: {
              $sum: {
                $cond: [{ $eq: ['$_id.type', 'Credit'] }, '$total', 0]
              }
            },
            count: { $sum: '$count' }
          }
        },
        { $sort: { debit: -1 } }
      ]);

      return {
        success: true,
        data: {
          overview: stats,
          categories: categoryStats
        }
      };
    } catch (error) {
      console.error('Error fetching summary:', error);
      return { success: false, message: error.message };
    }
  }

  // Delete transactions by user
  async deleteUserTransactions(userId) {
    try {
      const result = await Transaction.deleteMany({ userId });
      return { success: true, deleted: result.deletedCount };
    } catch (error) {
      console.error('Error deleting transactions:', error);
      return { success: false, message: error.message };
    }
  }

  // Get all categories for a user
  async getCategories(userId) {
    try {
      const categories = await Transaction.distinct('category', { userId });
      return { success: true, data: categories };
    } catch (error) {
      console.error('Error fetching categories:', error);
      return { success: false, message: error.message };
    }
  }
}

module.exports = new DatabaseService();