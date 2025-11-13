"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
  Shield,
  Zap,
  ArrowRight,
  CheckCircle2,
  MessageSquare,
  Target,
  Play,
  Code2,
  Database,
  Sparkles,
  Check,
  X,
  GitBranch,
  EyeOff,
  AlertTriangle,
  Users,
  TrendingUp,
  Network,
  Brain,
  ListOrdered,
  AlertCircle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import AnimatedTextCycle from "@/components/ui/animated-text-cycle"

const animatedWords = [
  "TEAM",
  "WORKFLOW",
  "PRODUCTIVITY",
  "PROJECTS",
  "ANALYTICS",
  "DASHBOARD",
  "PLATFORM",
  "BUSINESS"
]

const features = [
  {
    icon: GitBranch,
    title: "Supply Chain Visibility",
    description: "See the full dependency tree and where vulnerabilities hide. Instantly know if debug or chalk compromised versions are lurking in YOUR stack.",
    badge: "New",
  },
  {
    icon: Brain,
    title: "AI Impact Analysis",
    description: "AI explains if a CVE actually affects YOUR code paths. Ask: 'Does this chalk exploit affect my CLI tool or just my tests?'",
    badge: "New",
  },
  {
    icon: ListOrdered,
    title: "Smart Prioritization",
    description: "Know which CVEs to fix first based on real impact. Stop panic-fixing every CVE. Focus on what matters to YOUR project.",
    badge: null,
  },
  {
    icon: MessageSquare,
    title: "Conversational Intelligence",
    description: "Ask 'Does this affect me?' and get real answers. Chat like it's a security expert sitting next to you.",
    badge: null,
  },
]

const stats = [
  { label: "CVEs Analyzed", value: "200K+", icon: Database },
  { label: "Dependency Tree", value: "Full", icon: GitBranch },
  { label: "AI Analysis", value: "Real-Time", icon: Sparkles },
  { label: "Forever", value: "Free", icon: CheckCircle2 },
]

type ComparisonValue = boolean | "partial" | "auto-pr"

interface ComparisonFeature {
  name: string
  traditional: ComparisonValue
  dependabot: ComparisonValue
  cyberintel: boolean
}

const comparisonFeatures: ComparisonFeature[] = [
  { name: "Detects Direct CVEs", traditional: true, dependabot: true, cyberintel: true },
  { name: "Shows Transitive Dependencies", traditional: false, dependabot: "partial", cyberintel: true },
  { name: "AI Impact Analysis", traditional: false, dependabot: false, cyberintel: true },
  { name: "Explains Supply Chain Risk", traditional: false, dependabot: false, cyberintel: true },
  { name: '"Does this CVE affect ME?"', traditional: false, dependabot: false, cyberintel: true },
  { name: "Prioritization Guidance", traditional: false, dependabot: "auto-pr", cyberintel: true },
  { name: "Free Forever", traditional: false, dependabot: true, cyberintel: true },
]

const techStack = [
  { name: "Next.js 15", icon: Code2 },
  { name: "FastAPI", icon: Zap },
  { name: "ChromaDB", icon: Database },
  { name: "RAG AI", icon: Sparkles },
  { name: "WebSocket", icon: MessageSquare },
]

