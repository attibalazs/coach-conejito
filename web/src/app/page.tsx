import fs from "fs";
import Link from "next/link";
import path from "path";
import React from "react";
import { DualLoadChart, EfficiencyAndCadenceChart } from "@/components/Charts";
import { TrainingLogFeed } from "@/components/TrainingLogFeed";
import type { DualLoadBlock, TrainingExport, WellnessEntry } from "@/types/training";

export const dynamic = "force-dynamic";

function loadTrainingData(): TrainingExport | null {
  const filePath = path.join(process.cwd(), "public", "data", "training.json");
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as TrainingExport;
}

function formatInt(val: number): string {
  return Math.round(val).toLocaleString("en-US");
}

function formatDuration(minutes: number): string {
  const totalMins = Math.round(minutes);
  const h = Math.floor(totalMins / 60);
  const m = totalMins % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function getTsbStatus(tsb: number): { label: string; color: string } {
  if (tsb >= 5) return { label: "Fresh", color: "var(--accent-easy)" };
  if (tsb >= -10) return { label: "Optimal", color: "var(--accent-cardio)" };
  if (tsb >= -25) return { label: "Productive", color: "var(--accent-tempo)" };
  return { label: "Overreaching", color: "var(--accent-hard)" };
}

function DeltaPill({ pct, label }: { pct: number | null | undefined; label?: string }) {
  if (pct === null || pct === undefined) return null;
  const sign = pct > 0 ? "+" : "";
  const color = pct >= 0 ? "var(--accent-easy)" : "var(--accent-tempo)";
  return (
    <span className="badge mono" style={{ color, fontSize: "0.7rem", padding: "0.12rem 0.45rem" }}>
      {sign}{pct.toFixed(1)}%{label ? ` ${label}` : ""}
    </span>
  );
}

function LoadCard({
  title,
  subtitle,
  accentColor,
  block,
  deltaPct,
}: {
  title: string;
  subtitle: string;
  accentColor: string;
  block: DualLoadBlock;
  deltaPct?: number | null;
}) {
  const status = getTsbStatus(block.tsb);
  const tsbStr = block.tsb >= 0 ? `+${block.tsb.toFixed(0)}` : block.tsb.toFixed(0);

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.4rem" }}>
        <span style={{ fontSize: "0.73rem", color: accentColor, fontWeight: 700, letterSpacing: "0.03em" }}>
          {title}
        </span>
        <span className="badge mono" style={{ color: status.color, fontSize: "0.7rem", padding: "0.12rem 0.45rem" }}>
          {status.label}
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", marginTop: "0.3rem" }}>
        <span style={{ fontSize: "1.65rem", fontWeight: 700, lineHeight: 1.1 }} className="mono">
          {tsbStr}
        </span>
        <span style={{ fontSize: "0.78rem", color: "var(--muted)" }} className="mono">
          Form (TSB)
        </span>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.45rem", fontSize: "0.78rem", color: "var(--muted)" }} className="mono">
        <span>
          CTL <strong style={{ color: "var(--text)" }}>{block.ctl.toFixed(0)}</strong> · ATL{" "}
          <strong style={{ color: "var(--text)" }}>{block.atl.toFixed(0)}</strong>
        </span>
        <DeltaPill pct={deltaPct} />
      </div>

      <div style={{ fontSize: "0.74rem", color: "var(--muted)", marginTop: "0.25rem" }}>
        {subtitle}
      </div>
    </div>
  );
}

