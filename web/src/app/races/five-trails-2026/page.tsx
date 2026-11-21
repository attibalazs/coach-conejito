import Link from "next/link";
import React from "react";
import { RankProgressionChart } from "@/components/RaceCharts";

const SPLIT_ROWS = [
  {
    leg: "Trail 1",
    borbala: "01:03:52 (44th / 10th F)",
    attila: "01:03:58 (45th)",
    firstF: "00:51:29",
    winner: "00:47:37",
  },
  {
    leg: "Trail 2",
    borbala: "01:02:05 (24th= / 4th F)",
    attila: "01:02:05 (24th=)",
    firstF: "00:55:22",
    winner: "00:50:29",
  },
  {
    leg: "Trail 3",
    borbala: "01:01:15 (19th / 3rd F)",
    attila: "01:01:17 (20th)",
    firstF: "00:55:36",
    winner: "00:50:42",
  },
  {
    leg: "Trail 4",
    borbala: "01:14:03 (14th / 2nd F)",
    attila: "01:14:06 (15th)",
    firstF: "01:09:40",
    winner: "01:03:05",
  },
  {
    leg: "Trail 5 (Finish)",
    borbala: "01:12:43 (17th / 4th F)",
    attila: "01:12:55 (18th)",
    firstF: "01:06:53",
    winner: "00:57:12",
  },
];

const STREAM_SPLITS = [
  { seg: "00–05 km", elev: "+89 / -89m", pace: "6:10", gap: "6:07", hr: "128", eff: "2.13", cad: "161", note: "Easy Zone 2 cruise" },
  { seg: "05–10 km", elev: "+75 / -71m", pace: "5:54", gap: "5:53", hr: "135", eff: "2.09", cad: "161", note: "Smooth, controlled" },
  { seg: "10–15 km", elev: "+207 / -111m", pace: "6:52", gap: "6:28", hr: "141", eff: "1.83", cad: "150", note: "First big climb (hiking steep pitches)" },
  { seg: "15–20 km", elev: "+139 / -95m", pace: "6:38", gap: "6:25", hr: "138", eff: "1.88", cad: "158", note: "Settled in well" },
  { seg: "20–25 km", elev: "+119 / -128m", pace: "6:03", gap: "6:02", hr: "150", eff: "1.85", cad: "161", note: "Strong mid-race push" },
  { seg: "25–30 km", elev: "+122 / -151m", pace: "6:52", gap: "6:53", hr: "146", eff: "1.66", cad: "159", note: "1st dip (GAP +51s/km)" },
  { seg: "30–35 km", elev: "+90 / -121m", pace: "6:11", gap: "6:16", hr: "155", eff: "1.71", cad: "160", note: "Rallied; HR +20 bpm vs start" },
  { seg: "35–40 km", elev: "+177 / -88m", pace: "6:54", gap: "6:32", hr: "157", eff: "1.62", cad: "156", note: "Peak HR; engine ceiling felt" },
  { seg: "40–45 km", elev: "+120 / -243m", pace: "7:07", gap: "7:25", hr: "152", eff: "1.48", cad: "161", note: "Slippery clay descent + knee braking" },
  { seg: "45–50 km", elev: "+67 / -111m", pace: "6:33", gap: "6:38", hr: "151", eff: "1.66", cad: "160", note: "Strong final-5k recovery" },
  { seg: "50–51.2 km", elev: "+17 / -11m", pace: "6:55", gap: "6:45", hr: "155", eff: "1.59", cad: "161", note: "Finish push" },
];

