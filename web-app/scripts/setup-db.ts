/**
 * Database setup script
 * Run this to initialize the database schema
 * Usage: npx tsx scripts/setup-db.ts
 */

import { db } from '../src/lib/db';
import { sql } from 'drizzle-orm';

async function setupDatabase() {
  try {
    console.log('Setting up database schema...');
    
    // Create the jobs table if it doesn't exist
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS jobs (
        id SERIAL PRIMARY KEY,
        topic TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
      );
    `);
    
    console.log('Database schema created successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Error setting up database:', error);
    process.exit(1);
  }
}

setupDatabase();

