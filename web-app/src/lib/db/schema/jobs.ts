import {
  pgTable,
  uuid,
  text,
  timestamp,
  index,
} from "drizzle-orm/pg-core";
import { channels } from "./channels";
import { jobStatusEnum } from "./enums";

/**
 * Jobs table
 * Each job belongs to exactly one channel
 */
export const jobs = pgTable(
  "jobs",
  {
    id: uuid("id").defaultRandom().primaryKey(),

    channelId: uuid("channel_id")
      .notNull()
      .references(() => channels.id, { onDelete: "cascade" }),

    topic: text("topic").notNull(),

    status: jobStatusEnum("status")
      .default("pending")
      .notNull(),

    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at")
      .defaultNow()
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => ({
    channelIdx: index("jobs_channel_idx").on(table.channelId),
    statusIdx: index("jobs_status_idx").on(table.status),
  })
);

export type Job = typeof jobs.$inferSelect;
export type NewJob = typeof jobs.$inferInsert;
