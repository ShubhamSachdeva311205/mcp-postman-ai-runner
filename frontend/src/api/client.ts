import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"
export const api = axios.create({ baseURL: API_URL })

export type Provider = "ollama" | "gemini" | "claude"
export type Verdict = "PASS" | "WARN" | "FAIL"

export interface ProviderInfo {
  available: boolean
  models: string[]
  needs_key: boolean
}

export interface Info {
  version: string
  providers: Record<Provider, ProviderInfo>
  default_provider: Provider
  default_model: string | null
}

export interface ResultRow {
  name: string
  folder: string
  method: string
  url: string
  status_code: number | null
  latency_ms: number
  verdict: Verdict
  severity: "low" | "medium" | "high"
  anomalies: string[]
  summary: string
}

export interface RunReport {
  summary: {
    total: number
    passed: number
    warnings: number
    failed: number
    avg_latency_ms: number
    provider: string
    model: string | null
    collection: string
  }
  results: ResultRow[]
}

export interface RunOptions {
  provider?: Provider
  model?: string
  variables?: Record<string, string>
  use_llm?: boolean
  max_requests?: number
}

export async function getInfo(): Promise<Info> {
  const { data } = await api.get<Info>("/info")
  return data
}

export async function runCollection(collection: unknown, opts: RunOptions): Promise<RunReport> {
  const { data } = await api.post<RunReport>("/run", {
    collection,
    provider: opts.provider,
    model: opts.model,
    variables: opts.variables,
    use_llm: opts.use_llm ?? true,
    max_requests: opts.max_requests ?? 50,
  })
  return data
}
