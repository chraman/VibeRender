import { pgEnum } from "drizzle-orm/pg-core";

/**
 * Job lifecycle states
 */
export const jobStatusEnum = pgEnum("job_status", [
  "pending",
  "processing",
  "completed",
  "failed",
]);
const jobStatuses = ["pending", "processing", "completed", "failed"] as const;

export type JobStatus = (typeof jobStatuses)[number];