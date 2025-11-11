"use client"

import { useState } from "react"
import { FileCode, FileJson, Package } from "lucide-react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fadeIn, smooth } from "@/lib/animations"

interface SampleFile {
  name: string
  icon: React.ReactNode
  type: "python" | "npm"
}

const SAMPLE_FILES: SampleFile[] = [
  {
    name: "vulnerable-requirements.txt",
    icon: <FileCode className="w-6 h-6" />,
    type: "python",
  },
  {
    name: "package-lock.json",
    icon: <FileJson className="w-6 h-6" />,
    type: "npm",
  },
  {
    name: "Pipfile",
    icon: <Package className="w-6 h-6" />,
    type: "python",
  },
]

interface SampleFilesProps {
  onFileSelect?: (file: File) => void
}

export function SampleFiles({ onFileSelect }: SampleFilesProps) {
  const [draggingFile, setDraggingFile] = useState<string | null>(null)

  const handleDragStart = (e: React.DragEvent, fileName: string) => {
    setDraggingFile(fileName)
    e.dataTransfer.effectAllowed = "copy"
    e.dataTransfer.setData("application/x-sample-file", fileName)
  }

  const handleDragEnd = () => {
    setDraggingFile(null)
  }

  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={fadeIn}
      transition={smooth}
      className="w-full"
    >
      <Card className="border-2">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Sample Files</CardTitle>
          <p className="text-xs text-muted-foreground">
            Drag files to try the scanner
          </p>
        </CardHeader>
        <CardContent className="space-y-2">
          {SAMPLE_FILES.map((file) => (
            <motion.div
              key={file.name}
              draggable
              onDragStart={(e) => handleDragStart(e, file.name)}
              onDragEnd={handleDragEnd}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`
                flex items-center gap-3 p-3 rounded-lg border-2 transition-all
                cursor-grab active:cursor-grabbing
                ${
                  draggingFile === file.name
                    ? "border-primary bg-primary/5 opacity-50"
                    : "border-border hover:border-primary/50 hover:bg-accent/50"
                }
              `}
            >
              <div
                className={`
                  flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center
                  ${file.type === "python" ? "bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400" : "bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400"}
                `}
              >
                {file.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground capitalize">
                  {file.type}
                </p>
              </div>
            </motion.div>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  )
}