const exampleQuestions = [
  "Which CVE should I fix first in my React app?",
  "Does this lodash vulnerability affect my API endpoints?",
  "Show me the dependency chain for CVE-2025-1234",
  "Is this debug package a supply chain attack risk?",
  "Did the Shai-Hulud worm affect any of my dependencies?",
  "What's the blast radius of this chalk compromise?",
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
              <span className="font-medium">AI-Powered Supply Chain Security</span>
            </div>
            <h1 className="mb-6 text-3xl font-bold tracking-tight sm:text-5xl">
              Understand the REAL Impact
              <br />
              of Vulnerabilities in YOUR
              <br />
              <span className="text-primary inline-block"><AnimatedTextCycle
                  words={animatedWords}
                  interval={3000}
                  className="text-primary"
                /></span>
            </h1>
            <p className="mb-4 text-lg leading-8 text-muted-foreground sm:text-xl">
              AI-powered supply chain security that explains how CVEs actually affect YOUR dependencies
            </p>
            <div className="mb-10 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
                <div className="text-left text-sm text-muted-foreground">
                  <span className="font-semibold text-foreground">When debug and chalk packages were compromised in Sept 2025</span> (2 billion weekly downloads), could you answer: <span className="font-semibold text-foreground">"Does MY project use these?"</span> in under 5 minutes?
                </div>
              </div>
            </div>
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

      {/* The Hidden Risk Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              The Hidden Risk in Your Dependencies
            </h2>
            <p className="text-lg text-muted-foreground">
              Real supply chain attacks targeting packages you trust
            </p>
          </motion.div>

          {/* Real Attack Callout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mb-12"
          >
            <Card className="border-red-500/20 bg-red-500/5 p-6">
              <div className="flex items-start gap-4">
                <AlertTriangle className="h-6 w-6 shrink-0 text-red-600 dark:text-red-400 mt-1" />
                <div className="flex-1">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-red-600 px-2 py-0.5 text-xs font-medium text-white">
                      Real Attack - September 2025
                    </span>
                    <span className="text-sm font-semibold text-foreground">The Shai-Hulud Worm</span>
                  </div>
                  <p className="mb-3 text-sm text-muted-foreground">
                    The Shai-Hulud worm compromised <span className="font-semibold text-foreground">180+ npm packages</span> including debug, chalk, and CrowdStrike libraries. The self-replicating malware stole npm tokens and automatically infected MORE packages.
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    Could you answer: "Does MY project use these?" in under 5 minutes?
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* 3 Pain Points */}
          <div className="grid gap-6 md:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Network className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">Transitive Dependency Risk</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Package X uses Y, which has CVE-2024-1234. Is that critical?
                </p>
                <div className="rounded-md border border-muted bg-muted/30 p-3 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Example:</span> Your Express app uses a logging library that depends on debug@4.3.6 (compromised version)
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <EyeOff className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">Hidden Vulnerable Dependencies</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Your old library has 5 vulnerable dependencies you can't see
                </p>
                <div className="rounded-md border border-muted bg-muted/30 p-3 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Example:</span> That 2-year-old utility package still pulls in chalk@4.0.0 with the malicious post-install script
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <AlertTriangle className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">Supply Chain Worm Attacks</h3>
                <p className="mb-4 text-sm text-muted-foreground">
                  Self-replicating attacks spread through packages you trust
                </p>
                <div className="rounded-md border border-muted bg-muted/30 p-3 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Example:</span> Shai-Hulud used stolen npm tokens to automatically infect MORE packages - spreading like wildfire
                </div>
              </Card>
            </motion.div>
          </div>
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
              Watch how AI helps you understand and prioritize vulnerabilities in your supply chain
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
                <span>See Full Tree</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Select CVEs</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Chat with AI</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                <span>Get Action Plan</span>
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
              Stop Guessing. Start Understanding.
            </h2>
            <p className="text-lg text-muted-foreground">
              The only tool that explains if CVEs actually affect YOUR code
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
              When Shai-Hulud hit, could your current tools answer these questions?
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
                      <th className="p-4 text-center font-semibold">Traditional Scanners</th>
                      <th className="p-4 text-center font-semibold">GitHub Dependabot</th>
                      <th className="p-4 text-center font-semibold text-primary">CyberIntel</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonFeatures.map((feature, index) => (
                      <tr key={index} className="border-b last:border-b-0">
                        <td className="p-4 font-medium">{feature.name}</td>
                        <td className="p-4 text-center">
                          {feature.traditional === true ? (
                            <Check className="mx-auto h-5 w-5 text-green-600" />
                          ) : feature.traditional === "partial" ? (
                            <span className="text-xs text-muted-foreground">Partial</span>
                          ) : feature.traditional === "auto-pr" ? (
                            <span className="text-xs text-muted-foreground">Auto-PR</span>
                          ) : (
                            <X className="mx-auto h-5 w-5 text-muted-foreground/30" />
                          )}
                        </td>
                        <td className="p-4 text-center">
                          {feature.dependabot === true ? (
                            <Check className="mx-auto h-5 w-5 text-green-600" />
                          ) : feature.dependabot === "partial" ? (
                            <span className="text-xs text-muted-foreground">Partial</span>
                          ) : feature.dependabot === "auto-pr" ? (
                            <span className="text-xs text-muted-foreground">Auto-PR</span>
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

      {/* Multi-Persona Section */}
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
              Built for Everyone Who Ships Code
            </h2>
            <p className="text-lg text-muted-foreground">
              From individual developers to engineering leaders
            </p>
          </motion.div>

          <div className="grid gap-8 md:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Code2 className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">For Developers</h3>
                <p className="mb-4 text-muted-foreground">
                  Stop wasting hours researching CVEs
                </p>
                <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
                  <p className="italic">"Should I worry about this debug vulnerability?"</p>
                </div>
                <p className="mt-4 text-xs text-muted-foreground">
                  Instead of Googling for 2 hours, just ask CyberIntel
                </p>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">For Teams</h3>
                <p className="mb-4 text-muted-foreground">
                  Understand your supply chain risk across all projects
                </p>
                <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
                  <p className="italic">"Which team projects were hit by Shai-Hulud?"</p>
                </div>
                <p className="mt-4 text-xs text-muted-foreground">
                  Scanned 50 repos and found 12 affected packages in 5 minutes
                </p>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <Card className="h-full p-6">
                <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">For Engineering Leaders</h3>
                <p className="mb-4 text-muted-foreground">
                  Prevent supply chain attacks before they become breaches
                </p>
                <div className="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
                  <p className="italic">"What's our overall security posture?"</p>
                </div>
                <p className="mt-4 text-xs text-muted-foreground">
                  Security insights you can actually understand and act on
                </p>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="border-y bg-muted/30 px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              From Scan to Action in Minutes
            </h2>
            <p className="text-lg text-muted-foreground">
              Five simple steps to understand and secure your supply chain
            </p>
          </motion.div>

          <div className="space-y-8">
            {[
              {
                step: "01",
                title: "Upload Your Dependency File",
                description:
                  "package.json, requirements.txt, Pipfile - we support them all. Or use our sample files to try it out.",
              },
              {
                step: "02",
                title: "Scan Entire Dependency Tree",
                description:
                  "We check direct AND transitive dependencies (the ones you can't see). Find that vulnerable chalk 5 levels deep in your dependency tree.",
              },
              {
                step: "03",
                title: "Select Concerning CVEs",
                description:
                  "See severity, CVSS scores, and which packages are affected. Use checkbox selection for focused AI analysis of specific vulnerabilities.",
              },
              {
                step: "04",
                title: "Chat with AI About Impact",
                description:
                  'Ask: "Does this debug exploit affect my API server or just dev tools?" Get real-time streaming responses that explain the blast radius.',
              },
              {
                step: "05",
                title: "Get Prioritized Action Plan",
                description:
                  "AI tells you: Fix THIS now, THIS can wait, THIS doesn't affect you. Export reports in JSON, CSV, or HTML for your records.",
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

      {/* Real Questions Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Ask Questions That Actually Matter
            </h2>
            <p className="text-lg text-muted-foreground">
              Stop Googling CVEs. Start having conversations.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="flex flex-wrap justify-center gap-3"
          >
            {exampleQuestions.map((question, index) => (
              <div
                key={index}
                className="rounded-full border bg-background px-4 py-2 text-sm text-muted-foreground transition-all hover:border-primary hover:text-foreground"
              >
                {question}
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Animated CTA Section */}
      <section className="border-y bg-gradient-to-b from-background to-muted/20 px-6 py-24 sm:py-32 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-4xl text-center"
        >
          <h2 className="mb-6 text-3xl font-bold tracking-tight sm:text-5xl">
            Your{" "}
            <span className="text-primary inline-block">
              <AnimatedTextCycle
                words={animatedWords}
                interval={3000}
                className="text-primary"
              />
            </span>{" "}
            Deserves Better Security
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">
            Don't let hidden vulnerabilities in your supply chain become tomorrow's security incident.
            <br />
            When the next Shai-Hulud hits, will you know if you're affected?
          </p>

          {/* Stats Row */}
          <div className="mb-10 flex flex-wrap justify-center gap-8 text-sm">
            <div className="flex flex-col items-center">
              <div className="text-3xl font-bold text-primary">180+</div>
              <div className="text-muted-foreground">Packages in Shai-Hulud</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="text-3xl font-bold text-primary">2B</div>
              <div className="text-muted-foreground">Weekly downloads affected</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="text-3xl font-bold text-primary">Minutes</div>
              <div className="text-muted-foreground">To detect with CyberIntel</div>
            </div>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button asChild size="lg" className="text-base">
              <Link href="/upload">
                Scan Your First Project
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="text-base">
              <Link href="#demo">See Live Demo</Link>
            </Button>
          </div>
        </motion.div>
      </section>

      {/* Tech Stack Section */}
      <section className="px-6 py-16 sm:py-20 lg:px-8">
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

      {/* Final CTA Section */}
      <section className="px-6 py-24 sm:py-32 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Ready to Understand Your Risk?
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
