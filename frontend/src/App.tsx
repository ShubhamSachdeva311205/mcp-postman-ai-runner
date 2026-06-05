import { useEffect, useState } from "react"
import { AlertCircle, Github, Network, Workflow } from "lucide-react"
import { CollectionInput } from "./components/CollectionInput"
import { RunnerControls, type RunState } from "./components/RunnerControls"
import { ResultsView } from "./components/ResultsView"
import { type Info, type RunReport, getInfo, runCollection } from "./api/client"
import axios from "axios"

type Status = "connecting" | "online" | "offline"
interface Parsed { collection: Record<string, unknown>; name: string; count: number }

function StatusBadge({ status, version }: { status: Status; version?: string }) {
  const dot = status === "online" ? "bg-primary" : status === "offline" ? "bg-destructive" : "bg-ink-faint"
  const label = status === "online" ? `backend ${version ?? ""}`.trim() : status === "offline" ? "backend offline" : "connecting…"
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 font-mono text-[11px] text-ink-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${dot} ${status === "connecting" ? "animate-pulse-soft" : ""}`} />
      {label}
    </span>
  )
}

export default function App() {
  const [info, setInfo] = useState<Info | null>(null)
  const [status, setStatus] = useState<Status>("connecting")
  const [parsed, setParsed] = useState<Parsed | null>(null)
  const [run, setRun] = useState<RunState>({ provider: "ollama", model: "", useLlm: true })
  const [report, setReport] = useState<RunReport | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getInfo()
      .then((i) => {
        setInfo(i)
        setStatus("online")
        setRun((r) => ({
          ...r,
          provider: i.default_provider,
          model: i.providers[i.default_provider]?.models[0] ?? i.default_model ?? "",
        }))
      })
      .catch(() => setStatus("offline"))
  }, [])

  const onRun = async () => {
    if (!parsed) return
    setBusy(true)
    setError(null)
    try {
      setReport(await runCollection(parsed.collection, {
        provider: run.provider,
        model: run.model || undefined,
        use_llm: run.useLlm,
      }))
    } catch (e) {
      const detail = axios.isAxiosError(e) ? e.response?.data?.detail : null
      setError(detail || (status === "offline" ? "Backend offline. Start the API on :8000." : "Run failed. Check the API logs."))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen overflow-x-hidden">
      <header className="sticky top-0 z-20 border-b border-border bg-bg/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
          <div className="flex items-center gap-2.5">
            <div className="grid h-8 w-8 place-items-center rounded-md border border-primary/30 bg-primary/10 text-primary">
              <Workflow className="h-4 w-4" strokeWidth={1.75} />
            </div>
            <div className="leading-tight">
              <h1 className="text-sm font-semibold tracking-tight text-ink">Postman AI Runner</h1>
              <p className="font-mono text-[11px] text-ink-faint">LLM-analyzed API tests · MCP</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={status} version={info?.version} />
            <a
              href="https://github.com/ShubhamSachdeva311205/mcp-postman-ai-runner"
              target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface hover:text-ink"
            >
              <Github className="h-3.5 w-3.5" /> Source
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-5 py-7 lg:grid-cols-[340px_1fr]">
        <aside className="flex min-w-0 flex-col gap-5 lg:sticky lg:top-[68px] lg:h-fit">
          <CollectionInput parsed={parsed} onParsed={(p) => { setParsed(p); setReport(null); setError(null) }} />
          <RunnerControls
            info={info}
            state={run}
            onChange={(patch) => setRun((r) => ({ ...r, ...patch }))}
            onRun={onRun}
            busy={busy}
            ready={!!parsed}
          />
        </aside>

        <section className="min-w-0 space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-ink">
              <AlertCircle className="h-4 w-4 text-destructive" /> {error}
            </div>
          )}

          {report ? (
            <ResultsView report={report} />
          ) : (
            <div className="flex min-h-[420px] flex-col items-center justify-center rounded-md border border-dashed border-border bg-surface/40 p-10 text-center">
              <Network className="h-9 w-9 text-ink-faint" strokeWidth={1.25} />
              <h2 className="mt-4 text-base font-medium text-ink">No run yet</h2>
              <p className="mt-1 max-w-sm text-sm text-ink-faint">
                Load a Postman collection, pick an LLM analyst, and run it. Each request is executed and
                its response judged PASS / WARN / FAIL with anomalies and a one-line summary.
              </p>
              <p className="mt-4 font-mono text-[11px] text-ink-faint">
                default analyst: {info ? `${info.default_provider}${info.default_model ? " · " + info.default_model : ""}` : "…"}
              </p>
            </div>
          )}
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-10 pt-2">
        <p className="border-t border-border pt-4 text-xs text-ink-faint">
          Runs Postman collections natively (no Newman) and analyzes responses with a configurable LLM
          (Ollama / Gemini / Claude). Also usable as an MCP server. Nothing is stored.
        </p>
      </footer>
    </div>
  )
}
