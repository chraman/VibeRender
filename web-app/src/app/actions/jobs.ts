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
  const startTime = Date.now();
  const trimmedTopic = topic.trim();
  
  console.log('[SERVER ACTION] createJob called');
  console.log(`  Topic: "${trimmedTopic}"`);
  console.log(`  Timestamp: ${new Date().toISOString()}`);
  
  try {
    if (!trimmedTopic || trimmedTopic.length === 0) {
      console.warn('[SERVER ACTION] createJob failed: Empty topic');
      return { success: false, error: 'Topic cannot be empty' };
    }

    console.log('[SERVER ACTION] Inserting job into database...');
    
    // Insert the new job into the database
    const [newJob] = await db
      .insert(jobs)
      .values({
        topic: trimmedTopic,
        status: 'pending',
      })
      .returning();

    const elapsedTime = Date.now() - startTime;
    console.log(`[SERVER ACTION] ✅ Job created successfully`);
    console.log(`  Job ID: ${newJob.id}`);
    console.log(`  Status: ${newJob.status}`);
    console.log(`  Time taken: ${elapsedTime}ms`);

    // Revalidate the page to show the new job
    revalidatePath('/');
    console.log('[SERVER ACTION] Page revalidated');

    return { success: true, job: newJob };
  } catch (error) {
    const elapsedTime = Date.now() - startTime;
    console.error(`[SERVER ACTION] ❌ Error creating job (${elapsedTime}ms):`, error);
    console.error('  Error details:', error instanceof Error ? error.message : 'Unknown error');
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
  const startTime = Date.now();
  console.log('[SERVER ACTION] getAllJobs called');
  
  try {
    console.log('[SERVER ACTION] Fetching jobs from database...');
    
    const allJobs = await db
      .select()
      .from(jobs)
      .orderBy(desc(jobs.createdAt));

    const elapsedTime = Date.now() - startTime;
    console.log(`[SERVER ACTION] ✅ Fetched ${allJobs.length} job(s) in ${elapsedTime}ms`);
    
    if (allJobs.length > 0) {
      const statusCounts = allJobs.reduce((acc, job) => {
        acc[job.status] = (acc[job.status] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      console.log(`[SERVER ACTION]   Status breakdown:`, statusCounts);
    }

    return { success: true, jobs: allJobs };
  } catch (error) {
    const elapsedTime = Date.now() - startTime;
    console.error(`[SERVER ACTION] ❌ Error fetching jobs (${elapsedTime}ms):`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch jobs',
      jobs: [],
    };
  }
}
