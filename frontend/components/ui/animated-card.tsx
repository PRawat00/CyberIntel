"use client"

import { motion } from "framer-motion"
import { Card } from "./card"
import { scaleIn, smooth } from "@/lib/animations"
import type { ComponentProps } from "react"

export function AnimatedCard({ children, ...props }: ComponentProps<typeof Card>) {
  return (
    <motion.div
      variants={scaleIn}
      initial="initial"
      animate="animate"
      transition={smooth}
      whileHover={{ scale: 1.02 }}
      className="h-full"
    >
      <Card {...props}>{children}</Card>
    </motion.div>
  )
}
