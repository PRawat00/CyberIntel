/**
 * Individual chat message component with markdown rendering and syntax highlighting.
 */

import { Bot, User, Copy, Check, RotateCw } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { ChatMessage as ChatMessageType } from "@/lib/types"
import type { ExtraProps } from "react-markdown"

type CodeProps = React.HTMLAttributes<HTMLElement> &
  ExtraProps & {
    children?: React.ReactNode
  }

interface ChatMessageProps {
  message: ChatMessageType | { role: "user" | "assistant"; content: string }
  isStreaming?: boolean
  onRegenerate?: () => void
  canRegenerate?: boolean
}

// Code block component with copy button
function CodeBlock({ language, children }: { language?: string; children: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative group">
      <Button
        variant="ghost"
        size="sm"
        className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleCopy}
      >
        {copied ? (
          <Check className="h-3 w-3" />
        ) : (
          <Copy className="h-3 w-3" />
        )}
      </Button>
      <SyntaxHighlighter
        language={language || "text"}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: "0.375rem",
          fontSize: "0.875rem",
          maxWidth: "100%",
          overflowX: "auto",
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  )
}

export function ChatMessage({ message, isStreaming = false, onRegenerate, canRegenerate = true }: ChatMessageProps) {
  const isUser = message.role === "user"
  const [copied, setCopied] = useState(false)

  const handleCopyMessage = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRegenerate = () => {
    if (onRegenerate && canRegenerate) {
      onRegenerate()
    }
  }

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "flex-1 w-full rounded-lg px-4 py-3 overflow-hidden break-words relative",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {isUser ? (
            // User messages: plain text
            <p className="m-0">{message.content}</p>
          ) : (
            // Assistant messages: markdown rendering with syntax highlighting
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code(props: CodeProps) {
                  const { className, children, ...rest } = props
                  const match = /language-(\w+)/.exec(className || "")
                  const codeString = String(children).replace(/\n$/, "")

                  return match ? (
                    <CodeBlock language={match[1]}>
                      {codeString}
                    </CodeBlock>
                  ) : (
                    <code className={className} {...rest}>
                      {children}
                    </code>
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
          {isStreaming && (
            <span className="inline-block ml-1 w-2 h-4 bg-current animate-pulse" />
          )}
        </div>

        {/* Metadata (only for saved messages) */}
        {"created_at" in message && (
          <div className="mt-2 text-xs opacity-70">
            {new Date(message.created_at).toLocaleString([], {
              hour: "2-digit",
              minute: "2-digit",
              hour12: true,
            })}
          </div>
        )}

        {/* Message Actions - Always bottom-right for all messages */}
        {!isStreaming && (
          <div
            className={cn(
              "absolute bottom-2 right-2 flex gap-1",
              "opacity-0 group-hover:opacity-100 sm:opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity"
            )}
          >
            {/* Copy Message Button */}
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-6 w-6 p-0",
                isUser ? "hover:bg-primary-foreground/20" : "hover:bg-muted-foreground/20"
              )}
              onClick={handleCopyMessage}
              title="Copy message"
            >
              {copied ? (
                <Check className="h-3 w-3" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>

            {/* Regenerate Response Button - Only for assistant messages */}
            {!isUser && onRegenerate && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-muted-foreground/20"
                onClick={handleRegenerate}
                disabled={!canRegenerate}
                title="Regenerate response"
              >
                <RotateCw className="h-3 w-3" />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
