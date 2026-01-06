/**
 * Dashboard layout with two-level sidebar system and chat sidebar.
 */

"use client"

import { usePathname } from "next/navigation"
import { ChatSidebar } from "@/components/layout/chat-sidebar"
import { ChatSidebarToggle } from "@/components/layout/chat-sidebar-toggle"
import { SidebarL1 } from "@/components/layout/sidebar-l1"
import { SidebarL2 } from "@/components/layout/sidebar-l2"
import { SidebarL2Dependencies } from "@/components/layout/sidebar-l2-dependencies"
import { SidebarL2Integrations } from "@/components/layout/sidebar-l2-integrations"
import { SidebarL2Settings } from "@/components/layout/sidebar-l2-settings"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { cn } from "@/lib/utils"
import { AuthLoadingWrapper } from "@/components/auth/auth-loading-wrapper"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { isL2Collapsed } = useNavigationState()

  // Determine which L2 sidebar content to show based on route
  const getL2Content = () => {
    if (pathname.startsWith("/dashboard/dependencies")) {
      return <SidebarL2Dependencies />
    } else if (pathname.startsWith("/dashboard/integrations")) {
      return <SidebarL2Integrations />
    } else if (pathname.startsWith("/dashboard/settings")) {
      return <SidebarL2Settings />
    } else if (pathname.startsWith("/dashboard/reports")) {
      return <SidebarL2Dependencies /> // Show scans list for reports too
    }
    // Default to dependencies for other dashboard pages
    return <SidebarL2Dependencies />
  }

  return (
    <AuthLoadingWrapper>
      <div className="min-h-screen overflow-hidden h-screen">
        {/* Level 1 Sidebar (Icon Navigation) */}
        <SidebarL1 />

        {/* Level 2 Sidebar (Context-Aware Content) */}
        <SidebarL2>{getL2Content()}</SidebarL2>

        {/* Main Content Area */}
        <main className={cn(
          "fixed top-16 bottom-0 overflow-hidden transition-all duration-300 ease-in-out",
          "right-[380px]",
          isL2Collapsed ? "left-20" : "left-[400px]"
        )}>
          {children}
        </main>

        {/* Chat Sidebar */}
        <ChatSidebar />
      </div>
    </AuthLoadingWrapper>
  )
}
