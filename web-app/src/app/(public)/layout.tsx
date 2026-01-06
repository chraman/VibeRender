// Public layout (no sidebar, no auth check)
export default function PublicLayout({
    children,
  }: {
    children: React.ReactNode;
  }) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        {children}
      </div>
    );
  }
  