import {
  pgTable,
  uuid,
  text,
  timestamp,
  index,
  pgEnum
} from "drizzle-orm/pg-core";
import { users } from "./users";

export const channelStatusEnum = pgEnum("channel_status", [
  "active",
  "paused",
  "archived",
]);
const channelStatuses = [ "active","paused","archived"] as const;

export type ChannelStatus = (typeof channelStatuses)[number];
/**
 * Channels table
 * Each channel belongs to exactly one user
 */
export const channels = pgTable(
  "channels",
  {
    id: uuid("id").defaultRandom().primaryKey(),

    userId: uuid("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),

    name: text("name").notNull(),
    platform: text("platform"), // youtube, instagram, etc.
    category: text("category"),
    subNiche: text("sub_niche"),
    targetAudience: text("target_audience"),
    contentFormat: text("content_format"),
    brandVoice: text("brand_voice"),

    forbiddenTopics: text("forbidden_topics").array(),

    status: channelStatusEnum("status").default("active"),
    createdAt: timestamp("created_at").defaultNow().notNull(),
    updatedAt: timestamp("updated_at")
      .defaultNow()
      .$onUpdate(() => new Date())
      .notNull(),
  },
  (table) => ({
    userIdx: index("channels_user_idx").on(table.userId),
  })
);

export type Channel = typeof channels.$inferSelect;
export type NewChannel = typeof channels.$inferInsert;
