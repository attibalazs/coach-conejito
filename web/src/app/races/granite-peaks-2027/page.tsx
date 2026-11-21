import Link from "next/link";
import React from "react";

const TOP_VERT_RUNS = [
  {
    date: "2026-07-16",
    location: "Selva di Val Gardena (Dolomites)",
    dist: "21.1 km",
    vert: "+1,935 m",
    density: "92 m/km",
    time: "5h 23m",
    ekm: "40.4",
    paceEkm: "8:00/ekm",
    hr: "112",
  },
  {
    date: "2026-07-17",
    location: "Selva di Val Gardena (back-to-back)",
    dist: "22.0 km",
    vert: "+1,565 m",
    density: "71 m/km",
    time: "4h 52m",
    ekm: "37.6",
    paceEkm: "7:46/ekm",
    hr: "111",
  },
  {
    date: "2025-11-28",
    location: "Tejeda Trail (Gran Canaria)",
    dist: "29.5 km",
    vert: "+1,553 m",
    density: "53 m/km",
    time: "5h 32m",
    ekm: "45.1",
    paceEkm: "7:22/ekm",
    hr: "114",
  },
  {
    date: "2025-11-27",
    location: "San Bartolomé (Gran Canaria, b2b)",
    dist: "25.2 km",
    vert: "+1,542 m",
    density: "61 m/km",
    time: "5h 15m",
    ekm: "40.6",
    paceEkm: "7:45/ekm",
    hr: "113",
  },
  {
    date: "2026-07-13",
    location: "Selva di Val Gardena (Dolomites)",
    dist: "20.1 km",
    vert: "+1,425 m",
    density: "71 m/km",
    time: "4h 10m",
    ekm: "34.4",
    paceEkm: "7:16/ekm",
    hr: "119",
  },
];

