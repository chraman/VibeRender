"use client";

/**
 * This file acts as an error boundary for the /dashboard route.
 * It catches runtime errors and displays a fallback UI.
 */

export default function DashboardError({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-2">
        Something went wrong
      </h2>

      <p className="text-gray-600 mb-4">
        {error.message}
      </p>

      <button
        onClick={() => reset()}
        className="bg-black text-white px-4 py-2 rounded"
      >
        Try again
      </button>
    </div>
  );
}
