/**
 * Simple database setup script
 * Creates the jobs table if it doesn't exist
 * 
 * Run with: npm run db:setup
 * Or use: npm run db:push (recommended - uses Drizzle)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Check if .env.local exists
const envPath = path.join(__dirname, '..', '.env.local');
if (!fs.existsSync(envPath)) {
  console.error('❌ .env.local not found!');
  console.error('Create web-app/.env.local with:');
  console.error('DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viberender');
  process.exit(1);
}

console.log('📦 Using Drizzle to set up database...');
console.log('Running: npm run db:push\n');

try {
  execSync('npm run db:push', { 
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit'
  });
  console.log('\n✓ Database setup complete!');
} catch (error) {
  console.error('\n❌ Setup failed. Make sure:');
  console.error('1. Docker containers are running: docker-compose up -d');
  console.error('2. .env.local exists with correct DATABASE_URL');
  process.exit(1);
}
