import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Providers } from "./providers"
import { Toaster } from "@/components/ui/sonner"
import { Navbar } from "@/components/layout/navbar"
import { ConditionalFooter } from "@/components/layout/conditional-footer"
import { DemoModeBadge } from "@/components/ui/demo-mode-badge"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "CyberIntel - AI-Powered Dependency Security Scanner",
  description: "Scan your dependencies for vulnerabilities with AI-powered insights. Find CVEs in npm and pip packages instantly.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <ConditionalFooter />
          </div>
          <DemoModeBadge />
        </Providers>
        <Toaster />
      </body>
    </html>
  )
}
