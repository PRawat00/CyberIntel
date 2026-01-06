"use client"

import { usePathname, useRouter } from "next/navigation"
import { Package, Plug, Settings } from "lucide-react"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { cn } from "@/lib/utils"

interface NavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  path: string
}

const navItems: NavItem[] = [
  {
    id: "dependencies",
    label: "Dependencies",
    icon: Package,
    path: "/dashboard/dependencies",
  },
  {
    id: "integrations",
    label: "Integrations",
    icon: Plug,
    path: "/dashboard/integrations",
  },
]

const bottomNavItem: NavItem = {
  id: "settings",
  label: "Settings",
  icon: Settings,
  path: "/dashboard/settings",
}

export function SidebarL1() {
  const pathname = usePathname()
  const router = useRouter()
  const { expandL2 } = useNavigationState()

  const isActive = (path: string) => {
    return pathname.startsWith(path)
  }

  const handleNavClick = (path: string) => {
    expandL2()
    router.push(path)
  }

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-20 bg-card border-r border-border flex flex-col items-center py-6 z-40">
      {/* Main Navigation Items */}
      <nav className="flex flex-col gap-4 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = isActive(item.path)

          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.path)}
              className={cn(
                "group relative flex flex-col items-center justify-center w-14 h-14 rounded-lg transition-all duration-200",
                "hover:bg-muted",
                active
                  ? "bg-brand-600/10 text-brand-400"
                  : "text-slate-400 hover:text-slate-200"
              )}
              title={item.label}
            >
              {/* Active Indicator */}
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-brand-500 rounded-r-full" />
              )}

              <Icon className={cn("h-6 w-6 transition-transform", active && "scale-110")} />

              <span className="text-xs font-medium mt-1">{item.label.slice(0, 4)}</span>

              {/* Tooltip */}
              <div className="absolute left-full ml-2 px-3 py-2 bg-background border border-border rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap text-sm font-medium shadow-lg z-50">
                {item.label}
              </div>
            </button>
          )
        })}
      </nav>

      {/* Bottom Navigation (Settings) */}
      <nav className="flex flex-col gap-4">
        {(() => {
          const Icon = bottomNavItem.icon
          const active = isActive(bottomNavItem.path)

          return (
            <button
              key={bottomNavItem.id}
              onClick={() => handleNavClick(bottomNavItem.path)}
              className={cn(
                "group relative flex flex-col items-center justify-center w-14 h-14 rounded-lg transition-all duration-200",
                "hover:bg-muted",
                active
                  ? "bg-brand-600/10 text-brand-400"
                  : "text-slate-400 hover:text-slate-200"
              )}
              title={bottomNavItem.label}
            >
              {/* Active Indicator */}
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-brand-500 rounded-r-full" />
              )}

              <Icon className={cn("h-6 w-6 transition-transform", active && "scale-110")} />

              <span className="text-xs font-medium mt-1">{bottomNavItem.label.slice(0, 4)}</span>

              {/* Tooltip */}
              <div className="absolute left-full ml-2 px-3 py-2 bg-background border border-border rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap text-sm font-medium shadow-lg z-50">
                {bottomNavItem.label}
              </div>
            </button>
          )
        })()}
      </nav>
    </aside>
  )
}
