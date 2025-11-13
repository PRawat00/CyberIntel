"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
  Shield,
  Zap,
  BarChart3,
  Lock,
  ArrowRight,
  CheckCircle2,
  MessageSquare,
  Target,
  Play,
  Code2,
  Database,
  Sparkles,
  Check,
  X
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

const features = [
  {
    icon: MessageSquare,
    title: "AI Security Assistant",
    description: "Chat with AI about YOUR specific vulnerabilities. Get remediation guidance tailored to your stack in real-time.",
    badge: "New",
  },
  {
    icon: Shield,
    title: "Smart Dependency Scanning",
    description: "Upload any dependency file. Instantly scan against 200K+ CVEs from the NVD database with intelligent matching.",
    badge: null,
  },
  {
    icon: Target,
    title: "Context-Aware Analysis",
    description: "Select specific packages - AI focuses on what matters to YOU. No generic answers, only actionable insights.",
    badge: "New",
  },
  {
    icon: Lock,
    title: "Privacy-First Architecture",
    description: "Local processing, zero data transmission. Your code stays private and secure. Run air-gapped if needed.",
    badge: null,
  },
]

const stats = [
  { label: "CVEs Searchable", value: "200K+", icon: Database },
  { label: "AI-Powered", value: "RAG", icon: Sparkles },
  { label: "Real-Time", value: "Chat", icon: MessageSquare },
  { label: "Forever", value: "Free", icon: CheckCircle2 },
]

const comparisonFeatures = [
  { name: "Dependency Scanning", snyk: true, chatgpt: false, cyberintel: true },
  { name: "AI Chat Assistant", snyk: false, chatgpt: true, cyberintel: true },
  { name: "Knows YOUR Stack", snyk: false, chatgpt: false, cyberintel: true },
  { name: "Context-Aware", snyk: false, chatgpt: false, cyberintel: true },
  { name: "Free Forever", snyk: false, chatgpt: false, cyberintel: true },
]