function avgMetric(entries: WellnessEntry[], getter: (w: WellnessEntry) => number | null): number | null {
  const vals = entries.map(getter).filter((v): v is number => v !== null && v > 0);
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

export default function HomePage() {
  const data = loadTrainingData();

  if (!data) {
    return (
      <main className="container">
        <div className="card">
          <h1>No training data found</h1>
          <p>
            Run <code>coach -u atti export --days 180 --format json --out web/public/data/training.json</code>{" "}
            to generate your training log dataset.
          </p>
        </div>
      </main>
    );
  }

  const { summary, weekly_trends, activities, wellness, journals } = data;
  const imp = summary.dual_load.impact;
  const car = summary.dual_load.cardio;
  const spd = summary.dual_load.speed;
  const delta = summary.delta_vs_previous;

  const activeWeeks = weekly_trends.filter((w) => w.sessions > 0);
  const latestWeek = activeWeeks.length > 0 ? activeWeeks[activeWeeks.length - 1] : null;

  const recentWellness = wellness.slice(-7);
  const avgRhr = avgMetric(recentWellness, (w) => w.resting_hr);
  const avgHrv = avgMetric(recentWellness, (w) => w.hrv_ms);
  const avgSleep = avgMetric(recentWellness, (w) => w.sleep_score);
  const avgBb = avgMetric(recentWellness, (w) => w.body_battery_high);

  return (
    <main className="container">
      {/* AstroPaper Hero */}
      <header className="hero">
        <p className="hero-kicker mono">
          Athlete: {data.user_id} · {data.window.start} → {data.window.end} ({data.window.days}d)
        </p>
        <h1>Endurance &amp; Trail Log</h1>
        <p className="hero-sub">
          Weekly training notes, 3-pillar Albon fitness (Impact, Cardio, Speed), SWAP running economy, Uphill Athlete drift, and Benzie biomechanics.
        </p>
      </header>

      {/* Featured Race Post */}
      <Link href="/races/five-trails-2026" className="featured-card">
        <span className="featured-badge mono">Featured Race Debrief · 2026-11-14</span>
        <h2 className="serif" style={{ margin: "0 0 6px", fontSize: "1.45rem" }}>
          5 Trails 50k Ultra — 05:34:21 (22nd / 108) &amp; Road to Granite Peaks (+4,000m)
        </h2>
        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.92rem" }}>
          Staggered-start negative split (45th → 22nd), 5 km Strava stream GAP &amp; HR breakdown, Borbala Hidegh&apos;s 4th Female finish, and 10h 49m–11h 23m Granite Peaks projection.
        </p>
      </Link>

      {/* Tier 1: Volume, Latest Week, Efficiency/Drift, Polarization */}
      <section className="grid-4" style={{ marginBottom: "0.85rem" }}>
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.73rem", color: "var(--muted)", fontWeight: 600 }}>VOLUME ({data.window.days}D)</span>
            <DeltaPill pct={delta?.distance_pct} />
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.25rem", lineHeight: 1.15 }} className="mono">
            {formatInt(summary.distance_km)} km
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.35rem" }} className="mono">
            {summary.sessions} runs · {formatDuration(summary.duration_min)} · +{formatInt(summary.elevation_gain_m)}m
          </div>
          {summary.cross_training && (summary.cross_training.cycling_sessions > 0 || summary.cross_training.strength_sessions > 0) && (
            <div style={{ fontSize: "0.74rem", color: "var(--muted)", marginTop: "0.2rem" }} className="mono">
              +{summary.cross_training.cycling_sessions} bike ({formatInt(summary.cross_training.cycling_km)} km) · {summary.cross_training.strength_sessions} strength
            </div>
          )}
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.73rem", color: "var(--muted)", fontWeight: 600 }}>
              LATEST WEEK {latestWeek ? `(${latestWeek.week.slice(5)})` : ""}
            </span>
            {latestWeek?.impact_to_cardio_ratio !== null && latestWeek?.impact_to_cardio_ratio !== undefined && (
              <span className="badge mono" style={{ fontSize: "0.7rem", padding: "0.12rem 0.45rem" }}>
                I:C {latestWeek.impact_to_cardio_ratio.toFixed(2)}
              </span>
            )}
          </div>
          {latestWeek ? (
            <>
              <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.25rem", lineHeight: 1.15 }} className="mono">
                {latestWeek.distance_km.toFixed(1)} km
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.35rem" }} className="mono">
                {latestWeek.sessions} runs · {formatDuration(latestWeek.duration_min)} · +{formatInt(latestWeek.elevation_gain_m)}m
              </div>
              <div style={{ fontSize: "0.74rem", color: "var(--muted)", marginTop: "0.2rem" }} className="mono">
                {latestWeek.start_date} → {latestWeek.end_date}
              </div>
            </>
          ) : (
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "0.4rem" }}>No recent runs</div>
          )}
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.73rem", color: "var(--muted)", fontWeight: 600 }}>AEROBIC ECONOMY</span>
            <DeltaPill pct={delta?.efficiency_pct} />
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.25rem", lineHeight: 1.15 }} className="mono">
            {summary.aerobic_efficiency !== null ? summary.aerobic_efficiency.toFixed(2) : "-"}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "0.35rem" }} className="mono">
            GAP/HR · {summary.avg_hr ? `${summary.avg_hr.toFixed(0)} bpm avg` : "HR n/a"}
          </div>
          <div style={{ fontSize: "0.74rem", color: summary.avg_decoupling_pct !== null && summary.avg_decoupling_pct < 5 ? "var(--accent-easy)" : "var(--muted)", marginTop: "0.2rem" }} className="mono">
            {summary.avg_decoupling_pct !== null ? `${summary.avg_decoupling_pct.toFixed(1)}% cardiac drift` : "Drift n/a"}
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ fontSize: "0.73rem", color: "var(--muted)", fontWeight: 600 }}>SWAP POLARIZATION</span>
            {latestWeek && latestWeek.polarization.easy_pct < 75 && (
              <span className="badge mono" style={{ color: "var(--accent-tempo)", fontSize: "0.7rem", padding: "0.12rem 0.45rem" }}>
                Wk {latestWeek.polarization.easy_pct.toFixed(0)}% easy
              </span>
            )}
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.25rem", lineHeight: 1.15 }} className="mono">
            {summary.polarization.easy_pct}% Easy
          </div>
          <div style={{ marginTop: "0.4rem", height: 6, borderRadius: 999, overflow: "hidden", display: "flex", background: "#eee" }}>
            <div style={{ width: `${summary.polarization.easy_pct}%`, background: "var(--accent-easy)" }} title={`Easy ${summary.polarization.easy_pct}%`} />
            <div style={{ width: `${summary.polarization.tempo_pct}%`, background: "var(--accent-tempo)" }} title={`Tempo ${summary.polarization.tempo_pct}%`} />
            <div style={{ width: `${summary.polarization.hard_pct}%`, background: "var(--accent-hard)" }} title={`Hard ${summary.polarization.hard_pct}%`} />
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.3rem" }} className="mono">
            {summary.polarization.tempo_pct}% tempo · {summary.polarization.hard_pct}% hard
          </div>
        </div>
      </section>

      {/* Tier 2: Dual-Load + Speed Form Cards */}
      <section className="grid-3" style={{ marginBottom: "0.85rem" }}>
        <LoadCard
          title="ALBON IMPACT"
          subtitle="Mechanical leg load (musculoskeletal)"
          accentColor="var(--accent-impact)"
          block={imp}
          deltaPct={delta?.impact_pct}
        />
        <LoadCard
          title="CARDIO TRIMP"
          subtitle="Cardiovascular engine load"
          accentColor="var(--accent-cardio)"
          block={car}
          deltaPct={delta?.cardio_pct}
        />
        {spd && (
          <LoadCard
            title="SPEED FITNESS"
            subtitle="GAP output vs threshold (4:30/km)"
            accentColor="var(--accent-tempo)"
            block={spd}
          />
        )}
      </section>

      {/* Tier 3: 7-Day Wellness & Recovery Strip */}
      {(avgRhr !== null || avgHrv !== null || avgSleep !== null || avgBb !== null) && (
        <section
          className="card"
          style={{
            marginBottom: "1.25rem",
            padding: "0.75rem 1.25rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "0.75rem",
            background: "#f7f5f0",
          }}
        >
          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--muted)", letterSpacing: "0.04em" }} className="mono">
            7D RECOVERY
          </span>
          <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", fontSize: "0.82rem" }} className="mono">
            {avgRhr !== null && (
              <span>
                RHR <strong style={{ color: "var(--text)" }}>{avgRhr.toFixed(0)}</strong> bpm
              </span>
            )}
            {avgHrv !== null && (
              <span>
                HRV <strong style={{ color: "var(--text)" }}>{avgHrv.toFixed(0)}</strong> ms
              </span>
            )}
            {avgSleep !== null && (
              <span>
                Sleep <strong style={{ color: "var(--text)" }}>{avgSleep.toFixed(0)}</strong>/100
              </span>
            )}
            {avgBb !== null && (
              <span>
                Body Battery <strong style={{ color: "var(--text)" }}>{avgBb.toFixed(0)}</strong>
              </span>
            )}
          </div>
        </section>
      )}

      {/* Interactive Trend Charts */}
      <section style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2rem" }}>
        <DualLoadChart weeks={weekly_trends} />
        <EfficiencyAndCadenceChart weeks={weekly_trends} />
      </section>

      {/* Chronological Weekly Blog / Training Log */}
      <section>
        <h2 style={{ fontSize: "1.25rem", marginBottom: "1rem", letterSpacing: "-0.01em" }}>
          Weekly Training Log
        </h2>
        <TrainingLogFeed
          weeks={weekly_trends}
          activities={activities}
          wellness={wellness}
          journals={journals}
        />
      </section>
    </main>
  );
}
