import Link from "next/link";

export default function Sidebar() {
  return (
    <aside className="w-64 bg-black text-white p-4">
      <h2 className="text-lg font-bold mb-6">Dashboard</h2>

      <nav className="space-y-2">
        <Link href="/dashboard">Channels</Link>
      </nav>
    </aside>
  );
}
