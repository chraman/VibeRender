
import { db } from "@/lib/db"; // your Drizzle DB instance
import { eq } from "drizzle-orm";
import { jobs, jobStatusEnum } from "@/lib/db/schema";
import type { Job, NewJob } from "@/lib/db/schema";
import type { JobStatus } from "@/lib/db/schema";
import { desc } from 'drizzle-orm';
/** Create a new job */
export const createJob = async (job: NewJob): Promise<Job> => {
  const inserted = await db.insert(jobs).values(job).returning();
  return inserted[0];
};

/** Get a job by ID */
export const getJobById = async (id: string): Promise<Job | null> => {
  const results = await db.select().from(jobs).where(eq(jobs.id, id));
  return results[0] ?? null;
};

/** Get all jobs for a specific channel */
export const getJobsByChannel = async (channelId: string): Promise<Job[]> => {
  return await db.select().from(jobs).where(eq(jobs.channelId, channelId));
};

/** Get jobs by status */
export const getJobsByStatus = async (status: JobStatus): Promise<Job[]> => {
  return await db.select().from(jobs).where(eq(jobs.status, status));
};

/** Update the status of a job */
export const updateJobStatus = async (id: string, status: JobStatus): Promise<Job | null> => {
  const updated = await db
    .update(jobs)
    .set({ status, updatedAt: new Date() })
    .where(eq(jobs.id, id))
    .returning();
  return updated[0] ?? null;
};

/** Delete a job by ID */
export const deleteJob = async (id: string): Promise<Job | null> => {
  const deleted = await db.delete(jobs).where(eq(jobs.id, id)).returning();
  return deleted[0] ?? null;
};

/** Fetch latest jobs, optionally filtered by status */
export const getLatestJobs = async (limit = 10, status?: JobStatus): Promise<Job[]> => {
  let query = db.select().from(jobs).
  where(status ? eq(jobs.status, status) : undefined).orderBy(desc(jobs.createdAt)).limit(limit);
  return query;
};