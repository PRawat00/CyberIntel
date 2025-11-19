"use client"

import { User, Bell, Key, Shield, Palette } from "lucide-react"
import { cn } from "@/lib/utils"

const settingsCategories = [
  {
    id: "profile",
    name: "Profile",
    icon: User,
    description: "Manage your account",
  },
  {
    id: "notifications",
    name: "Notifications",
    icon: Bell,
    description: "Alert preferences",
  },
  {
    id: "api-keys",
    name: "API Keys",
    icon: Key,
    description: "Manage API access",
  },
  {
    id: "security",
    name: "Security",
    icon: Shield,
    description: "Authentication & security",
  },
  {
    id: "appearance",
    name: "Appearance",
    icon: Palette,
    description: "Theme & display",
  },
]

export function SidebarL2Settings() {
  return (
    <div className="flex flex-col h-full p-4">
      <div className="space-y-2">
        {settingsCategories.map((category) => {
          const Icon = category.icon
          return (
            <button
              key={category.id}
              className={cn(
                "w-full flex items-start gap-3 p-3 rounded-lg border transition-all text-left",
                "border-dark-border hover:border-brand-500/50 hover:bg-dark-hover"
              )}
            >
              <Icon className="h-5 w-5 text-slate-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-slate-200">{category.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{category.description}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
