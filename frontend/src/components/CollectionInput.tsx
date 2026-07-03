import { useRef, useState } from "react"
import { FileJson, FlaskConical, Upload, X } from "lucide-react"
import { cn } from "../lib/utils"

const SAMPLE = {
  info: { name: "Sample API Tests", schema: "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  variable: [{ key: "base", value: "https://jsonplaceholder.typicode.com" }],
  item: [
    { name: "Get a todo", request: { method: "GET", header: [], url: { raw: "{{base}}/todos/1" } } },
    { name: "Missing resource", request: { method: "GET", header: [], url: { raw: "{{base}}/nope/404" } } },
    {
      name: "Create a post",
      request: {
        method: "POST",
        header: [{ key: "Content-Type", value: "application/json" }],
        body: { mode: "raw", raw: '{"title":"hello","body":"world","userId":1}' },
        url: { raw: "{{base}}/posts" },
      },
    },
  ],
}

interface Parsed {
  collection: Record<string, unknown>
  name: string
  count: number
}

function countRequests(node: any): number {
  if (!node?.item) return node?.request ? 1 : 0
  return node.item.reduce((n: number, c: any) => n + countRequests(c), 0)
}

interface Props {
  parsed: Parsed | null
  onParsed: (p: Parsed | null) => void
}

export function CollectionInput({ parsed, onParsed }: Props) {
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const accept = (text: string) => {
    setError(null)
    try {
      const obj = JSON.parse(text)
      if (!obj.item || !Array.isArray(obj.item)) throw new Error("no 'item' array — not a Postman v2.1 collection")
      onParsed({ collection: obj, name: obj.info?.name ?? "Untitled collection", count: countRequests(obj) })
    } catch (e) {
      onParsed(null)
      setError(e instanceof Error ? e.message : "Invalid JSON")
    }
  }

  if (parsed) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface px-3 py-2.5">
        <div className="flex min-w-0 items-center gap-2.5">
          <FileJson className="h-5 w-5 shrink-0 text-primary" strokeWidth={1.75} />
          <div className="min-w-0">
            <p className="truncate text-sm text-ink">{parsed.name}</p>
            <p className="font-mono text-xs text-ink-faint">{parsed.count} request{parsed.count === 1 ? "" : "s"}</p>
          </div>
        </div>
        <button
          onClick={() => onParsed(null)}
          className="inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-xs text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
        >
          <X className="h-3.5 w-3.5" /> Clear
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault(); setDragging(false)
          e.dataTransfer.files?.[0]?.text().then(accept)
        }}
        className={cn(
          "flex w-full flex-col items-center justify-center gap-2 rounded-md border border-dashed px-6 py-7 text-center transition-colors",
          dragging ? "border-primary bg-primary/5" : "border-border-strong/60 hover:border-primary/60 hover:bg-surface/60",
        )}
      >
        <input ref={inputRef} type="file" accept=".json,application/json" className="sr-only"
          onChange={(e) => e.target.files?.[0]?.text().then(accept)} />
        <Upload className="h-6 w-6 text-primary" strokeWidth={1.5} />
        <span className="text-sm font-medium text-ink">Drop a Postman collection</span>
        <span className="text-xs text-ink-faint">v2.1 JSON · or paste below</span>
      </button>

      <button
        type="button"
        onClick={() => accept(JSON.stringify(SAMPLE))}
        className="flex w-full items-center justify-center gap-2 rounded-md border border-primary/40 bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
      >
        <FlaskConical className="h-4 w-4" strokeWidth={1.75} /> Use sample test collection
      </button>
      <p className="text-center text-[11px] text-ink-faint">one click — no file needed</p>

      <textarea
        onChange={(e) => e.target.value.trim() && accept(e.target.value)}
        placeholder="…or paste collection JSON here"
        spellCheck={false}
        className="h-20 w-full resize-y rounded-md border border-input bg-bg px-3 py-2 font-mono text-xs text-ink placeholder:text-ink-faint/60 focus-visible:border-primary/60 focus-visible:outline-none"
      />

      {error && <span className="block truncate text-xs text-fail">{error}</span>}
    </div>
  )
}
