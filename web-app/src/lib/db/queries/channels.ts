import { db } from "@/lib/db";
import { channels, jobs } from "@/lib/db/schema";
import { eq, desc, count } from "drizzle-orm";

/**
 * Get all channels for a specific user
 * Used on dashboard page
 */
export async function getUserChannels(userId: string) {
  return db.query.channels.findMany({
    where: eq(channels.userId, userId),
    orderBy: desc(channels.createdAt),
    with: {
      jobs: true,
    },
  });
}

/**
 * Get a single channel by ID (with jobs)
 */
export async function getChannelById(channelId: string) {
  return db.query.channels.findFirst({
    where: eq(channels.id, channelId),
    with: {
      jobs: {
        orderBy: desc(jobs.createdAt),
      },
    },
  });
}

/**
 * Create a new channel
 */
export async function createChannel(params: {
  userId: string;
  name: string;
  platform?: string;
}) {
  const [channel] = await db
    .insert(channels)
    .values({
      userId: params.userId,
      name: params.name,
      platform: params.platform,
    })
    .returning();

  return channel;
}

/**
 * Delete channel (jobs will cascade)
 */
export async function deleteChannel(channelId: string) {
  await db
    .delete(channels)
    .where(eq(channels.id, channelId));
}

/**
 * Get job stats for a channel
 * Used for dashboard cards
 */
export async function getChannelStats(channelId: string) {
  const result = await db
    .select({
      totalJobs: count(jobs.id),
    })
    .from(jobs)
    .where(eq(jobs.channelId, channelId));

  return {
    totalJobs: result[0]?.totalJobs ?? 0,
  };
}
