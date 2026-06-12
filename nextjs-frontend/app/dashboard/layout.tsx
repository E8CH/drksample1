import NavBar from "@/components/layout/NavBar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-dalock-surface">
      <NavBar />
      <main className="pt-14">{children}</main>
    </div>
  );
}