export default function GranitePeaksPage() {
  return (
    <main className="container">
      <div style={{ marginBottom: "1rem", display: "flex", gap: "1rem", flexWrap: "wrap" }} className="mono">
        <Link href="/" style={{ fontSize: "0.85rem", color: "var(--muted)", textDecoration: "none" }}>
          ← Back to Training Log
        </Link>
        <Link href="/races/five-trails-2026" style={{ fontSize: "0.85rem", color: "var(--accent-cardio)", textDecoration: "none" }}>
          5 Trails 50k Debrief →
        </Link>
        <Link href="/methodology" style={{ fontSize: "0.85rem", color: "var(--text)", textDecoration: "none" }}>
          Methodology Guide →
        </Link>
      </div>

      <header style={{ marginBottom: "1.75rem", borderBottom: "1px solid var(--border)", paddingBottom: "1.25rem" }}>
        <div style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent-easy)", fontWeight: 700 }} className="mono">
          Next Target · April 2027 · Sub-12h Goal
        </div>
        <h1 style={{ margin: "0.35rem 0 0.4rem", fontSize: "2rem", letterSpacing: "-0.02em" }}>
          Granite Peaks 50 km / +4,000 m — Race Projection &amp; Prep
        </h1>
        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.95rem" }}>
          90.0 Effort-km (50 km + 4,000 m vert) · 80 m/km vertical density (3.5× steeper than 5 Trails 50k)
        </p>
      </header>

      {/* Finish Time Projections (with Positive-Split & GAP Drift) */}
      <section className="grid-metrics" style={{ marginBottom: "1.25rem" }}>
        <div className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-easy)", fontWeight: 700 }} className="mono">
            STRONG DAY (+12–15% DRIFT)
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.2rem" }} className="mono">
            10h 35m – 10h 55m
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }} className="mono">
            1st half 6:30/ekm → 2nd half 7:29/ekm + 20m aid
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-cardio)", fontWeight: 700 }} className="mono">
            REALISTIC (+18–20% DRIFT)
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.2rem" }} className="mono">
            11h 05m – 11h 35m
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }} className="mono">
            1st half 6:45/ekm → 2nd half 8:00/ekm + 20m aid
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-tempo)", fontWeight: 700 }} className="mono">
            HEAVY FADE (+25% DRIFT)
          </div>
          <div style={{ fontSize: "1.55rem", fontWeight: 700, marginTop: "0.2rem" }} className="mono">
            11h 45m – 12h 10m
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }} className="mono">
            1st half 7:00/ekm → 2nd half 8:45/ekm + 25m aid
          </div>
        </div>
      </section>

      {/* Positive-Split & GAP Drift Breakdown */}
      <section className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 style={{ margin: "0 0 0.3rem", fontSize: "1.1rem" }}>
          Positive-Split &amp; GAP Drift Model (90.0 Effort-km)
        </h2>
        <p style={{ margin: "0 0 0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          Calibrated from your 5 Trails 50k stream data, where 2nd-half GAP slowed <strong>+8.6%</strong> (<code>6:11/km</code> → <code>6:43/km</code>) over 5.5 hours. Over 10–12 hours at +4,000 m, expect <strong>+12% to +25%</strong> positive-split drift.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th className="num">1st Half (45 ekm)</th>
                <th className="num">2nd-Half Drift</th>
                <th className="num">2nd Half (45 ekm)</th>
                <th className="num">Aid Stops</th>
                <th className="num">Projected Finish</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Strong Day</strong></td>
                <td className="num">4h 52m (6:30/ekm)</td>
                <td className="num">+15%</td>
                <td className="num">5h 37m (7:29/ekm)</td>
                <td className="num">20m</td>
                <td className="num"><strong>10h 49m</strong></td>
              </tr>
              <tr>
                <td><strong>Realistic</strong></td>
                <td className="num">5h 04m (6:45/ekm)</td>
                <td className="num">+18%</td>
                <td className="num">5h 59m (7:58/ekm)</td>
                <td className="num">20m</td>
                <td className="num"><strong>11h 23m</strong></td>
              </tr>
              <tr>
                <td><strong>Heavy Fade</strong></td>
                <td className="num">5h 15m (7:00/ekm)</td>
                <td className="num">+25%</td>
                <td className="num">6h 34m (8:45/ekm)</td>
                <td className="num">25m</td>
                <td className="num"><strong>12h 14m</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Top 5 Highest-Elevation Runs */}
      <section className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 style={{ margin: "0 0 0.3rem", fontSize: "1.1rem" }}>
          Top 5 Highest-Elevation 20 km+ Runs (Past 12 Months)
        </h2>
        <p style={{ margin: "0 0 0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          Effort-km = <code>distance_km + elevation_gain_m / 100</code>. Your Dolomites &amp; Gran Canaria blocks match Granite Peaks&apos; steepness (<code>71–92 m/km</code>) at just <code>111–119 bpm</code> avg HR.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Location / Run</th>
                <th className="num">Dist</th>
                <th className="num">Vert+</th>
                <th className="num">Density</th>
                <th className="num">Time</th>
                <th className="num">Effort-km</th>
                <th className="num">Pace/ekm</th>
                <th className="num">Avg HR</th>
              </tr>
            </thead>
            <tbody>
              {TOP_VERT_RUNS.map((r) => (
                <tr key={r.date}>
                  <td className="mono">{r.date}</td>
                  <td><strong>{r.location}</strong></td>
                  <td className="num">{r.dist}</td>
                  <td className="num"><strong>{r.vert}</strong></td>
                  <td className="num">{r.density}</td>
                  <td className="num">{r.time}</td>
                  <td className="num">{r.ekm}</td>
                  <td className="num">{r.paceEkm}</td>
                  <td className="num">{r.hr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cutoff & Sub-12h Blueprint */}
      <section className="card">
        <h2 style={{ margin: "0 0 0.6rem", fontSize: "1.15rem" }}>
          4-Point Blueprint to Beat Cutoffs &amp; Guarantee Sub-12 Hours
        </h2>
        <ol style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.9rem" }}>
          <li style={{ marginBottom: "0.6rem" }}>
            <strong>Protect your uphill engine (600–800 m/hr climbing rate):</strong> At +4,000 m, climbing efficiency decides cutoffs. Add <strong>1×/wk sustained uphill threshold</strong> (<code>4 × 6 min</code> or <code>3 × 10 min</code> steep climb at 145–155 bpm) + <strong>1×/wk short steep hill sprints</strong> (<code>8–10 × 12s</code>) to raise vertical speed without spiking HR.
          </li>
          <li style={{ marginBottom: "0.6rem" }}>
            <strong>Keep easy days truly easy (53% → 80% &lt;140 bpm):</strong> Your 30d pre-5-Trails build had 40.1% gray-zone Tempo (140–159 bpm). Polarizing easy days below 140 bpm lets you push harder on climb days and reduces late-race cardiac drift (16.97% at 5 Trails).
          </li>
          <li style={{ marginBottom: "0.6rem" }}>
            <strong>Simulate back-to-back vertical &amp; knee stability (Feb–Mar 2027):</strong> Replicate your Dolomites (+3,500 m over 2 days) and Gran Canaria (+3,095 m over 2 days) weekends. Target <strong>4–6 peak weeks at 2,500–3,500 m/wk running vert</strong> and <strong>Running Impact CTL 45–50+</strong>, paired with single-leg knee/ankle strength (step-downs, split squats) for 4,000 m of descending.
          </li>
          <li>
            <strong>Aid-station discipline &amp; 75–90 g/hr carb fueling:</strong> Keep aid-station stops under 2–3 minutes (saving 30–40 min over a 10–11h day) and practice 75–90 g/hr carb intake on 4–5h mountain prep runs logged via <code>coach journal add</code>.
          </li>
        </ol>
      </section>
    </main>
  );
}
