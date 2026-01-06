import type { Job } from "@/lib/db/schema/jobs";

interface Props {
  jobs: Job[];
}

const STATUS_COLORS: Record<Job["status"], string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function JobList({ jobs }: Props) {
  return (
    <div className="rounded-2xl bg-white px-6 py-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Video Jobs
        </h2>
        <p className="text-sm text-slate-500">
          Recent jobs for this channel
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className="text-sm text-slate-500">
          No jobs created yet.
        </div>
      ) : (
        <ul className="space-y-3">
          {jobs.map((job) => (
            <li
              key={job.id}
              className="flex items-center justify-between rounded-lg border px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {job.topic}
                </p>
                <p className="text-xs text-slate-500">
                  {job.videoTheme}
                </p>
                <p className="text-xs text-slate-500">
                  {job.emotionalGoal}
                </p>
                <p className="text-xs text-slate-500">
                  {new Date(job.createdAt).toLocaleString()}
                </p>
              </div>

              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_COLORS[job.status]}`}
              >
                {job.status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