const techStack = [
  { name: "Next.js 15", icon: Code2 },
  { name: "FastAPI", icon: Zap },
  { name: "ChromaDB", icon: Database },
  { name: "RAG AI", icon: Sparkles },
  { name: "WebSocket", icon: MessageSquare },
]

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b bg-gradient-to-b from-background to-muted/20 px-6 py-24 sm:py-32 lg:px-8">
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]" />
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border bg-background px-4 py-1.5 text-sm">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="font-medium">AI-Powered Security Co-Pilot</span>
            </div>
            <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-6xl">
              Scan. Chat. Secure.
              <br />
              <span className="text-primary">Your AI Security Co-Pilot</span>
            </h1>
            <p className="mb-10 text-lg leading-8 text-muted-foreground sm:text-xl">
              Upload your dependencies → Get instant vulnerability scan → Chat with AI about YOUR CVEs →
              Get remediation guidance tailored to YOUR stack. All free, all local.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="text-base">
                <Link href="/upload">
                  Start Scanning
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="text-base">
                <Link href="#demo">
                  <Play className="mr-2 h-4 w-4" />
                  Watch Demo
                </Link>
              </Button>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-16 grid grid-cols-2 gap-4 sm:grid-cols-4"
          >
            {stats.map((stat, index) => (
              <div key={index} className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2">
                  <stat.icon className="h-5 w-5 text-primary" />
                  <div className="text-3xl font-bold text-primary">{stat.value}</div>
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Video Demo Section */}
      <section id="demo" className="px-6 py-24 sm:py-32 lg:px-8 bg-muted/30">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border bg-background px-3 py-1 text-xs font-medium">
              <Play className="h-3 w-3 text-primary" />
              Demo
            </div>
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              See CyberIntel in Action
            </h2>
            <p className="mb-10 text-lg text-muted-foreground">
              Watch how AI helps you prioritize and fix vulnerabilities in your dependencies
            </p>

            {/* Video Placeholder */}
            <div className="relative aspect-video w-full overflow-hidden rounded-xl border bg-muted shadow-2xl">
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <Play className="mx-auto mb-4 h-16 w-16 text-primary opacity-50" />
                  <p className="text-muted-foreground">
                    Demo video placeholder
                  </p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Add your demo video URL here
                  </p>
                </div>
              </div>
              {/* When you have a video, replace above with:
              <iframe
                src="YOUR_VIDEO_URL"
                className="h-full w-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
              */}
            </div>

            <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Upload → Scan</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Select Packages</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Chat with AI</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Get Remediation</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              The First Free AI Security Co-Pilot
            </h2>
            <p className="text-lg text-muted-foreground">
              Combines dependency scanning with ChatGPT-like AI that actually knows YOUR stack
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-2">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="relative h-full p-6 transition-all hover:shadow-lg">
                  {feature.badge && (
                    <div className="absolute right-4 top-4 rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">
                      {feature.badge}
                    </div>
                  )}
                  <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table Section */}
      <section className="border-y bg-muted/30 px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Why CyberIntel?
            </h2>
            <p className="text-lg text-muted-foreground">
              The only tool that combines scanning with AI that knows YOUR vulnerabilities
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="p-4 text-left font-semibold">Feature</th>
                      <th className="p-4 text-center font-semibold">Snyk/Dependabot</th>
                      <th className="p-4 text-center font-semibold">ChatGPT</th>
                      <th className="p-4 text-center font-semibold text-primary">CyberIntel</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonFeatures.map((feature, index) => (
                      <tr key={index} className="border-b last:border-b-0">
                        <td className="p-4 font-medium">{feature.name}</td>
                        <td className="p-4 text-center">
                          {feature.snyk ? (
                            <Check className="mx-auto h-5 w-5 text-green-600" />
                          ) : (
                            <X className="mx-auto h-5 w-5 text-muted-foreground/30" />
                          )}
                        </td>
                        <td className="p-4 text-center">
                          {feature.chatgpt ? (
                            <Check className="mx-auto h-5 w-5 text-green-600" />
                          ) : (
                            <X className="mx-auto h-5 w-5 text-muted-foreground/30" />
                          )}
                        </td>
                        <td className="p-4 text-center bg-primary/5">
                          {feature.cyberintel ? (
                            <Check className="mx-auto h-5 w-5 text-primary" />
                          ) : (
                            <X className="mx-auto h-5 w-5 text-muted-foreground/30" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              How it works
            </h2>
            <p className="text-lg text-muted-foreground">
              Five simple steps to scan, analyze, and secure your dependencies
            </p>
          </motion.div>

          <div className="space-y-8">
            {[
              {
                step: "01",
                title: "Upload Your Dependency File",
                description:
                  "Drag and drop any package file - package.json, requirements.txt, Pipfile, or use our sample files.",
              },
              {
                step: "02",
                title: "Automatic Vulnerability Scan",
                description:
                  "AI-powered scanner matches dependencies against 200K+ CVEs from the NVD database with intelligent CPE matching.",
              },
              {
                step: "03",
                title: "Select Packages to Analyze",
                description:
                  "Choose specific vulnerable packages from the results table. AI will focus on your selection for context-aware answers.",
              },
              {
                step: "04",
                title: "Chat with AI About YOUR CVEs",
                description:
                  "Ask questions like 'Which CVE should I fix first?' or 'Explain this vulnerability in plain English.' Get real-time streaming responses.",
              },
              {
                step: "05",
                title: "Export & Fix Vulnerabilities",
                description:
                  "Download reports in JSON, CSV, or HTML format. Follow AI-recommended remediation steps tailored to your stack.",
              },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex gap-6"
              >
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
                  {item.step}
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-xl font-semibold">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="border-t bg-muted/30 px-6 py-16 sm:py-20 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <h3 className="mb-2 text-sm font-medium text-muted-foreground">
              Built with Modern Tech
            </h3>
            <div className="mt-6 flex flex-wrap justify-center gap-4">
              {techStack.map((tech, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 rounded-full border bg-background px-4 py-2 text-sm font-medium"
                >
                  <tech.icon className="h-4 w-4 text-primary" />
                  <span>{tech.name}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Ready to try your AI Security Co-Pilot?
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">
            Start scanning and chatting with AI about your vulnerabilities in seconds.
          </p>
          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button asChild size="lg" className="text-base">
              <Link href="/upload">
                Start Free Scan
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="text-base">
              <Link href="/dashboard">Explore Dashboard</Link>
            </Button>
          </div>

          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>Local processing</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>Open source</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span>AI-powered</span>
            </div>
          </div>
        </motion.div>
      </section>
    </div>
  )
}
