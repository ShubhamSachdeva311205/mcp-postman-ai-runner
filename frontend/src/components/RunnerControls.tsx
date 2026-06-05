import { Loader2, Play } from "lucide-react"
import type { Info, Provider } from "../api/client"
import { cn } from "../lib/utils"

export interface RunState {
  provider: Provider
  model: string
  useLlm: boolean
}

interface Props {
  info: Info | null
  state: RunState
  onChange: (patch: Partial<RunState>) => void
  onRun: () => void
  busy: boolean
  ready: boolean
}

const PROVIDERS: Provider[] = ["ollama", "gemini", "claude"]
const LABEL: Record<Provider, string> = { ollama: "Ollama", gemini: "Gemini", claude: "Claude" }

export function RunnerControls({ info, state, onChange, onRun, busy, ready }: Props) {
  const pinfo = info?.providers[state.provider]
  const models = pinfo?.models ?? []

  return (
    <div className="space-y-4">
      <div>
        <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">LLM provider</p>
        <div className="grid grid-cols-3 gap-1 rounded-md border border-border bg-bg p-1">
          {PROVIDERS.map((p) => {
            const avail = info?.providers[p]?.available
            return (
              <button
                key={p}
                type="button"
                aria-pressed={state.provider === p}
                disabled={info ? !avail : false}
                title={avail ? "" : info?.providers[p]?.needs_key ? "Set this provider's API key" : "Is Ollama running?"}
                onClick={() => onChange({ provider: p, model: info?.providers[p]?.models[0] ?? "" })}
                className={cn(
                  "rounded-sm px-2 py-1.5 font-mono text-xs transition-colors disabled:cursor-not-allowed disabled:opacity-35",
                  state.provider === p ? "bg-primary/15 text-primary" : "text-ink-muted hover:bg-surface-2 hover:text-ink",
                )}
              >
                {LABEL[p]}
              </button>
            )
          })}
        </div>
        {info && pinfo && !pinfo.available && (
          <p className="mt-1.5 text-xs text-warn">
            {pinfo.needs_key ? `Set the ${LABEL[state.provider]} API key on the server.` : "Ollama isn't reachable on :11434."}
          </p>
        )}
      </div>

      <div>
        <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">Model</p>
        {state.provider === "ollama" && models.length > 0 ? (
          <select
            value={state.model}
            onChange={(e) => onChange({ model: e.target.value })}
            className="w-full rounded-md border border-input bg-bg px-3 py-2 font-mono text-sm text-ink focus-visible:border-primary/60 focus-visible:outline-none"
          >
            {models.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        ) : (
          <input
            value={state.model}
            onChange={(e) => onChange({ model: e.target.value })}
            placeholder={info?.default_model ?? "model name"}
            className="w-full rounded-md border border-input bg-bg px-3 py-2 font-mono text-sm text-ink placeholder:text-ink-faint/60 focus-visible:border-primary/60 focus-visible:outline-none"
          />
        )}
      </div>

      <label className="flex cursor-pointer items-center justify-between gap-3 rounded-md border border-border bg-bg px-3 py-2.5">
        <span>
          <span className="block text-sm text-ink">AI analysis</span>
          <span className="mt-0.5 block text-xs text-ink-faint">Off = deterministic checks only (status, latency)</span>
        </span>
        <input
          type="checkbox"
          checked={state.useLlm}
          onChange={(e) => onChange({ useLlm: e.target.checked })}
          className="h-4 w-4 accent-[oklch(0.70_0.115_185)]"
        />
      </label>

      <button
        type="button"
        onClick={onRun}
        disabled={!ready || busy}
        className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-primary font-medium text-primary-foreground transition-[filter,opacity] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
        {busy ? "Running collection…" : "Run collection"}
      </button>
      {!ready && <p className="-mt-2 text-center text-xs text-ink-faint">Load a collection to run.</p>}
    </div>
  )
}
