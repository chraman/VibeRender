import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

// Get database URL from environment variables
const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/viberender_new';

// Create the connection
const client = postgres(connectionString);

// Create the Drizzle instance with schema
export const db = drizzle(client, { schema });