export default function FiveTrailsRacePage() {
  return (
    <main className="container">
      <div style={{ marginBottom: "1rem", display: "flex", gap: "1rem", flexWrap: "wrap" }} className="mono">
        <Link href="/" style={{ fontSize: "0.85rem", color: "var(--muted)", textDecoration: "none" }}>
          ← Back to Training Log
        </Link>
        <Link href="/races/granite-peaks-2027" style={{ fontSize: "0.85rem", color: "var(--accent-easy)", textDecoration: "none" }}>
          Granite Peaks 2027 Prep →
        </Link>
        <Link href="/methodology" style={{ fontSize: "0.85rem", color: "var(--text)", textDecoration: "none" }}>
          Methodology &amp; Metrics Guide →
        </Link>
      </div>

      <header style={{ marginBottom: "1.75rem", borderBottom: "1px solid var(--border)", paddingBottom: "1.25rem" }}>
        <div style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted)" }} className="mono">
          Race Analysis · Freedom Racing · 2026-11-14 · Graffham, South Downs
        </div>
        <h1 style={{ margin: "0.35rem 0 0.4rem", fontSize: "2rem", letterSpacing: "-0.02em" }}>
          5 Trails 50k Ultra — Post-Race Debrief
        </h1>
        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.95rem" }}>
          51.16 km · +1,130 m / -1,130 m · Staggered start (08:48:25 / 08:48:27) · 108 finishers (116 starters) ·{" "}
          <a
            href="https://www.sportident.co.uk/results/FreedomRacing/2026/FiveTrailsUltra/"
            target="_blank"
            rel="noreferrer"
            style={{ color: "var(--accent-cardio)" }}
          >
            Official SPORTident Results
          </a>
        </p>
      </header>

      {/* Side-by-side Athlete Cards */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
        <div className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-cardio)", fontWeight: 700 }} className="mono">
            ATTILA BALAZS · MSEN · RUNNYMEDE RUNNERS
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, marginTop: "0.25rem" }} className="mono">
            05:34:21
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            <strong>22nd / 108</strong> overall (Top 20%) · <strong>18th</strong> Male · <strong>10th / 30</strong> MSEN
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.45rem" }} className="mono">
            Strava Streams: GAP 6:22/km · Impact 264.7 · Cardio 525.0 · Pa:HR Drift 16.97% (vs 2.6% 28d avg)
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-impact)", fontWeight: 700 }} className="mono">
            BORBALA HIDEGH · FV40 · RUNNYMEDE RUNNERS
          </div>
          <div style={{ fontSize: "1.75rem", fontWeight: 700, marginTop: "0.25rem" }} className="mono">
            05:33:58
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "0.25rem" }}>
            <strong>21st / 108</strong> overall · <strong>4th / 31</strong> Female (<strong>9s</strong> off 3rd F podium!)
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.45rem" }} className="mono">
            3rd F Lucy Williams: 05:33:49 · 1st F Katy Cherry: 04:59:00 (+34:58)
          </div>
        </div>
      </section>

      <section style={{ marginBottom: "1.25rem" }}>
        <RankProgressionChart />
      </section>

      {/* Checkpoint Splits Table */}
      <section className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1.1rem" }}>Checkpoint-by-Checkpoint Splits</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Leg</th>
                <th>Borbala Hidegh (Overall / F)</th>
                <th>Attila Balazs (Overall)</th>
                <th className="num">1st Female</th>
                <th className="num">Overall Winner</th>
              </tr>
            </thead>
            <tbody>
              {SPLIT_ROWS.map((r) => (
                <tr key={r.leg}>
                  <td><strong>{r.leg}</strong></td>
                  <td className="mono">{r.borbala}</td>
                  <td className="mono">{r.attila}</td>
                  <td className="num">{r.firstF}</td>
                  <td className="num">{r.winner}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5 km Strava Stream Breakdown */}
      <section className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 style={{ margin: "0 0 0.3rem", fontSize: "1.1rem" }}>5 km Stream Breakdown (GAP, HR &amp; Efficiency)</h2>
        <p style={{ margin: "0 0 0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          Course conditions: slippery clay mud on descents (especially 40–45 km, causing knee braking stress rather than quad fatigue) and engine ceiling felt from km 30–40 (HR 155–157 bpm).
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Segment</th>
                <th>Elev (+/-)</th>
                <th className="num">Pace</th>
                <th className="num">GAP</th>
                <th className="num">HR</th>
                <th className="num">Eff</th>
                <th className="num">Cad</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {STREAM_SPLITS.map((s) => (
                <tr key={s.seg}>
                  <td className="mono"><strong>{s.seg}</strong></td>
                  <td className="mono">{s.elev}</td>
                  <td className="num">{s.pace}</td>
                  <td className="num"><strong>{s.gap}</strong></td>
                  <td className="num">{s.hr}</td>
                  <td className="num">{s.eff}</td>
                  <td className="num">{s.cad}</td>
                  <td style={{ color: "var(--muted)" }}>{s.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Coaching Debrief: What Could Have Been Done Better */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: "1rem" }}>
        <div className="card">
          <h3 style={{ margin: "0 0 0.6rem", fontSize: "1.05rem", color: "var(--accent-cardio)" }}>
            Attila — What You Could Have Done Better
          </h3>
          <ul style={{ margin: 0, paddingLeft: "1.15rem", fontSize: "0.9rem" }}>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Trail 1 was overly conservative (45th at CP1):</strong> You ran <code>1:03:58</code> on Trail 1 and then ran <em>faster</em> on Trail 2 (<code>1:02:05</code>) and Trail 3 (<code>1:01:17</code>), passing 25 runners by CP4. Opening ~3 minutes quicker on Trail 1 (around 30th instead of 45th) keeps you in a faster pack without spiking HR (your avg HR was a very controlled 146 bpm).
            </li>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Late-race turnover on Trail 5 (20th → 22nd):</strong> After a stellar 15th-fastest split on Trail 4, you slipped 2 places on the final leg. Your last 28 days had <code>0.0%</code> hard/top-end work (SWAP &ldquo;bacon&rdquo;)—adding short strides and fast-finish long runs in the next block will sharpen fatigued leg speed.
            </li>
            <li>
              <strong>Descent cadence (154.5 spm avg):</strong> On runnable trails, keeping turnover quick (Benzie) reduces braking forces and saves quads for the final 10 km.
            </li>
          </ul>
        </div>

        <div className="card">
          <h3 style={{ margin: "0 0 0.6rem", fontSize: "1.05rem", color: "var(--accent-impact)" }}>
            Borbala — Race Context &amp; Takeaways
          </h3>
          <ul style={{ margin: 0, paddingLeft: "1.15rem", fontSize: "0.9rem" }}>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Podium-level fitness (5–10 min in reserve):</strong> Borbala felt great all day and waited for Attila multiple times—meaning her true solo ceiling on the day was around <strong>05:24–05:28</strong>, comfortably ahead of 3rd Female Lucy Williams (<code>05:33:49</code>).
            </li>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Staggered-start blind spot:</strong> Because of the staggered start (<code>08:48:27</code>), there was no way to know on the trail that she had climbed to <strong>3rd Female</strong> leaving CP4 (running the 2nd fastest female split on Trail 4 in <code>1:14:03</code>) and was only 9 seconds off the podium at the line.
            </li>
            <li>
              <strong>Next race takeaway:</strong> In staggered-start races, checking live splits at late checkpoints (or running her own effort from CP3 onward when targeting a podium) unlocks that extra 5–10 minutes.
            </li>
          </ul>
        </div>
      </section>

      {/* Pre-Race Build (90 / 60 / 30d) & Taper */}
      <section className="card" style={{ marginTop: "1.25rem", marginBottom: "1.25rem" }}>
        <h2 style={{ margin: "0 0 0.3rem", fontSize: "1.1rem" }}>
          Pre-Race Build &amp; Taper — Running Only vs. Cross-Training (90 / 60 / 30 Days → 2026-11-13)
        </h2>
        <p style={{ margin: "0 0 0.85rem", fontSize: "0.85rem", color: "var(--muted)" }}>
          Peak running week <strong>W39</strong> (61.9 km / +1,536m + 93.9 km cycling) → Last big week <strong>W44</strong> (47.6 km / +1,266m) → Taper <strong>W45</strong> (42.5 km / +445m, Efficiency +5.5% to 2.348) → Race Eve Dual TSB <strong>+10.2 (Impact) / +29.4 (Cardio)</strong>.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Metric (Running Only, except Cardio &amp; Cross-Training)</th>
                <th className="num">90 Days</th>
                <th className="num">60 Days</th>
                <th className="num">30 Days (incl. Taper)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Running Sessions</td>
                <td className="num">75</td>
                <td className="num">49</td>
                <td className="num">26</td>
              </tr>
              <tr>
                <td>Running Distance</td>
                <td className="num">615.3 km (~48/wk)</td>
                <td className="num">413.8 km (~48/wk)</td>
                <td className="num">203.9 km (~48/wk)</td>
              </tr>
              <tr>
                <td>Running Elevation Gain</td>
                <td className="num">+10,851 m (~844/wk)</td>
                <td className="num">+7,639 m (~891/wk)</td>
                <td className="num">+3,724 m</td>
              </tr>
              <tr>
                <td>Cross-Training (Cycling + Strength)</td>
                <td className="num">684.4 km (15) + 22 str</td>
                <td className="num">421.4 km (10) + 13 str</td>
                <td className="num">181.7 km (4) + 7 str</td>
              </tr>
              <tr>
                <td>Albon Impact (Run) / Cardio (All)</td>
                <td className="num">3,125 / 6,299 (0.50)</td>
                <td className="num">2,105 / 4,307 (0.49)</td>
                <td className="num">1,036 / 2,115 (0.49)</td>
              </tr>
              <tr>
                <td>Avg Running HR</td>
                <td className="num">126.1 bpm</td>
                <td className="num">126.7 bpm</td>
                <td className="num">128.2 bpm</td>
              </tr>
              <tr>
                <td>SWAP Running Polarization (E / T / H)</td>
                <td className="num">93.3% / 6.7% / 0.0%</td>
                <td className="num">89.8% / 10.2% / 0.0%</td>
                <td className="num">80.8% / 19.2% / 0.0%</td>
              </tr>
              <tr>
                <td>Running Aerobic Efficiency (GAP/HR)</td>
                <td className="num">2.251</td>
                <td className="num">2.247</td>
                <td className="num">2.240</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Next Goal: Granite Peaks 50km / +4,000m */}
      <section className="card">
        <div style={{ fontSize: "0.75rem", color: "var(--accent-easy)", fontWeight: 700 }} className="mono">
          NEXT TARGET · APRIL 2027 (~22 WEEKS OUT)
        </div>
        <h2 style={{ margin: "0.25rem 0 0.5rem", fontSize: "1.15rem" }}>
          Granite Peaks 50 km / +4,000 m — 5 Training Adjustments
        </h2>
        <p style={{ margin: "0 0 0.85rem", fontSize: "0.88rem", color: "var(--muted)" }}>
          5 Trails was <strong>22 m/km</strong> of climbing (+1,130 m). Granite Peaks is <strong>80 m/km</strong> (+4,000 m) — 3.5× the vertical density (7–9+ hours). Your cycling + 22 strength sessions gave you a huge Cardio CTL (63.3) on ~48 km/wk of running, but Granite Peaks demands much more <em>running-specific</em> vertical &amp; eccentric leg load.
        </p>
        <ol style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.9rem" }}>
          <li style={{ marginBottom: "0.5rem" }}>
            <strong>3× your running vertical (~844 m/wk → 2,500–3,500 m/wk):</strong> Peak running week W39 was +1,536 m. For a +4,000 m race, build 4–6 weeks in Feb–Mar 2027 at 2,500–3,500 m+/wk of running vert (even if running volume only rises to 60–75 km/wk), focusing on steep climbs and power-hiking efficiency.
          </li>
          <li style={{ marginBottom: "0.5rem" }}>
            <strong>Knee stability &amp; downhill footwork (Albon Impact CTL 31.9 → 45–50+):</strong> Slippery clay descents shifted braking load to your knees. Pair progressive downhill volume with single-leg knee/ankle stability (slow eccentric step-downs, split squats) and technical descent practice.
          </li>
          <li style={{ marginBottom: "0.5rem" }}>
            <strong>Add SWAP &ldquo;Bacon&rdquo; + uphill threshold (0.0% → 5–8% Hard):</strong> Keep your ~90% easy running base and 2-week taper, but add 1×/wk short steep hill sprints (8–10 × 12s) + 1×/wk uphill tempo/threshold (4 × 6 min steep climb).
          </li>
          <li style={{ marginBottom: "0.5rem" }}>
            <strong>Separate hiking vs. running cadence (Benzie):</strong> Cue 175–185 spm light turnover on runnable flats/descents; keep rhythmic pole/power-hike cadence on steep pitches.
          </li>
          <li>
            <strong>Practice 75–90+ g/hr carb fueling:</strong> Track gut-training carbs/hr via <code>coach journal add</code> on Feb–Mar long mountain days.
          </li>
        </ol>
      </section>
    </main>
  );
}
