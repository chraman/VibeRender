/**
 * Quick test script to verify worker can see jobs
 * Run with: node scripts/test-worker.js
 */

const { execSync } = require('child_process');
const path = require('path');

console.log('🔍 Testing Worker Connection...\n');

// Test 1: Check if database is accessible
console.log('1. Checking database connection...');
try {
  const result = execSync(
    'docker exec viberender-new-postgres psql -U postgres -d viberender_new -c "SELECT COUNT(*) FROM jobs;"',
    { encoding: 'utf-8', stdio: 'pipe' }
  );
  console.log('   ✅ Database is accessible');
  console.log('   Result:', result.trim());
} catch (error) {
  console.log('   ❌ Cannot connect to database');
  console.log('   Make sure: docker-compose up -d');
  process.exit(1);
}

// Test 2: Check pending jobs
console.log('\n2. Checking for pending jobs...');
try {
  const result = execSync(
    'docker exec viberender-new-postgres psql -U postgres -d viberender_new -t -c "SELECT COUNT(*) FROM jobs WHERE status = \'pending\';"',
    { encoding: 'utf-8', stdio: 'pipe' }
  );
  const count = parseInt(result.trim());
  if (count > 0) {
    console.log(`   ⚠️  Found ${count} pending job(s) - worker should pick these up`);
  } else {
    console.log('   ✅ No pending jobs (this is normal if worker is running)');
  }
} catch (error) {
  console.log('   ❌ Error checking jobs');
}

// Test 3: Show recent jobs
console.log('\n3. Recent jobs (last 5):');
try {
  const result = execSync(
    'docker exec viberender-new-postgres psql -U postgres -d viberender_new -c "SELECT id, topic, status, created_at FROM jobs ORDER BY id DESC LIMIT 5;"',
    { encoding: 'utf-8', stdio: 'pipe' }
  );
  console.log(result);
} catch (error) {
  console.log('   ❌ Error fetching jobs');
}

console.log('\n✅ Test complete!');
console.log('\n💡 Tips:');
console.log('   - If you see pending jobs, make sure the worker is running');
console.log('   - Worker should pick up jobs within 5 seconds');
console.log('   - Check worker console for processing messages');

