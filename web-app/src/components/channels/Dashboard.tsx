"use client";

import { useState } from "react";
import { ChannelCard } from "./ChannelCard";
import { CreateChannelModal } from "./CreateChannelModal";
import type { Channel } from "@/lib/db/schema/channels";

interface Props {
  channels: Channel[];
}

export default function Dashboard({ channels: initialChannels }: Props) {
  const [channels, setChannels] = useState(initialChannels);

  const handleCreateChannel = async (name: string) => {
    const res = await fetch("/api/channels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    if (!res.ok) return;

    const newChannel: Channel = await res.json();
    setChannels((prev) => [newChannel, ...prev]);
  };

  return (
    <div className="min-h-screen bg-slate-50 px-8 py-6">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Your Channels
          </h1>
          <p className="text-sm text-slate-500">
            Manage and monitor your content pipelines
          </p>
        </div>

        <CreateChannelModal onCreate={handleCreateChannel} />
      </div>

      {/* Channels Grid */}
      {channels.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-white p-12 text-center text-slate-500">
          No channels yet. Create your first channel to get started.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {channels.map((channel) => (
            <ChannelCard key={channel.id} channel={channel} />
          ))}
        </div>
      )}
    </div>
  );
}
