import ChannelCard from "@/components/channels/ChannelCard";

const mockChannels = [
  { id: "1", name: "YouTube Channel" },
  { id: "2", name: "Instagram Page" },
];

export default function DashboardPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Your Channels</h1>

        <a
          href="/dashboard/channels/create"
          className="bg-black text-white px-4 py-2 rounded"
        >
          + Create / Link Channel
        </a>
      </div>

      {/* <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mockChannels.map((channel) => (
          // <ChannelCard key={channel.id} channel={channel} />
        ))}
      </div> */}
    </div>
  );
}
