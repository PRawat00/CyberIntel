"use client"

import { Github, MessageSquare, Ticket } from "lucide-react"
import { cn } from "@/lib/utils"

const integrationCategories = [
  {
    title: "Version Control",
    items: [
      { id: "github", name: "GitHub", icon: Github, connected: true },
      { id: "gitlab", name: "GitLab", icon: Github, connected: false },
    ],
  },
  {
    title: "Communication",
    items: [
      { id: "slack", name: "Slack", icon: MessageSquare, connected: false },
      { id: "discord", name: "Discord", icon: MessageSquare, connected: false },
    ],
  },
  {
    title: "Project Management",
    items: [
      { id: "jira", name: "Jira", icon: Ticket, connected: false },
      { id: "linear", name: "Linear", icon: Ticket, connected: false },
    ],
  },
]

export function SidebarL2Integrations() {
  return (
    <div className="flex flex-col h-full p-4">
      <div className="space-y-6">
        {integrationCategories.map((category) => (
          <div key={category.title}>
            <h3 className="text-sm font-semibold text-slate-400 mb-3">{category.title}</h3>
            <div className="space-y-2">
              {category.items.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    className={cn(
                      "w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left",
                      item.connected
                        ? "border-green-500/30 bg-green-500/5"
                        : "border-dark-border hover:border-slate-600 hover:bg-dark-hover"
                    )}
                  >
                    <Icon className="h-5 w-5 text-slate-400" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-200">{item.name}</p>
                      <p className="text-xs text-slate-500">
                        {item.connected ? "Connected" : "Not connected"}
                      </p>
                    </div>
                    {item.connected && (
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
