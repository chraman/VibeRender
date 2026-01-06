import { getChannelById } from "@/lib/db/queries/channels";
import { CreateVideoJob } from "@/components/jobs/CreateVideoJob";
import { JobList } from "@/components/jobs/JobList";

export default async function ChannelPage({
  params,
}: {
  params: Promise<{ channelId: string }>;
}) {
  const { channelId } = await params;

  const channel = await getChannelById(channelId);

  if (!channel) {
    return <div className="p-8">Channel not found</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 px-8 py-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-900">
          {channel.name}
        </h1>
        <p className="text-sm text-slate-500">
          {channel.category} • {channel.subNiche}
        </p>
      </div>

      {/* Workspace */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left: Create Job */}
        <CreateVideoJob channel={channel} />

        {/* Right: Job List */}
        <JobList jobs={channel.jobs ?? []} />
      </div>
    </div>
  );
}
