import { useState } from "react"
import { AlertTriangle, CheckCircle2, ChevronRight, XCircle } from "lucide-react"
import type { ResultRow, RunReport, Verdict } from "../api/client"
import { cn } from "../lib/utils"

const VERDICT = {
  PASS: { cls: "text-pass bg-pass/12 border-pass/30", Icon: CheckCircle2 },
  WARN: { cls: "text-warn bg-warn/12 border-warn/30", Icon: AlertTriangle },
  FAIL: { cls: "text-fail bg-fail/12 border-fail/30", Icon: XCircle },
} as const

function VerdictBadge({ v }: { v: Verdict }) {
  const { cls, Icon } = VERDICT[v]
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 font-mono text-[11px]", cls)}>
      <Icon className="h-3 w-3" /> {v}
    </span>
  )
}

function methodColor(m: string) {
  return {
    GET: "text-primary", POST: "text-pass", PUT: "text-warn",
    PATCH: "text-warn", DELETE: "text-fail",
  }[m.toUpperCase()] ?? "text-ink-muted"
}

function Stat({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="flex flex-col gap-0.5 px-3 py-2">
      <span className="text-[10px] uppercase tracking-wide text-ink-faint">{label}</span>
      <span className={cn("font-mono text-base", tone ?? "text-ink")}>{value}</span>
    </div>
  )
}

function Row({ r }: { r: ResultRow }) {
  const [open, setOpen] = useState(false)
  const hasDetail = r.summary || r.anomalies.length > 0
  return (
    <>
      <tr
        onClick={() => hasDetail && setOpen((o) => !o)}
        className={cn("border-t border-border", hasDetail && "cursor-pointer hover:bg-surface-2/50")}
      >
        <td className="py-2 pl-3 pr-2">
          <ChevronRight className={cn("h-3.5 w-3.5 text-ink-faint transition-transform", open && "rotate-90", !hasDetail && "opacity-0")} />
        </td>
        <td className="py-2 pr-2 font-mono text-xs"><span className={methodColor(r.method)}>{r.method}</span></td>
        <td className="py-2 pr-2">
          <div className="text-sm text-ink">{r.name}</div>
          <div className="truncate font-mono text-[11px] text-ink-faint" style={{ maxWidth: "32ch" }}>{r.url}</div>
        </td>
        <td className="py-2 pr-2 text-right font-mono text-xs text-ink-muted">{r.status_code ?? "—"}</td>
        <td className="hidden py-2 pr-2 text-right font-mono text-xs text-ink-faint sm:table-cell">{r.latency_ms.toFixed(0)}ms</td>
        <td className="py-2 pr-3 text-right"><VerdictBadge v={r.verdict} /></td>
      </tr>
      {open && hasDetail && (
        <tr className="border-t border-border/60 bg-bg/40">
          <td />
          <td colSpan={5} className="py-2 pr-3">
            {r.summary && <p className="mb-1 text-xs text-ink-muted">{r.summary}</p>}
            {r.anomalies.length > 0 && (
              <ul className="list-inside list-disc space-y-0.5">
                {r.anomalies.map((a, i) => <li key={i} className="font-mono text-[11px] text-warn">{a}</li>)}
              </ul>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export function ResultsView({ report }: { report: RunReport }) {
  const s = report.summary
  return (
    <div className="animate-fade-up space-y-4">
      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <div className="grid grid-cols-3 divide-x divide-border border-b border-border sm:grid-cols-6">
          <Stat label="Total" value={s.total} />
          <Stat label="Passed" value={s.passed} tone="text-pass" />
          <Stat label="Warnings" value={s.warnings} tone="text-warn" />
          <Stat label="Failed" value={s.failed} tone="text-fail" />
          <Stat label="Avg latency" value={`${s.avg_latency_ms}ms`} />
          <Stat label="Analyst" value={s.provider === "none" ? "rules" : s.provider} />
        </div>
        <div className="px-3 py-2 font-mono text-[11px] text-ink-faint">
          {s.collection}{s.model ? ` · ${s.model}` : ""}
        </div>
      </div>

      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-ink-faint">
              <th className="w-6" />
              <th className="py-2 pr-2 font-medium">Method</th>
              <th className="py-2 pr-2 font-medium">Request</th>
              <th className="py-2 pr-2 text-right font-medium">Code</th>
              <th className="hidden py-2 pr-2 text-right font-medium sm:table-cell">Latency</th>
              <th className="py-2 pr-3 text-right font-medium">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {report.results.map((r, i) => <Row key={i} r={r} />)}
          </tbody>
        </table>
      </div>
    </div>
  )
}
