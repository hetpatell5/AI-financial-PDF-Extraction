const mongoose = require('mongoose');

const transactionSchema = new mongoose.Schema({
  id: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  date: {
    type: Date,
    required: true,
    index: true
  },
  description: {
    type: String,
    required: true
  },
  amount: {
    type: Number,
    required: true,
    min: 0
  },
  type: {
    type: String,
    required: true,
    enum: ['Credit', 'Debit']
  },
  category: {
    type: String,
    required: true,
    index: true,
    default: 'Other'
  },
  balance: {
    type: Number,
    default: null
  },
  raw_line: {
    type: String,
    default: null
  }
}, {
  timestamps: true
});

// Compound indexes for common queries
transactionSchema.index({ userId: 1, date: -1 });
transactionSchema.index({ userId: 1, category: 1 });
transactionSchema.index({ userId: 1, type: 1 });
transactionSchema.index({ userId: 1, date: -1, category: 1 });

// Virtual for formatted amount
transactionSchema.virtual('formattedAmount').get(function() {
  return `₹${this.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
});

// Method to check for duplicate
transactionSchema.statics.isDuplicate = async function(transactionId) {
  const exists = await this.findOne({ id: transactionId });
  return !!exists;
};

// Method to get user statistics
transactionSchema.statics.getUserStats = async function(userId, startDate, endDate) {
  const match = { userId };
  
  if (startDate || endDate) {
    match.date = {};
    if (startDate) match.date.$gte = new Date(startDate);
    if (endDate) match.date.$lte = new Date(endDate);
  }

  const stats = await this.aggregate([
    { $match: match },
    {
      $group: {
        _id: '$type',
        total: { $sum: '$amount' },
        count: { $sum: 1 }
      }
    }
  ]);

  const result = {
    totalCredit: 0,
    totalDebit: 0,
    creditCount: 0,
    debitCount: 0,
    netAmount: 0
  };

  stats.forEach(stat => {
    if (stat._id === 'Credit') {
      result.totalCredit = stat.total;
      result.creditCount = stat.count;
    } else if (stat._id === 'Debit') {
      result.totalDebit = stat.total;
      result.debitCount = stat.count;
    }
  });

  result.netAmount = result.totalCredit - result.totalDebit;
  return result;
};

const Transaction = mongoose.model('Transaction', transactionSchema);

module.exports = Transaction;