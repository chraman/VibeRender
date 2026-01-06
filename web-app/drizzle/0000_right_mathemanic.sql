CREATE TABLE "jobs" (
	"id" serial PRIMARY KEY NOT NULL,
	"topic" text NOT NULL,
	"status" text DEFAULT 'pending' NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
