'use server';

import { db } from '@/lib/db';
import { jobs } from '@/lib/db/schema';
import { revalidatePath } from 'next/cache';
import { desc } from 'drizzle-orm';

/**
 * Server Action to add a new video generation job
 * @param topic - The topic for the video to generate
 * @returns The created job or an error
 */
export async function createJob(topic: string) {
  try {
    if (!topic || topic.trim().length === 0) {
      return { success: false, error: 'Topic cannot be empty' };
    }

    // Insert the new job into the database
    const [newJob] = await db
      .insert(jobs)
      .values({
        topic: topic.trim(),
        status: 'pending',
      })
      .returning();

    // Revalidate the page to show the new job
    revalidatePath('/');

    return { success: true, job: newJob };
  } catch (error) {
    console.error('Error creating job:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create job',
    };
  }
}

/**
 * Server Action to get all jobs
 * @returns List of all jobs ordered by creation date (newest first)
 */
export async function getAllJobs() {
  try {
    const allJobs = await db
      .select()
      .from(jobs)
      .orderBy(desc(jobs.createdAt));

    return { success: true, jobs: allJobs };
  } catch (error) {
    console.error('Error fetching jobs:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch jobs',
      jobs: [],
    };
  }
}
