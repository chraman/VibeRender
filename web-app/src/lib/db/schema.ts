import { pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core';

// Jobs table schema for video generation tasks
export const jobs = pgTable('jobs', {
  id: serial('id').primaryKey(),
  topic: text('topic').notNull(),
  status: text('status').default('pending').notNull(), // pending, processing, completed, failed
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export type Job = typeof jobs.$inferSelect;
export type NewJob = typeof jobs.$inferInsert;

