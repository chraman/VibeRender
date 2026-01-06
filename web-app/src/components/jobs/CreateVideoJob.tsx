"use client";

import { useState } from "react";
import type { Channel } from "@/lib/db/schema/channels";

interface Props {
  channel: Channel;
}

export function CreateVideoJob({ channel }: Props) {
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    topic: "",
    videoTheme: "",
    emotionalGoal: "",
    pacing: "",
  });

  const canSubmit =
    form.topic.trim() &&
    form.videoTheme.trim() &&
    form.emotionalGoal.trim();

  const submit = async () => {
    setLoading(true);

    await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channelId: channel.id,
        ...form,
      }),
    });

    setLoading(false);
    setForm({
      topic: "",
      videoTheme: "",
      emotionalGoal: "",
      pacing: "",
    });
  };

  return (
    <div className="mx-auto max-w-xl rounded-2xl bg-white px-6 py-6 shadow-sm">
      {/* Header */}
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900">
          Create Video Job
        </h2>
        <p className="text-sm text-slate-500">
          Define what the AI should generate for this channel
        </p>
      </div>

      {/* Video Idea */}
      <div className="mb-6">
        <label className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-500">
          Video Idea
        </label>
        <input
          placeholder="e.g. The Annabelle Doll explained"
          value={form.topic}
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
          className="w-full rounded-xl border px-4 py-3 text-base focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Creative Direction */}
      <div className="mb-6">
        <div className="mb-3 text-xs font-medium uppercase tracking-wide text-slate-500">
          Creative Direction
        </div>

        <div className="space-y-3">
          <input
            placeholder="Video theme (e.g. VHS Found Footage)"
            value={form.videoTheme}
            onChange={(e) =>
              setForm({ ...form, videoTheme: e.target.value })
            }
            className="w-full rounded-lg border px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
          />

          <input
            placeholder="Emotional goal (e.g. Make viewer feel paranoid)"
            value={form.emotionalGoal}
            onChange={(e) =>
              setForm({ ...form, emotionalGoal: e.target.value })
            }
            className="w-full rounded-lg border px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
          />

          <input
            placeholder="Pacing (optional)"
            value={form.pacing}
            onChange={(e) =>
              setForm({ ...form, pacing: e.target.value })
            }
            className="w-full rounded-lg border px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Action */}
      <div className="flex justify-end">
        <button
          disabled={!canSubmit || loading}
          onClick={submit}
          className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Generate Video Job"}
        </button>
      </div>
    </div>
  );
}
