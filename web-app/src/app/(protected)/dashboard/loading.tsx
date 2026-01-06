/**
 * Loading UI for /dashboard route
 * Automatically shown while page data is loading
 */
export default function DashboardLoading() {
  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold mb-4">
        Loading dashboard...
      </h2>

      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
        <div className="h-4 bg-gray-200 rounded w-2/3 animate-pulse" />
      </div>
    </div>
  );
}
