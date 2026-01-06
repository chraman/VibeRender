import Sidebar from "@/components/layout/Sidebar";

// This layout wraps ALL protected pages
export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 p-6 bg-gray-50">
        {children}
      </main>
    </div>
  );
}
