"use client";

import React, { useState } from "react";
import type { ActivityItem, JournalEntry, WeekSummary, WellnessEntry } from "@/types/training";

function formatPace(secPerKm: number | null): string {
  if (!secPerKm || secPerKm <= 0) return "-";
  const mins = Math.floor(secPerKm / 60);
  const secs = Math.round(secPerKm % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}/km`;
}

function buildTakeaways(w: WeekSummary): string[] {
  const notes: string[] = [];
  if (w.impact_to_cardio_ratio !== null) {
    if (w.impact_to_cardio_ratio > 1.1) {
      notes.push(`High mechanical load vs cardio (ratio ${w.impact_to_cardio_ratio.toFixed(2)}) — heavy downhill/pounding week; prioritize soft surfaces & recovery.`);
    } else if (w.impact_to_cardio_ratio < 0.75) {
      notes.push(`Cardio-dominant week (ratio ${w.impact_to_cardio_ratio.toFixed(2)}) — engine worked harder than legs (steep climbs, heat, or intensity).`);
    } else {
      notes.push(`Balanced Impact:Cardio ratio (${w.impact_to_cardio_ratio.toFixed(2)}).`);
    }
  }

  if (w.polarization.easy_pct >= 80 && w.polarization.hard_pct === 0) {
    notes.push(`SWAP "Big Salad": ${w.polarization.easy_pct}% easy base, 0% top-end — consider adding 4–6×20s flat strides or short hill sprints.`);
  } else if (w.polarization.easy_pct < 75) {
    notes.push(`SWAP Polarization alert: only ${w.polarization.easy_pct}% easy — watch for gray-zone creep (${w.polarization.tempo_pct}% tempo).`);
  } else {
    notes.push(`SWAP Polarization on target: ${w.polarization.easy_pct}% easy / ${w.polarization.tempo_pct}% tempo / ${w.polarization.hard_pct}% hard.`);
  }

  if (w.avg_cadence !== null) {
    if (w.avg_cadence < 168) {
      notes.push(`Benzie Form: avg cadence ${w.avg_cadence.toFixed(0)} spm (below 175–185 target; check if hiking/steep trails pulled average down).`);
    } else {
      notes.push(`Benzie Form: crisp ${w.avg_cadence.toFixed(0)} spm avg cadence.`);
    }
  }

  if (w.avg_decoupling_pct !== null) {
    notes.push(`Uphill Athlete Drift: ${w.avg_decoupling_pct.toFixed(1)}% (${w.avg_decoupling_pct < 5 ? "strong aerobic durability" : "moderate/high cardiac drift"}).`);
  }

  if (w.injury_risk_score !== undefined && w.injury_risk_score !== null) {
    const acwrText = w.acwr !== undefined && w.acwr !== null ? ` · ACWR ${w.acwr.toFixed(2)}` : "";
    const factorsText = w.risk_factors && w.risk_factors.length > 0 ? ` (${w.risk_factors[0]})` : "";
    notes.push(`Injury Risk: ${(w.injury_risk_level || "unknown").toUpperCase()} ${w.injury_risk_score.toFixed(0)}/100${acwrText}${factorsText}.`);
  }
  return notes;
}

function formatDuration(minutes: number): string {
  const totalMins = Math.round(minutes);
  const h = Math.floor(totalMins / 60);
  const m = totalMins % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function TrainingLogFeed({
  weeks,
  activities,
  wellness,
  journals,
}: {
  weeks: WeekSummary[];
  activities: ActivityItem[];
  wellness: WellnessEntry[];
  journals: JournalEntry[];
}) {
  const ordered = [...weeks].filter((w) => w.sessions > 0).reverse();
  const [expandedWeek, setExpandedWeek] = useState<string | null>(
    ordered.length > 0 ? ordered[0].week : null
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.15rem" }}>
      {ordered.map((w) => {
        const weekActs = activities.filter((a) => a.date >= w.start_date && a.date <= w.end_date);
        const weekWell = wellness.filter((x) => x.date >= w.start_date && x.date <= w.end_date);
        const weekJourn = journals.filter((j) => j.date >= w.start_date && j.date <= w.end_date);
        const takeaways = buildTakeaways(w);
        const isOpen = expandedWeek === w.week;

        const avgRhr = weekWell.filter((x) => x.resting_hr).map((x) => x.resting_hr as number);
        const avgHrv = weekWell.filter((x) => x.hrv_ms).map((x) => x.hrv_ms as number);

        return (
          <article key={w.week} className="card">
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem" }}>
              <div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)" }} className="mono">
                  {w.week} · {w.start_date} → {w.end_date}
                </div>
                <h2 style={{ margin: "0.2rem 0 0", fontSize: "1.25rem", letterSpacing: "-0.01em" }}>
                  {w.distance_km.toFixed(1)} km across {w.sessions} sessions · {formatDuration(w.duration_min)} · +{Math.round(w.elevation_gain_m).toLocaleString("en-US")}m
                </h2>
              </div>

              <div style={{ display: "flex", gap: "0.45rem", flexWrap: "wrap" }}>
                <span className="badge mono" style={{ color: "var(--accent-impact)" }}>
                  Impact {w.impact_score.toFixed(0)}
                </span>
                <span className="badge mono" style={{ color: "var(--accent-cardio)" }}>
                  Cardio {w.cardio_score.toFixed(0)}
                </span>
                {w.speed_score !== undefined && (
                  <span className="badge mono" style={{ color: "var(--accent-tempo)" }}>
                    Speed {w.speed_score.toFixed(0)}
                  </span>
                )}
                {w.acwr !== undefined && w.acwr !== null && (
                  <span className="badge mono">ACWR {w.acwr.toFixed(2)}</span>
                )}
                {w.injury_risk_score !== undefined && w.injury_risk_score !== null && (
                  <span
                    className="badge mono"
                    style={{
                      color:
                        w.injury_risk_level === "high"
                          ? "var(--accent-hard)"
                          : w.injury_risk_level === "medium"
                          ? "var(--accent-tempo)"
                          : "var(--accent-easy)",
                    }}
                  >
                    Risk {w.injury_risk_score.toFixed(0)}/100
                  </span>
                )}
                {w.aerobic_efficiency !== null && (
                  <span className="badge mono">Eff {w.aerobic_efficiency.toFixed(2)}</span>
                )}
              </div>
            </header>

            {/* Polarization Bar */}
            <div style={{ marginTop: "0.9rem", height: 7, borderRadius: 999, overflow: "hidden", display: "flex", background: "#eee" }}>
              <div style={{ width: `${w.polarization.easy_pct}%`, background: "var(--accent-easy)" }} title={`Easy ${w.polarization.easy_pct}%`} />
              <div style={{ width: `${w.polarization.tempo_pct}%`, background: "var(--accent-tempo)" }} title={`Tempo ${w.polarization.tempo_pct}%`} />
              <div style={{ width: `${w.polarization.hard_pct}%`, background: "var(--accent-hard)" }} title={`Hard ${w.polarization.hard_pct}%`} />
            </div>

            {/* Editorial Methodology Takeaways */}
            <ul style={{ margin: "0.9rem 0 0", paddingLeft: "1.15rem", fontSize: "0.9rem", color: "#33302c" }}>
              {takeaways.map((t, idx) => (
                <li key={idx} style={{ marginBottom: "0.25rem" }}>{t}</li>
              ))}
            </ul>

            {/* Wellness + N=1 Journal Strip */}
            {(avgRhr.length > 0 || avgHrv.length > 0 || weekJourn.length > 0) && (
              <div style={{ marginTop: "0.85rem", padding: "0.65rem 0.85rem", background: "#f7f5f0", borderRadius: 8, fontSize: "0.82rem" }}>
                <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }} className="mono">
                  {avgRhr.length > 0 && (
                    <span>Avg RHR: {(avgRhr.reduce((a, b) => a + b, 0) / avgRhr.length).toFixed(0)} bpm</span>
                  )}
                  {avgHrv.length > 0 && (
                    <span>Avg HRV: {(avgHrv.reduce((a, b) => a + b, 0) / avgHrv.length).toFixed(0)} ms</span>
                  )}
                </div>
                {weekJourn.map((j) => (
                  <div key={j.date} style={{ marginTop: "0.35rem", color: "var(--muted)" }}>
                    <strong style={{ color: "var(--text)" }}>{j.date} Journal:</strong> RPE {j.rpe ?? "-"}/10 · Soreness {j.soreness ?? "-"}/10 · Mood: {j.mood || "-"} {j.notes ? `— "${j.notes}"` : ""}
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: "0.9rem" }}>
              <button
                type="button"
                onClick={() => setExpandedWeek(isOpen ? null : w.week)}
                style={{
                  background: "transparent",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "0.35rem 0.7rem",
                  fontSize: "0.8rem",
                  cursor: "pointer",
                  color: "var(--text)",
                }}
              >
                {isOpen ? `Hide ${weekActs.length} runs ▲` : `Show ${weekActs.length} runs ▼`}
              </button>
            </div>

            {isOpen && (
              <div className="table-wrap" style={{ marginTop: "0.75rem" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Activity</th>
                      <th className="num">Dist</th>
                      <th className="num">Dur</th>
                      <th className="num">Vert+</th>
                      <th className="num">GAP</th>
                      <th className="num">HR</th>
                      <th className="num">Cad</th>
                      <th className="num">Impact</th>
                      <th className="num">Cardio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {weekActs.map((a) => (
                      <tr key={a.id}>
                        <td className="mono">{a.date}</td>
                        <td>{a.name || a.type || "Run"}</td>
                        <td className="num">{a.distance_km.toFixed(1)} km</td>
                        <td className="num">{a.duration_min.toFixed(0)}m</td>
                        <td className="num">{a.elevation_gain_m ? `+${a.elevation_gain_m.toFixed(0)}m` : "-"}</td>
                        <td className="num">{formatPace(a.gap_pace_sec_per_km)}</td>
                        <td className="num">{a.avg_hr ?? "-"}</td>
                        <td className="num">{a.cadence ? a.cadence.toFixed(0) : "-"}</td>
                        <td className="num" style={{ color: "var(--accent-impact)" }}>{a.impact_score.toFixed(0)}</td>
                        <td className="num" style={{ color: "var(--accent-cardio)" }}>{a.cardio_score.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
