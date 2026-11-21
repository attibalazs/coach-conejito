"use client";

import React from "react";

interface SplitPoint {
  label: string;
  attilaRank: number;
  borbalaRank: number;
  borbalaFemaleRank: number;
}

const SPLITS: SplitPoint[] = [
  { label: "Trail 1", attilaRank: 45, borbalaRank: 44, borbalaFemaleRank: 10 },
  { label: "Trail 2", attilaRank: 31, borbalaRank: 30, borbalaFemaleRank: 7 },
  { label: "Trail 3", attilaRank: 25, borbalaRank: 24, borbalaFemaleRank: 5 },
  { label: "Trail 4", attilaRank: 20, borbalaRank: 19, borbalaFemaleRank: 3 },
  { label: "Finish", attilaRank: 22, borbalaRank: 21, borbalaFemaleRank: 4 },
];

export function RankProgressionChart() {
  const width = 760;
  const height = 210;
  const padL = 44;
  const padR = 28;
  const padT = 20;
  const padB = 32;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const maxRank = 50;

  const toX = (i: number) => padL + (i / (SPLITS.length - 1)) * plotW;
  const toY = (rank: number) => padT + ((rank - 1) / (maxRank - 1)) * plotH;

  const attilaPts = SPLITS.map((s, i) => `${toX(i).toFixed(1)},${toY(s.attilaRank).toFixed(1)}`).join(" ");
  const borbalaPts = SPLITS.map((s, i) => `${toX(i).toFixed(1)},${toY(s.borbalaRank).toFixed(1)}`).join(" ");

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.6rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem" }}>Overall Position Progression (Trail 1 → Finish)</h3>
          <p style={{ margin: "0.15rem 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>
            Higher = better overall rank (out of 108 finishers) · Both runners passed 23 runners after CP1
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.9rem", fontSize: "0.78rem" }}>
          <span><span style={{ display: "inline-block", width: 10, height: 10, background: "var(--accent-cardio)", borderRadius: 2, marginRight: 5 }} />Attila (45th → 22nd)</span>
          <span><span style={{ display: "inline-block", width: 10, height: 10, background: "var(--accent-impact)", borderRadius: 2, marginRight: 5 }} />Borbala (44th → 21st)</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", overflow: "visible" }}>
        {[1, 15, 30, 45].map((r) => {
          const y = toY(r);
          return (
            <g key={r}>
              <line x1={padL} x2={width - padR} y1={y} y2={y} stroke="var(--border)" strokeDasharray="3 3" />
              <text x={padL - 8} y={y + 4} textAnchor="end" fontSize="10" fill="var(--muted)" className="mono">
                #{r}
              </text>
            </g>
          );
        })}

        <polyline fill="none" stroke="var(--accent-cardio)" strokeWidth="2.5" points={attilaPts} />
        <polyline fill="none" stroke="var(--accent-impact)" strokeWidth="2.5" strokeDasharray="5 3" points={borbalaPts} />

        {SPLITS.map((s, i) => {
          const x = toX(i);
          return (
            <g key={s.label}>
              <circle cx={x} cy={toY(s.attilaRank)} r={4.5} fill="var(--accent-cardio)" />
              <circle cx={x} cy={toY(s.borbalaRank)} r={4.5} fill="var(--accent-impact)" />
              <text x={x} y={toY(s.borbalaRank) - 9} textAnchor="middle" fontSize="10" fill="var(--text)" className="mono">
                {s.borbalaRank}/{s.attilaRank}
              </text>
              <text x={x} y={height - 8} textAnchor="middle" fontSize="11" fill="var(--muted)" className="mono">
                {s.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
