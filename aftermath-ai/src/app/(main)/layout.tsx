import { NavTabs } from "@/components/nav-tabs";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex flex-col min-h-screen bg-[#fafaf9] md:pt-16 pb-16 md:pb-0">
      <NavTabs />
      <main className="flex-1 w-full max-w-lg mx-auto p-4">
        {children}
      </main>
    </div>
  );
}
