/**
 * Dashboard layout with chat sidebar.
 */

import { ChatSidebar } from "@/components/layout/chat-sidebar"
import { ChatSidebarToggle } from "@/components/layout/chat-sidebar-toggle"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="relative flex min-h-screen">
      {/* Main Content Area */}
      <main className="flex-1">
        {children}
      </main>

      {/* Chat Sidebar (opens on right side) */}
      <ChatSidebar />

      {/* Toggle Button */}
      <ChatSidebarToggle />
    </div>
  )
}
