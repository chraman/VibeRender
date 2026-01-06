import { relations } from "drizzle-orm";
import { users } from "./users";
import { channels } from "./channels";
import { jobs } from "./jobs";

export const usersRelations = relations(users, ({ many }) => ({
  channels: many(channels),
}));

export const channelsRelations = relations(channels, ({ one, many }) => ({
  user: one(users, {
    fields: [channels.userId],
    references: [users.id],
  }),
  jobs: many(jobs),
}));

export const jobsRelations = relations(jobs, ({ one }) => ({
  channel: one(channels, {
    fields: [jobs.channelId],
    references: [channels.id],
  }),
}));
