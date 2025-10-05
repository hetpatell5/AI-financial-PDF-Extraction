const http = require('http');

const BASE_URL = 'http://localhost:3000';
const TEST_USER_ID = 'user123';

// Helper function to make HTTP requests
function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      
      res.on('data', (chunk) => {
        body += chunk;
      });
      
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          resolve({ statusCode: res.statusCode, data: response });
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: body });
        }
      });
    });
    
    req.on('error', reject);
    
    if (data) {
      req.write(JSON.stringify(data));
    }
    
    req.end();
  });
}

// Test functions
async function testHealthCheck() {
  console.log('\n📋 Test 1: Health Check');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: '/health',
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Response:', JSON.stringify(response.data, null, 2));
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testGetAllTransactions() {
  console.log('\n📋 Test 2: Get All Transactions');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}?limit=10`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Total transactions:', response.data.pagination?.total || 0);
    console.log('Returned:', response.data.data?.length || 0);
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testGetMonthlyTransactions() {
  console.log('\n📋 Test 3: Get Monthly Transactions');
  console.log('─'.repeat(50));
  
  try {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}/month/${year}/${month}`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log(`Period: ${year}-${month}`);
    console.log('Transactions found:', response.data.data?.length || 0);
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testGetByCategory() {
  console.log('\n📋 Test 4: Get Transactions by Category');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}/category/Food`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Category: Food');
    console.log('Transactions found:', response.data.data?.length || 0);
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testGetSummary() {
  console.log('\n📋 Test 5: Get Summary Statistics');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}/summary`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    if (response.data.data?.overview) {
      console.log('Total Credit:', response.data.data.overview.totalCredit);
      console.log('Total Debit:', response.data.data.overview.totalDebit);
      console.log('Net Amount:', response.data.data.overview.netAmount);
      console.log('Categories:', response.data.data.categories?.length || 0);
    }
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testGetCategories() {
  console.log('\n📋 Test 6: Get All Categories');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}/categories`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Categories:', response.data.data?.join(', ') || 'None');
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testFilterByDateRange() {
  console.log('\n📋 Test 7: Filter by Date Range');
  console.log('─'.repeat(50));
  
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 1);
    
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}?startDate=${startDate.toISOString().split('T')[0]}&endDate=${endDate.toISOString().split('T')[0]}`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Date Range:', startDate.toISOString().split('T')[0], 'to', endDate.toISOString().split('T')[0]);
    console.log('Transactions found:', response.data.data?.length || 0);
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

async function testFilterByType() {
  console.log('\n📋 Test 8: Filter by Transaction Type');
  console.log('─'.repeat(50));
  
  try {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: `/api/transactions/${TEST_USER_ID}?type=Debit&limit=5`,
      method: 'GET'
    };
    
    const response = await makeRequest(options);
    console.log('Status:', response.statusCode);
    console.log('Type: Debit');
    console.log('Transactions found:', response.data.data?.length || 0);
    console.log(response.statusCode === 200 ? '✅ PASS' : '❌ FAIL');
  } catch (error) {
    console.log('❌ FAIL:', error.message);
  }
}

// Run all tests
async function runAllTests() {
  console.log('\n' + '='.repeat(60));
  console.log('🧪 Running API Tests');
  console.log('='.repeat(60));
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Test User: ${TEST_USER_ID}`);
  
  await testHealthCheck();
  await testGetAllTransactions();
  await testGetMonthlyTransactions();
  await testGetByCategory();
  await testGetSummary();
  await testGetCategories();
  await testFilterByDateRange();
  await testFilterByType();
  
  console.log('\n' + '='.repeat(60));
  console.log('✅ All tests completed!');
  console.log('='.repeat(60) + '\n');
}

// Check if server is running
http.get(`${BASE_URL}/health`, (res) => {
  runAllTests();
}).on('error', () => {
  console.error('\n❌ Error: API server is not running!');
  console.error('Please start the server first: npm run dev\n');
  process.exit(1);
});