"use client"

import { usePathname } from "next/navigation"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface SidebarL2Props {
  children: React.ReactNode
}

export function SidebarL2({ children }: SidebarL2Props) {
  const { isL2Collapsed, toggleL2Sidebar } = useNavigationState()
  const pathname = usePathname()

  // Determine sidebar title based on current route
  const getSidebarTitle = () => {
    if (pathname.startsWith("/dashboard/dependencies")) {
      return "Dependencies"
    } else if (pathname.startsWith("/dashboard/integrations")) {
      return "Integrations"
    } else if (pathname.startsWith("/dashboard/settings")) {
      return "Settings"
    } else if (pathname.startsWith("/dashboard/reports")) {
      return "Reports"
    }
    return "Menu"
  }

  return (
    <aside
      className={cn(
        "fixed left-20 top-16 bottom-0 bg-card border-r border-border transition-all duration-300 ease-in-out z-30 flex flex-col",
        isL2Collapsed ? "w-0 opacity-0" : "w-80 opacity-100"
      )}
    >
      {/* Header with collapse button */}
      <div className="flex items-center justify-between p-4 border-b border-border min-h-[57px]">
        <h2 className={cn(
          "text-lg font-semibold text-slate-200 transition-opacity duration-200",
          isL2Collapsed && "opacity-0"
        )}>
          {getSidebarTitle()}
        </h2>

        <Button
          variant="ghost"
          size="icon"
          onClick={toggleL2Sidebar}
          className={cn(
            "h-8 w-8 text-slate-400 hover:text-slate-200 transition-opacity duration-200",
            isL2Collapsed && "opacity-0"
          )}
          title={isL2Collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isL2Collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Content */}
      <div className={cn(
        "flex-1 overflow-y-auto transition-opacity duration-200",
        isL2Collapsed && "opacity-0"
      )}>
        {!isL2Collapsed && children}
      </div>
    </aside>
  )
}

// Export a toggle button for mobile/responsive
export function SidebarL2Toggle() {
  const { isL2Collapsed, toggleL2Sidebar } = useNavigationState()

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleL2Sidebar}
      className="fixed left-20 top-20 z-40 h-8 w-8"
      title={isL2Collapsed ? "Expand sidebar" : "Collapse sidebar"}
    >
      {isL2Collapsed ? (
        <ChevronRight className="h-4 w-4" />
      ) : (
        <ChevronLeft className="h-4 w-4" />
      )}
    </Button>
  )
}
