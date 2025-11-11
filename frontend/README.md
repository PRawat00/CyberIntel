# SecureChat Frontend

Modern Next.js 15 web interface for the SecureChat dependency vulnerability scanner.

## Tech Stack

- **Framework**: Next.js 15 (App Router) + TypeScript
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Data Fetching**: React Query
- **Charts**: Recharts
- **Animations**: Framer Motion

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000
```

**Prerequisites**: Backend API running at http://localhost:8000

## Environment Setup

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Status

✅ **Foundation Complete**:
- Next.js 15 with App Router
- shadcn/ui components (14 installed)
- React Query setup
- API client with full type safety
- Custom hooks for scans
- Dark mode support
- Severity color system

🚧 **In Progress**:
- Upload component
- Dashboard pages
- Scan results view
- CVE details modal

## Available Components

### shadcn/ui (14 components):
- button, card, table, badge, progress
- dialog, dropdown-menu, form, input
- select, tabs, alert, skeleton, label

### API Hooks:
```tsx
import { useScans, useScan, useUploadScan } from '@/hooks/use-scans'

// List scans
const { data } = useScans({ page: 1 })

// Upload file
const uploadMutation = useUploadScan()
await uploadMutation.mutateAsync(file)
```

## Severity Colors

```tsx
<Badge className="bg-[hsl(var(--severity-critical))]">Critical</Badge>
<Badge className="bg-[hsl(var(--severity-high))]">High</Badge>
<Badge className="bg-[hsl(var(--severity-medium))]">Medium</Badge>
<Badge className="bg-[hsl(var(--severity-low))]">Low</Badge>
<Badge className="bg-[hsl(var(--severity-safe))]">Safe</Badge>
```

## Next Steps

1. Build upload component (`components/scan/upload-zone.tsx`)
2. Create dashboard page (`app/dashboard/page.tsx`)
3. Build scan results page (`app/dashboard/scans/[id]/page.tsx`)
4. Add CVE details dialog

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [React Query](https://tanstack.com/query/latest)

## Learn More

See `/PHASE3_PROGRESS.md` in project root for detailed progress and architecture.
