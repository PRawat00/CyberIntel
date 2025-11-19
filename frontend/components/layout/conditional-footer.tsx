"use client"

import { usePathname } from "next/navigation"
import { Footer } from "./footer"

/**
 * Conditionally renders the footer based on the current route.
 * Footer is hidden on dashboard pages to maximize workspace.
 */
export function ConditionalFooter() {
  const pathname = usePathname()

  // Hide footer on all dashboard pages
  if (pathname.startsWith("/dashboard")) {
    return null
  }

  return <Footer />
}
