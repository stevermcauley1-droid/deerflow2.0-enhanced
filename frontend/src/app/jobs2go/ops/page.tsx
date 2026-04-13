"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type ModuleHealth = {
  name: string;
  status: string;
  note: string;
};

type KpiSnapshot = {
  jobs_created: number;
  offers_sent: number;
  offers_accepted: number;
  bookings_completed: number;
  fill_rate_15_min_pct: number;
  completion_rate_pct: number;
  escrow_authorized_count: number;
  escrow_released_count: number;
  escrow_release_rate_pct: number;
  reviews_count: number;
  trust_reports_count: number;
  trust_priority_reports_count: number;
};

async function fetchJson<T>(apiBase: string, path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Fall back to status text.
    }
    throw new Error(`${response.status}: ${detail}`);
  }
  return (await response.json()) as T;
}

const tileClass =
  "rounded-2xl border border-zinc-200/70 bg-white/80 p-4 shadow-[0_10px_30px_-18px_rgba(0,0,0,0.35)] backdrop-blur dark:border-zinc-700/60 dark:bg-zinc-900/70";

export default function Jobs2GoOpsPage() {
  const [apiBase, setApiBase] = useState("http://localhost:8001");
  const [modules, setModules] = useState<ModuleHealth[]>([]);
  const [kpi, setKpi] = useState<KpiSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [modulePayload, kpiPayload] = await Promise.all([
        fetchJson<{ modules: ModuleHealth[] }>(apiBase, "/v1/ops/modules"),
        fetchJson<KpiSnapshot>(apiBase, "/v1/ops/kpi"),
      ]);
      setModules(modulePayload.modules);
      setKpi(kpiPayload);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_20%_20%,#d3ffe3,transparent_30%),radial-gradient(circle_at_88%_10%,#d8ecff,transparent_25%),linear-gradient(165deg,#f8fff8,#eff7ff_50%,#f6f4ff)] px-4 py-8 text-zinc-900 dark:bg-[radial-gradient(circle_at_20%_20%,#133224,transparent_30%),radial-gradient(circle_at_88%_10%,#172d46,transparent_25%),linear-gradient(165deg,#17211b,#16202d_50%,#1c1a30)] dark:text-zinc-100 sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="rounded-3xl border border-zinc-200/80 bg-white/80 p-6 shadow-xl backdrop-blur dark:border-zinc-700/60 dark:bg-zinc-900/75">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700 dark:text-emerald-300">Pilot Ops Console</p>
          <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">Jobs2Go KPI and Module Health</h1>
          <p className="mt-2 max-w-3xl text-sm text-zinc-700 dark:text-zinc-300">
            Operations view for launch readiness. Monitor conversion, fulfillment, escrow settlement, and trust escalation from one page.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <input
              className="h-10 w-full max-w-sm rounded-xl border border-zinc-300 bg-white/85 px-3 text-sm outline-none focus:border-emerald-500 dark:border-zinc-600 dark:bg-zinc-800"
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="http://localhost:8001"
            />
            <button
              className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              onClick={() => void loadDashboard()}
              disabled={loading}
            >
              {loading ? "Refreshing..." : "Refresh Snapshot"}
            </button>
            <Link href="/jobs2go" className="rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-100 dark:border-zinc-600 dark:hover:bg-zinc-800">
              Open Pilot Cockpit
            </Link>
          </div>
          {error && <p className="mt-3 text-sm text-rose-600 dark:text-rose-300">Error: {error}</p>}
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className={tileClass}>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Jobs Created</p>
            <p className="mt-2 text-3xl font-semibold">{kpi?.jobs_created ?? 0}</p>
          </div>
          <div className={tileClass}>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Fill Rate (15m)</p>
            <p className="mt-2 text-3xl font-semibold">{kpi ? `${kpi.fill_rate_15_min_pct}%` : "0%"}</p>
          </div>
          <div className={tileClass}>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Completion Rate</p>
            <p className="mt-2 text-3xl font-semibold">{kpi ? `${kpi.completion_rate_pct}%` : "0%"}</p>
          </div>
          <div className={tileClass}>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Escrow Release Rate</p>
            <p className="mt-2 text-3xl font-semibold">{kpi ? `${kpi.escrow_release_rate_pct}%` : "0%"}</p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <article className={tileClass}>
            <h2 className="text-xl font-semibold">Pipeline Counters</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <MetricRow label="Offers Sent" value={kpi?.offers_sent ?? 0} />
              <MetricRow label="Offers Accepted" value={kpi?.offers_accepted ?? 0} />
              <MetricRow label="Bookings Completed" value={kpi?.bookings_completed ?? 0} />
              <MetricRow label="Escrow Authorized" value={kpi?.escrow_authorized_count ?? 0} />
              <MetricRow label="Escrow Released" value={kpi?.escrow_released_count ?? 0} />
              <MetricRow label="Reviews" value={kpi?.reviews_count ?? 0} />
              <MetricRow label="Trust Reports" value={kpi?.trust_reports_count ?? 0} />
              <MetricRow label="Priority Reports" value={kpi?.trust_priority_reports_count ?? 0} />
            </div>
          </article>

          <article className={tileClass}>
            <h2 className="text-xl font-semibold">Module Health</h2>
            <div className="mt-4 space-y-3">
              {modules.map((module) => (
                <div key={module.name} className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/70">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium">{module.name}</p>
                    <span className="rounded-lg bg-emerald-100 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                      {module.status}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-300">{module.note}</p>
                </div>
              ))}
              {modules.length === 0 && !loading && (
                <p className="text-sm text-zinc-500">No module health data loaded yet.</p>
              )}
            </div>
          </article>
        </section>
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-800/70">
      <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
