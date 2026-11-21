"use client";

import React, { useState } from "react";
import type { WeekSummary } from "@/types/training";

export function DualLoadChart({ weeks }: { weeks: WeekSummary[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const [showSpeed, setShowSpeed] = useState(false);
  const recent = weeks.slice(-16);
  if (recent.length === 0) return null;

  const hasSpeed = recent.some((w) => w.speed_score !== undefined);
  const maxVal = Math.max(
    ...recent.flatMap((w) => [
      w.impact_score,
      w.cardio_score,
      showSpeed && w.speed_score !== undefined ? w.speed_score : 0,
    ]),
    10
  );

  const width = 820;
  const height = 210;
  const padL = 42;
  const padB = 28;
  const padT = 14;
  const plotW = width - padL - 12;
  const plotH = height - padT - padB;
  const groupW = plotW / recent.length;
  const barsPerGroup = showSpeed && hasSpeed ? 3 : 2;
  const barW = Math.max(5, Math.min(16, (groupW * 0.72) / barsPerGroup));

  const active = hovered !== null ? recent[hovered] : null;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem" }}>Albon Dual-Load: Mechanical Impact vs. Cardio TRIMP</h3>
          <p style={{ margin: "0.15rem 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>
            Last {recent.length} weeks · Separates musculoskeletal pounding from cardiovascular strain
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.9rem", alignItems: "center", fontSize: "0.78rem" }}>
          <span><span style={{ display: "inline-block", width: 10, height: 10, background: "var(--accent-impact)", borderRadius: 2, marginRight: 5 }} />Impact</span>
          <span><span style={{ display: "inline-block", width: 10, height: 10, background: "var(--accent-cardio)", borderRadius: 2, marginRight: 5 }} />Cardio</span>
          {showSpeed && hasSpeed && (
            <span><span style={{ display: "inline-block", width: 10, height: 10, background: "var(--accent-tempo)", borderRadius: 2, marginRight: 5 }} />Speed</span>
          )}
          {hasSpeed && (
            <button
              type="button"
              onClick={() => setShowSpeed((s) => !s)}
              className="badge mono"
              style={{
                cursor: "pointer",
                color: showSpeed ? "var(--accent-tempo)" : "var(--muted)",
                background: showSpeed ? "#fef3c7" : "#f5f3ef",
              }}
            >
              {showSpeed ? "Hide Speed" : "+ Speed"}
            </button>
          )}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", overflow: "visible" }}>
        {[0, 0.5, 1].map((frac) => {
          const y = padT + plotH * (1 - frac);
          const label = Math.round(maxVal * frac);
          return (
            <g key={frac}>
              <line x1={padL} x2={width - 12} y1={y} y2={y} stroke="var(--border)" strokeDasharray="3 3" />
              <text x={padL - 6} y={y + 4} textAnchor="end" fontSize="10" fill="var(--muted)" className="mono">{label}</text>
            </g>
          );
        })}

        {recent.map((w, idx) => {
          const xCenter = padL + idx * groupW + groupW / 2;
          const impH = (w.impact_score / maxVal) * plotH;
          const carH = (w.cardio_score / maxVal) * plotH;
          const spdH = ((w.speed_score ?? 0) / maxVal) * plotH;
          const totalBarsW = barsPerGroup * barW + (barsPerGroup - 1) * 2;
          const startX = xCenter - totalBarsW / 2;
          const isHov = hovered === idx;
          return (
            <g
              key={w.week}
              onMouseEnter={() => setHovered(idx)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: "pointer" }}
            >
              <rect
                x={xCenter - groupW / 2}
                y={padT}
                width={groupW}
                height={plotH}
                fill={isHov ? "rgba(0,0,0,0.03)" : "transparent"}
              />
              <rect
                x={startX}
                y={padT + plotH - impH}
                width={barW}
                height={impH}
                rx={2}
                fill="var(--accent-impact)"
                opacity={hovered === null || isHov ? 0.9 : 0.45}
              />
              <rect
                x={startX + barW + 2}
                y={padT + plotH - carH}
                width={barW}
                height={carH}
                rx={2}
                fill="var(--accent-cardio)"
                opacity={hovered === null || isHov ? 0.9 : 0.45}
              />
              {showSpeed && hasSpeed && (
                <rect
                  x={startX + (barW + 2) * 2}
                  y={padT + plotH - spdH}
                  width={barW}
                  height={spdH}
                  rx={2}
                  fill="var(--accent-tempo)"
                  opacity={hovered === null || isHov ? 0.9 : 0.45}
                />
              )}
              {idx % 2 === 0 && (
                <text x={xCenter} y={height - 8} textAnchor="middle" fontSize="10" fill="var(--muted)" className="mono">
                  {w.week.slice(5)}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div style={{ minHeight: "1.4rem", marginTop: "0.4rem", fontSize: "0.8rem", color: "var(--muted)" }} className="mono">
        {active ? (
          <span>
            <strong style={{ color: "var(--text)" }}>{active.week}</strong> ({active.start_date} → {active.end_date}) ·{" "}
            {active.distance_km.toFixed(1)} km · +{active.elevation_gain_m.toFixed(0)}m · Impact{" "}
            <strong style={{ color: "var(--accent-impact)" }}>{active.impact_score.toFixed(0)}</strong> · Cardio{" "}
            <strong style={{ color: "var(--accent-cardio)" }}>{active.cardio_score.toFixed(0)}</strong>
            {showSpeed && active.speed_score !== undefined && (
              <>
                {" "}· Speed <strong style={{ color: "var(--accent-tempo)" }}>{active.speed_score.toFixed(0)}</strong>
              </>
            )}
          </span>
        ) : (
          <span>Hover any week to inspect Impact vs. Cardio breakdown</span>
        )}
      </div>
    </div>
  );
}

interface SparklineCardProps {
  title: string;
  subtitle: string;
  weeks: WeekSummary[];
  values: (number | null)[];
  minVal: number;
  maxVal: number;
  stroke: string;
  formatVal: (v: number) => string;
  unit?: string;
  targetBand?: [number, number];
}

function SparklineCard({
  title,
  subtitle,
  weeks,
  values,
  minVal,
  maxVal,
  stroke,
  formatVal,
  unit = "",
  targetBand,
}: SparklineCardProps) {
  const [hovered, setHovered] = useState<number | null>(null);

  const width = 420;
  const height = 160;
  const padL = 38;
  const padR = 14;
  const padT = 14;
  const padB = 24;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;

  const yOf = (v: number) =>
    padT + plotH - ((v - minVal) / Math.max(maxVal - minVal, 0.001)) * plotH;
  const xOf = (i: number) =>
    padL + (i / Math.max(values.length - 1, 1)) * plotW;

  const coords = values.map((v, i) =>
    v !== null ? { i, x: xOf(i), y: yOf(v), v, week: weeks[i] } : null
  );
  const validCoords = coords.filter((c): c is NonNullable<typeof c> => c !== null);
  const points = validCoords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
  const latest = validCoords.length > 0 ? validCoords[validCoords.length - 1] : null;
  const active = hovered !== null ? coords[hovered] : null;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "0.95rem" }}>{title}</h3>
        {latest && (
          <span className="badge mono" style={{ color: stroke }}>
            {formatVal(latest.v)}{unit ? ` ${unit}` : ""}
          </span>
        )}
      </div>
      <p style={{ margin: "0.15rem 0 0.5rem", fontSize: "0.78rem", color: "var(--muted)" }}>
        {subtitle}
      </p>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", overflow: "visible" }}>
        {targetBand && (
          <rect
            x={padL}
            y={yOf(targetBand[1])}
            width={plotW}
            height={Math.max(0, yOf(targetBand[0]) - yOf(targetBand[1]))}
            fill="var(--accent-easy)"
            opacity={0.12}
          />
        )}

        {[0, 0.5, 1].map((frac) => {
          const val = minVal + (maxVal - minVal) * frac;
          const y = padT + plotH * (1 - frac);
          return (
            <g key={frac}>
              <line x1={padL} x2={width - padR} y1={y} y2={y} stroke="var(--border)" strokeDasharray="3 3" />
              <text x={padL - 6} y={y + 3.5} textAnchor="end" fontSize="9.5" fill="var(--muted)" className="mono">
                {formatVal(val)}
              </text>
            </g>
          );
        })}

        <polyline fill="none" stroke={stroke} strokeWidth="2.5" points={points} />

        {coords.map((c) => {
          if (!c) return null;
          const isHov = hovered === c.i;
          return (
            <g
              key={c.week.week}
              onMouseEnter={() => setHovered(c.i)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: "pointer" }}
            >
              <circle cx={c.x} cy={c.y} r={10} fill="transparent" />
              <circle
                cx={c.x}
                cy={c.y}
                r={isHov ? 4.5 : 2.5}
                fill={stroke}
                stroke="var(--surface)"
                strokeWidth={isHov ? 1.5 : 0}
              />
            </g>
          );
        })}

        {weeks.length > 0 && (
          <>
            <text x={padL} y={height - 6} textAnchor="start" fontSize="9.5" fill="var(--muted)" className="mono">
              {weeks[0].week.slice(5)}
            </text>
            <text x={width - padR} y={height - 6} textAnchor="end" fontSize="9.5" fill="var(--muted)" className="mono">
              {weeks[weeks.length - 1].week.slice(5)}
            </text>
          </>
        )}
      </svg>

      <div style={{ minHeight: "1.2rem", marginTop: "0.25rem", fontSize: "0.76rem", color: "var(--muted)" }} className="mono">
        {active ? (
          <span>
            <strong style={{ color: "var(--text)" }}>{active.week.week}</strong>: {formatVal(active.v)}
            {unit ? ` ${unit}` : ""} ({active.week.start_date})
          </span>
        ) : (
          <span>Hover points to inspect weekly values</span>
        )}
      </div>
    </div>
  );
}

export function EfficiencyAndCadenceChart({ weeks }: { weeks: WeekSummary[] }) {
  const recent = weeks.slice(-16).filter((w) => w.sessions > 0);
  if (recent.length < 2) return null;

  const effVals = recent.map((w) => w.aerobic_efficiency).filter((v): v is number => v !== null);
  const cadVals = recent.map((w) => w.avg_cadence).filter((v): v is number => v !== null);

  const effMin = effVals.length ? Math.min(...effVals) * 0.95 : 1;
  const effMax = effVals.length ? Math.max(...effVals) * 1.05 : 3;
  const cadMin = cadVals.length ? Math.min(...cadVals, 145) - 5 : 140;
  const cadMax = cadVals.length ? Math.max(...cadVals, 185) + 5 : 190;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.85rem" }}>
      <SparklineCard
        title="SWAP Aerobic Efficiency (GAP / HR)"
        subtitle="Higher = faster grade-adjusted pace at the same heart rate"
        weeks={recent}
        values={recent.map((w) => w.aerobic_efficiency)}
        minVal={effMin}
        maxVal={effMax}
        stroke="var(--accent-easy)"
        formatVal={(v) => v.toFixed(2)}
      />

      <SparklineCard
        title="Benzie Cadence Trend (spm)"
        subtitle="Shaded target elastic turnover band: 175–185 spm"
        weeks={recent}
        values={recent.map((w) => w.avg_cadence)}
        minVal={cadMin}
        maxVal={cadMax}
        stroke="var(--accent-tempo)"
        formatVal={(v) => v.toFixed(0)}
        unit="spm"
        targetBand={[175, 185]}
      />
    </div>
  );
}
