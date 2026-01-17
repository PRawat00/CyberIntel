import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Generates a properly formatted NVD URL for a given CVE ID
 * Handles sanitization to ensure valid URLs
 * @param cveId - The CVE identifier (e.g., "CVE-2021-23337")
 * @returns The full NVD URL for the CVE
 */
export function getNvdUrl(cveId: string): string {
  // Trim whitespace and convert to uppercase
  // NVD expects format: CVE-YYYY-NNNNN (all uppercase)
  const sanitizedId = cveId.trim().toUpperCase()

  // No encoding needed - CVE IDs only contain alphanumeric chars and hyphens
  // which are all safe for URLs. Encoding would break the NVD validation.
  return `https://nvd.nist.gov/vuln/detail/${sanitizedId}`
}
