import type { Channel } from "@/lib/db/schema/channels";
import Link from "next/link";
interface Props {
  channel: Channel;
}

export function ChannelCard({ channel }: Props) {
  return (
    <Link
      href={`/dashboard/channels/${channel.id}`} className="group relative rounded-xl border bg-white p-6 shadow-sm transition hover:shadow-md">
      <h3 className="mb-2 text-lg font-medium text-slate-900">
        {channel.name}
      </h3>

      <p className="text-xs text-slate-500 break-all">
        Category
      </p>
      <p className="text-sm text-slate-600 break-all">
        {channel.category}
      </p>      
      <p className="text-xs text-slate-500 break-all">
        Sub Niche
      </p>
      <p className="text-sm text-slate-600 break-all">
        {channel.subNiche}
      </p>

      {/* Hover action hint */}
      <div className="pointer-events-none absolute inset-0 rounded-xl ring-1 ring-transparent group-hover:ring-slate-200" />
    </Link>
  );
}
