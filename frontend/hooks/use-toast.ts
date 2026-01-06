import { toast as sonnerToast } from "sonner"

export function useToast() {
  return {
    toast: ({
      title,
      description,
      variant = "default",
    }: {
      title?: string
      description?: string
      variant?: "default" | "destructive" | "success"
    }) => {
      if (variant === "destructive") {
        sonnerToast.error(title || "Error", {
          description,
        })
      } else if (variant === "success") {
        sonnerToast.success(title || "Success", {
          description,
        })
      } else {
        sonnerToast(title || "Notification", {
          description,
        })
      }
    },
  }
}
