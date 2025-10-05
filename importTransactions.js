require('dotenv').config();
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const USER_ID = 'user123'; // Change if needed
const API_URL = 'http://localhost:3000/api/transactions/import';
const EXTRACTED_DIR = path.join(__dirname, 'extracted');

// Get all JSON files inside extracted/
const files = fs.readdirSync(EXTRACTED_DIR).filter(f => f.endsWith('.json'));

(async () => {
  for (const file of files) {
    const filePath = path.join(EXTRACTED_DIR, file);

    console.log(`📂 Importing file: ${filePath}`);

try {
  const res = await axios.post('http://localhost:3000/api/transactions/import', {
    filePath: file,
    userId
  });
  console.log(`✅ Imported ${file}:`, res.data);
} catch (err) {
  console.error(`❌ Failed ${path.basename(file)}:`);

  if (err.response) {
    console.error("Status:", err.response.status);
    console.error("Data:", err.response.data);
  } else if (err.request) {
    console.error("No response received from server");
    console.error(err.request);
  } else {
    console.error("Error message:", err.message);
  }
}}

  console.log("\n🎉 All files processed!");
})();
