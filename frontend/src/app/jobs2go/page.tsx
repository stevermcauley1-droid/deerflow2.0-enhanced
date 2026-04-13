"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

type ParseResponse = {
  title: string;
  category_code: string;
  confidence: number;
  clarifications: string[];
};

type JobResponse = {
  id: string;
  title: string;
  description: string;
  category_code: string;
  status?: string;
};

type Candidate = {
  worker_id: string;
  score: number;
  eta_minutes: number;
  price_hourly_cents: number;
  why: string[];
};

type OfferResponse = {
  id: string;
  job_id: string;
  worker_id: string;
  status: string;
};

type BookingResponse = {
  booking_id: string;
  job_id: string;
  offer_id: string;
  status: string;
};

type PaymentResponse = {
  id: string;
  booking_id: string;
  escrow_status: string;
  gross_amount_cents: number;
  platform_fee_cents: number;
  worker_payout_cents: number;
};

const cardClass =
  "rounded-2xl border border-zinc-200/70 bg-white/70 p-5 shadow-[0_10px_30px_-15px_rgba(0,0,0,0.25)] backdrop-blur dark:border-zinc-700/60 dark:bg-zinc-900/60";

export default function Jobs2GoPilotPage() {
  const [apiBase, setApiBase] = useState("http://localhost:8001");
  const [jobInput, setJobInput] = useState(
    "Need someone to assemble a wardrobe this afternoon near downtown. Budget around $60/hour.",
  );
  const [employerId, setEmployerId] = useState("pilot_employer");
  const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedWorkerId, setSelectedWorkerId] = useState("w_1");
  const [offerAmount, setOfferAmount] = useState(12000);
  const [offer, setOffer] = useState<OfferResponse | null>(null);
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState<string | null>(null);

  const hasJob = useMemo(() => Boolean(job?.id), [job]);

  async function callApi<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${apiBase}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const payload = (await response.json()) as { detail?: string };
        detail = payload.detail ?? detail;
      } catch {
        // Keep default status text when response body is not JSON.
      }
      throw new Error(`${response.status}: ${detail}`);
    }

    return (await response.json()) as T;
  }

  async function parseJob() {
    setError(null);
    setStatus("Parsing job intent...");
    try {
      const parsed = await callApi<ParseResponse>("/v1/jobs/parse", {
        method: "POST",
        body: JSON.stringify({ input_text: jobInput, location_hint: "Downtown" }),
      });
      setParseResult(parsed);
      setStatus("Job intent parsed");
    } catch (err) {
      setError((err as Error).message);
      setStatus("Parse failed");
    }
  }

  async function createJob() {
    setError(null);
    setStatus("Creating job...");
    try {
      const created = await callApi<JobResponse>("/v1/jobs", {
        method: "POST",
        body: JSON.stringify({
          employer_id: employerId,
          title: parseResult?.title ?? "General Help",
          description: jobInput,
          category_code: parseResult?.category_code ?? "general.task",
          location_mode: "onsite",
          skill_level: "experienced",
          urgency: "same_day",
          budget_type: "hourly",
          budget_min_cents: 5000,
          budget_max_cents: 7000,
          currency: "USD",
        }),
      });
      setJob(created);
      setStatus(`Job created: ${created.id}`);
    } catch (err) {
      setError((err as Error).message);
      setStatus("Create failed");
    }
  }

  async function loadCandidates() {
    if (!job?.id) return;
    setError(null);
    setStatus("Ranking candidates...");
    try {
      const result = await callApi<{ candidates: Candidate[] }>(`/v1/match/jobs/${job.id}/candidates`, {
        method: "POST",
      });
      setCandidates(result.candidates);
      if (result.candidates[0]) {
        setSelectedWorkerId(result.candidates[0].worker_id);
      }
      setStatus("Candidates loaded");
    } catch (err) {
      setError((err as Error).message);
      setStatus("Matching failed");
    }
  }

  async function sendOffer() {
    if (!job?.id) return;
    setError(null);
    setStatus("Sending offer...");
    try {
      const createdOffer = await callApi<OfferResponse>(`/v1/jobs/${job.id}/offers`, {
        method: "POST",
        body: JSON.stringify({
          worker_id: selectedWorkerId,
          proposed_amount_cents: offerAmount,
          currency: "USD",
          message: "Can you start within 45 minutes?",
        }),
      });
      setOffer(createdOffer);
      setStatus(`Offer created: ${createdOffer.id}`);
    } catch (err) {
      setError((err as Error).message);
      setStatus("Offer failed");
    }
  }

  async function workerDecision(decision: "accept" | "decline") {
    if (!offer?.id) return;
    setError(null);
    setStatus(`Worker ${decision}ing offer...`);
    try {
      const updated = await callApi<OfferResponse>(`/v1/offers/${offer.id}/${decision}`, {
        method: "POST",
      });
      setOffer(updated);
      if (decision === "accept" && job?.id) {
        const bookingState = await callApi<BookingResponse>(`/v1/jobs/${job.id}/booking`);
        setBooking(bookingState);
      }
      setStatus(`Offer ${decision}ed`);
    } catch (err) {
      setError((err as Error).message);
      setStatus("Worker decision failed");
    }
  }

  async function startAndCompleteJob() {
    if (!job?.id) return;
    setError(null);
    setStatus("Starting job...");
    try {
      const started = await callApi<BookingResponse>(`/v1/jobs/${job.id}/start`, { method: "POST" });
      const completed = await callApi<BookingResponse>(`/v1/jobs/${job.id}/complete`, {
        method: "POST",
        body: JSON.stringify({ completion_notes: "Completed with photo proof" }),
      });
      setBooking(completed ?? started);
      setStatus("Job completed");
    } catch (err) {
      setError((err as Error).message);
      setStatus("Lifecycle update failed");
    }
  }

  async function runPaymentFlow() {
    if (!booking?.booking_id) return;
    setError(null);
    setStatus("Authorizing escrow...");
    try {
      await callApi<PaymentResponse>("/v1/payments/escrow/authorize", {
        method: "POST",
        body: JSON.stringify({
          booking_id: booking.booking_id,
          payment_method_id: "pm_demo_card",
          amount_cents: offerAmount,
          currency: "USD",
        }),
      });
      const released = await callApi<PaymentResponse>("/v1/payments/escrow/release", {
        method: "POST",
        body: JSON.stringify({ booking_id: booking.booking_id }),
      });
      setPayment(released);
      setStatus("Escrow released");
    } catch (err) {
      setError((err as Error).message);
      setStatus("Payment flow failed");
    }
  }

  async function sendTrustReport() {
    if (!job?.id) return;
    setError(null);
    setStatus("Submitting trust report...");
    try {
      await callApi<{ id: string }>("/v1/trust/reports", {
        method: "POST",
        body: JSON.stringify({
          target_user_id: selectedWorkerId,
          job_id: job.id,
          reason_code: "off_platform_payment_request",
          description: "Demo trust escalation from pilot cockpit",
        }),
      });
      setStatus("Trust report submitted");
    } catch (err) {
      setError((err as Error).message);
      setStatus("Trust report failed");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_15%_15%,#ffe8bf,transparent_35%),radial-gradient(circle_at_85%_5%,#c9f8ff,transparent_25%),linear-gradient(150deg,#fffaf0,#f7f5ff_45%,#eef9ff)] px-4 py-8 text-zinc-900 dark:bg-[radial-gradient(circle_at_15%_15%,#3a2a0d,transparent_35%),radial-gradient(circle_at_85%_5%,#0f2f38,transparent_25%),linear-gradient(150deg,#1f1b16,#1c1a26_45%,#13212b)] dark:text-zinc-100 sm:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="rounded-3xl border border-zinc-200/80 bg-white/75 p-6 shadow-xl backdrop-blur dark:border-zinc-700/60 dark:bg-zinc-900/70">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700 dark:text-amber-300">Jobs2Go Pilot Cockpit</p>
          <h1 className="mt-2 text-3xl font-semibold leading-tight sm:text-4xl">
            Employer to Worker Completion Flow
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-zinc-700 dark:text-zinc-300">
            This page runs the full pilot sequence from AI intake to escrow release. Execute each action in order and watch the status rail.
          </p>
          <div className="mt-4 grid gap-2 sm:grid-cols-[220px_1fr] sm:items-center">
            <label className="text-sm font-medium">API Base URL</label>
            <input
              className="h-10 rounded-xl border border-zinc-300 bg-white/80 px-3 text-sm shadow-inner outline-none ring-0 focus:border-amber-500 dark:border-zinc-600 dark:bg-zinc-800"
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="http://localhost:8001"
            />
          </div>
          <div className="mt-4">
            <Link
              href="/jobs2go/ops"
              className="inline-flex rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-100 dark:border-zinc-600 dark:hover:bg-zinc-800"
            >
              Open Ops KPI Dashboard
            </Link>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className={cardClass}>
            <h2 className="text-xl font-semibold">1. Employer Intake</h2>
            <textarea
              className="mt-3 min-h-28 w-full rounded-xl border border-zinc-300 bg-white/90 p-3 text-sm outline-none focus:border-amber-500 dark:border-zinc-600 dark:bg-zinc-800"
              value={jobInput}
              onChange={(event) => setJobInput(event.target.value)}
            />
            <div className="mt-3 grid gap-2 sm:grid-cols-[120px_1fr] sm:items-center">
              <label className="text-sm font-medium">Employer ID</label>
              <input
                className="h-10 rounded-xl border border-zinc-300 bg-white/90 px-3 text-sm outline-none focus:border-amber-500 dark:border-zinc-600 dark:bg-zinc-800"
                value={employerId}
                onChange={(event) => setEmployerId(event.target.value)}
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-amber-400 dark:text-zinc-900" onClick={parseJob}>
                Parse Job
              </button>
              <button className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-medium text-white" onClick={createJob}>
                Create Job
              </button>
            </div>
            {parseResult && (
              <div className="mt-4 rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-700 dark:bg-zinc-800/70">
                <p>
                  <strong>Category:</strong> {parseResult.category_code}
                </p>
                <p>
                  <strong>Confidence:</strong> {Math.round(parseResult.confidence * 100)}%
                </p>
                {parseResult.clarifications.length > 0 && (
                  <p>
                    <strong>Clarifications:</strong> {parseResult.clarifications.join(" | ")}
                  </p>
                )}
              </div>
            )}
            {job && (
              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-700/60 dark:bg-emerald-900/20 dark:text-emerald-200">
                Job created: {job.id}
              </div>
            )}
          </article>

          <article className={cardClass}>
            <h2 className="text-xl font-semibold">2. Matching and Offer</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={loadCandidates}
                disabled={!hasJob}
              >
                Load Candidates
              </button>
              <button
                className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={sendOffer}
                disabled={!hasJob}
              >
                Send Offer
              </button>
            </div>

            <div className="mt-4 grid gap-2 sm:grid-cols-[110px_1fr] sm:items-center">
              <label className="text-sm font-medium">Worker ID</label>
              <input
                className="h-10 rounded-xl border border-zinc-300 bg-white/90 px-3 text-sm outline-none focus:border-indigo-500 dark:border-zinc-600 dark:bg-zinc-800"
                value={selectedWorkerId}
                onChange={(event) => setSelectedWorkerId(event.target.value)}
              />
              <label className="text-sm font-medium">Offer cents</label>
              <input
                type="number"
                className="h-10 rounded-xl border border-zinc-300 bg-white/90 px-3 text-sm outline-none focus:border-indigo-500 dark:border-zinc-600 dark:bg-zinc-800"
                value={offerAmount}
                onChange={(event) => setOfferAmount(Number(event.target.value))}
              />
            </div>

            <div className="mt-4 space-y-2">
              {candidates.map((candidate) => (
                <div key={candidate.worker_id} className="rounded-xl border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-700 dark:bg-zinc-800/70">
                  <p className="font-medium">{candidate.worker_id}</p>
                  <p>
                    Score {candidate.score} | ETA {candidate.eta_minutes}m | ${candidate.price_hourly_cents / 100}/hr
                  </p>
                  <p className="text-zinc-600 dark:text-zinc-300">{candidate.why.join(", ")}</p>
                </div>
              ))}
            </div>

            {offer && (
              <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-900 dark:border-indigo-700/60 dark:bg-indigo-900/20 dark:text-indigo-200">
                Offer {offer.id} is {offer.status}
              </div>
            )}
          </article>

          <article className={cardClass}>
            <h2 className="text-xl font-semibold">3. Worker Decision and Job Lifecycle</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => workerDecision("accept")}
                disabled={!offer?.id}
              >
                Accept Offer
              </button>
              <button
                className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => workerDecision("decline")}
                disabled={!offer?.id}
              >
                Decline Offer
              </button>
              <button
                className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
                onClick={startAndCompleteJob}
                disabled={!job?.id || offer?.status !== "accepted"}
              >
                Start + Complete
              </button>
            </div>
            {booking && (
              <div className="mt-4 rounded-xl border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900 dark:border-teal-700/60 dark:bg-teal-900/20 dark:text-teal-200">
                Booking {booking.booking_id} status: {booking.status}
              </div>
            )}
          </article>

          <article className={cardClass}>
            <h2 className="text-xl font-semibold">4. Escrow and Trust</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="rounded-xl bg-orange-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={runPaymentFlow}
                disabled={!booking?.booking_id}
              >
                Authorize + Release Escrow
              </button>
              <button
                className="rounded-xl bg-fuchsia-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                onClick={sendTrustReport}
                disabled={!job?.id}
              >
                Submit Trust Report
              </button>
            </div>
            {payment && (
              <div className="mt-4 rounded-xl border border-orange-200 bg-orange-50 p-3 text-sm text-orange-900 dark:border-orange-700/60 dark:bg-orange-900/20 dark:text-orange-200">
                Payment {payment.id}: {payment.escrow_status} | gross {payment.gross_amount_cents} | fee {payment.platform_fee_cents} | payout {payment.worker_payout_cents}
              </div>
            )}
          </article>
        </section>

        <footer className="rounded-2xl border border-zinc-200/70 bg-white/70 p-4 text-sm dark:border-zinc-700/60 dark:bg-zinc-900/60">
          <p>
            <strong>Status:</strong> {status}
          </p>
          {error && <p className="mt-1 text-rose-600 dark:text-rose-300">Error: {error}</p>}
        </footer>
      </div>
    </div>
  );
}
