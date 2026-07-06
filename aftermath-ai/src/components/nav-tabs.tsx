"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Calendar, MessageSquare, Users, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { name: "Today", href: "/app", icon: Home },
  { name: "Exams", href: "/app/exams", icon: Calendar },
  { name: "Companion", href: "/app/companion", icon: MessageSquare },
  { name: "Care Circle", href: "/app/care-circle", icon: Users },
  { name: "Judge Panel", href: "/app/reasoning", icon: Activity },
];

export function NavTabs() {
  const pathname = usePathname();

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-white border-t border-gray-200 shadow-sm md:top-0 md:bottom-auto md:border-t-0 md:border-b">
      <div className="grid h-full max-w-lg grid-cols-5 mx-auto font-medium">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "inline-flex flex-col items-center justify-center px-5 hover:bg-gray-50 group transition-colors",
                isActive ? "text-indigo-600" : "text-gray-500 hover:text-gray-900"
              )}
            >
              <Icon className="w-6 h-6 mb-1" />
              <span className="text-[10px]">{tab.name}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
