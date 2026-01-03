'use client';

import { useState, useEffect } from 'react';
import { createJob, getAllJobs } from './actions/jobs';

type Job = {
  id: number;
  topic: string;
  status: string;
  createdAt: Date | null;
  updatedAt: Date | null;
};

export default function Home() {
  const [topic, setTopic] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);

  // Load jobs on mount and refresh periodically
  useEffect(() => {
    loadJobs();
    // Refresh jobs every 3 seconds to see status updates
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  async function loadJobs() {
    const result = await getAllJobs();
    if (result.success && result.jobs) {
      setJobs(result.jobs);
    }
    setIsLoadingJobs(false);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    try {
      const result = await createJob(topic);
      if (result.success) {
        setMessage({ type: 'success', text: `Video job created for: ${result.job?.topic}` });
        setTopic('');
        // Reload jobs to show the new one
        await loadJobs();
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to create job' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'An unexpected error occurred' });
    } finally {
      setIsSubmitting(false);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200';
      case 'processing':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
      case 'completed':
        return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
      default:
        return 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200';
    }
  }

  function formatDate(date: Date | null) {
    if (!date) return 'N/A';
    return new Date(date).toLocaleString();
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-4xl flex-col items-center py-16 px-8 bg-white dark:bg-black">
        <div className="flex flex-col items-center gap-8 text-center w-full">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-black dark:text-zinc-50">
            VibeRender
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            AI-powered YouTube automation SaaS. Generate videos from any topic.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-md">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="topic"
                className="text-sm font-medium text-zinc-700 dark:text-zinc-300 text-left"
              >
                Topic
              </label>
              <input
                id="topic"
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic for your video..."
                className="w-full px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-black dark:text-zinc-50 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-500 dark:focus:ring-zinc-400"
                disabled={isSubmitting}
                required
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !topic.trim()}
              className="w-full h-12 rounded-full bg-black dark:bg-white text-white dark:text-black font-medium transition-colors hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating...' : 'Generate Video'}
            </button>

            {message && (
              <div
                className={`mt-2 px-4 py-3 rounded-lg text-sm ${
                  message.type === 'success'
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                }`}
              >
                {message.text}
              </div>
            )}
          </form>

          {/* Jobs List */}
          <div className="w-full max-w-2xl mt-8">
            <h2 className="text-2xl font-semibold text-black dark:text-zinc-50 mb-4 text-left">
              Job Status
            </h2>
            {isLoadingJobs ? (
              <div className="text-zinc-600 dark:text-zinc-400">Loading jobs...</div>
            ) : jobs.length === 0 ? (
              <div className="text-zinc-600 dark:text-zinc-400">
                No jobs yet. Create your first video job above!
              </div>
            ) : (
              <div className="space-y-3">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-black dark:text-zinc-50">
                            #{job.id} - {job.topic}
                          </span>
                        </div>
                        <div className="text-xs text-zinc-500 dark:text-zinc-400">
                          Created: {formatDate(job.createdAt)} | Updated: {formatDate(job.updatedAt)}
                        </div>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(
                          job.status
                        )}`}
                      >
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
