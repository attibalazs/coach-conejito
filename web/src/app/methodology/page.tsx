import Link from "next/link";
import React from "react";

const ACRONYMS = [
  { term: "CTL", full: "Chronic Training Load", meaning: "42-day exponential rolling average — your long-term fitness & durability base." },
  { term: "ATL", full: "Acute Training Load", meaning: "7-day exponential rolling average — your short-term fatigue from the past week." },
  { term: "TSB", full: "Training Stress Balance", meaning: "CTL − ATL (Freshness / Form). +10 to +30 = tapered; -10 to -25 = productive build; < -30 = heavy fatigue." },
  { term: "GAP", full: "Grade-Adjusted Pace", meaning: "Equivalent flat-ground pace after adjusting for uphill/downhill steepness via Minetti's energy cost curve." },
  { term: "Pa:HR", full: "Pace-to-Heart-Rate Decoupling", meaning: "Aerobic drift % comparing 1st-half vs. 2nd-half GAP/HR efficiency. < 5% = strong aerobic base." },
  { term: "ACWR", full: "Acute:Chronic Workload Ratio", meaning: "7-day load ÷ 28-day average. 0.8–1.3 = safe progression; > 1.5 = injury spike risk; < 0.8 = recovery/taper." },
  { term: "TRIMP", full: "Training Impulse", meaning: "Banister heart-rate load score: duration × HR reserve × exponential intensity factor." },
  { term: "RHR", full: "Resting Heart Rate", meaning: "Lowest overnight/resting heart rate. A +5–10 bpm spike signals incomplete recovery or illness." },
  { term: "SWAP", full: "Some Work, All Play", meaning: "David & Megan Roche's coaching philosophy: polarized easy base + threshold + short strides + joy/N=1." },
  { term: "BPM", full: "Beats Per Minute", meaning: "Heart rate measurement unit." },
  { term: "SPM", full: "Steps Per Minute", meaning: "Running cadence (total steps across both feet). Flat running sweet spot: 175–185 spm." },
  { term: "GCT", full: "Ground Contact Time", meaning: "Milliseconds your foot spends on the ground per step. Crisp elastic recoil target: < 240 ms." },
];

export default function MethodologyPage() {
  return (
    <main className="article-shell">
      <header className="hero">
        <p className="hero-kicker mono">Coach Conejito · Science, Principles &amp; Glossary</p>
        <h1>Training Methodology &amp; Metrics Guide</h1>
        <p className="hero-sub">
          Every concept, formula, coaching principle, and acronym we use to monitor running load, aerobic durability, biomechanics, and race readiness.
        </p>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem" }}>
          <a href="#acronyms" className="badge mono">Acronyms A–Z</a>
          <a href="#albon" className="badge mono">1. Albon 3-Pillar</a>
          <a href="#ctl-atl-tsb" className="badge mono">2. CTL / ATL / TSB</a>
          <a href="#swap" className="badge mono">3. SWAP</a>
          <a href="#uphill-athlete" className="badge mono">4. Uphill Athlete</a>
          <a href="#benzie" className="badge mono">5. Benzie</a>
          <a href="#risk" className="badge mono">6. ACWR &amp; Foster</a>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {/* Acronyms Cheat Sheet */}
        <section id="acronyms" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent)", fontWeight: 700 }} className="mono">
            QUICK REFERENCE
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.75rem", fontSize: "1.35rem" }}>
            Acronyms &amp; Terms Used in Your Log
          </h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Acronym</th>
                  <th>Full Name</th>
                  <th>What It Means in Practice</th>
                </tr>
              </thead>
              <tbody>
                {ACRONYMS.map((a) => (
                  <tr key={a.term}>
                    <td className="mono"><strong>{a.term}</strong></td>
                    <td><strong>{a.full}</strong></td>
                    <td style={{ color: "var(--muted)" }}>{a.meaning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 1. Albon 3-Pillar */}
        <section id="albon" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-impact)", fontWeight: 700 }} className="mono">
            1. ALBON / ASCEND — 3-PILLAR LOAD MODEL
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            Separating Leg Impact, Cardio Engine &amp; Speed
          </h2>
          <p style={{ margin: "0 0 0.75rem", fontSize: "0.94rem" }}>
            Traditional platforms combine everything into a single stress score, hiding whether your <em>muscles/joints</em> or your <em>heart/lungs</em> are fatigued. Jon Albon&apos;s Ascend framework splits load into three independent dimensions:
          </p>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.92rem" }}>
            <li style={{ marginBottom: "0.55rem" }}>
              <strong>Mechanical Impact Score (Running Only):</strong> <code>duration × speed^1.15 × terrain_factor</code> across your GPS/grade stream—<strong>heart rate is ignored</strong>. Downhills amplify eccentric pounding (<code>-10%</code> grade = <code>1.45×</code> impact), uphills reduce ground shock (<code>+10%</code> = <code>0.85×</code>), and cycling/strength add <code>0</code> running impact.
            </li>
            <li style={{ marginBottom: "0.55rem" }}>
              <strong>Cardio Score (Banister TRIMP — All Cardio):</strong> <code>duration_min × HR_reserve × 0.64 × e^(1.92 × HR_reserve)</code> across both running and cycling. Captures true cardiovascular/metabolic stress regardless of terrain.
            </li>
            <li style={{ marginBottom: "0.55rem" }}>
              <strong>Speed Score (GAP vs. Threshold):</strong> <code>duration_min × (threshold_pace / GAP)²</code> (default threshold <code>4:30/km</code>), measuring neuromuscular speed exposure independently of HR.
            </li>
            <li>
              <strong>Impact : Cardio Ratio:</strong> <code>&gt; 1.1</code> = leg-heavy (steep descents or fast flat running); <code>0.8–1.0</code> = balanced running; <code>&lt; 0.7</code> = engine-heavy (cycling cross-training, steep climbs, or heat).
            </li>
          </ul>
        </section>

        {/* 2. Dual CTL / ATL / TSB */}
        <section id="ctl-atl-tsb" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-cardio)", fontWeight: 700 }} className="mono">
            2. COGGAN / BANISTER — FITNESS, FATIGUE &amp; FORM
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            Tracking CTL, ATL &amp; TSB Across All 3 Pillars
          </h2>
          <p style={{ margin: "0 0 0.75rem", fontSize: "0.92rem", color: "var(--muted)" }}>
            By computing CTL, ATL, and TSB separately for Impact, Cardio, and Speed, you can spot when your legs are fresh (Impact TSB +10) even if your engine is tired (Cardio TSB -20)—or vice versa.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Formula / Window</th>
                  <th>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="mono"><strong>CTL</strong></td>
                  <td className="mono">42-day EMA</td>
                  <td>Long-term fitness &amp; tissue resilience built over 6+ weeks.</td>
                </tr>
                <tr>
                  <td className="mono"><strong>ATL</strong></td>
                  <td className="mono">7-day EMA</td>
                  <td>Short-term fatigue accumulated over the past week.</td>
                </tr>
                <tr>
                  <td className="mono"><strong>TSB</strong></td>
                  <td className="mono">CTL − ATL</td>
                  <td><code>-10 to -25</code> = productive training; <code>&lt; -30</code> = overreaching risk; <code>+10 to +30</code> = tapered &amp; race-ready.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* 3. SWAP */}
        <section id="swap" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-easy)", fontWeight: 700 }} className="mono">
            3. SWAP (DAVID &amp; MEGAN ROCHE) — ECONOMY &amp; POLARIZATION
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            The &ldquo;Big Salad&rdquo; &amp; Running Economy
          </h2>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.92rem" }}>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Stream-Based Polarization:</strong> Computed second-by-second from your HR stream (not whole-run average HR, which hides short hill sprints/strides): <strong>Easy</strong> (<code>&lt;140 bpm</code>, &ldquo;greens&rdquo;, target ~80%), <strong>Tempo</strong> (<code>140–159 bpm</code>, &ldquo;dressing&rdquo;, ~10–15%), and <strong>Hard</strong> (<code>160+ bpm</code>, &ldquo;bacon&rdquo;, ~5–8%). Avoid letting easy days drift into the 140–155 bpm gray zone.
            </li>
            <li style={{ marginBottom: "0.5rem" }}>
              <strong>Grade-Adjusted Pace (GAP):</strong> Estimates your flat-ground equivalent pace using Minetti&apos;s metabolic cost polynomial.
            </li>
            <li>
              <strong>Aerobic Efficiency (GAP / HR):</strong> <code>(GAP speed m/s ÷ avg HR) × 100</code>. Rising efficiency over weeks means faster paces at the same cardiovascular cost.
            </li>
          </ul>
        </section>

        {/* 4. Uphill Athlete */}
        <section id="uphill-athlete" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-tempo)", fontWeight: 700 }} className="mono">
            4. UPHILL ATHLETE (SCOTT JOHNSTON &amp; STEVE HOUSE)
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            Aerobic Decoupling (Pa:HR Drift %) &amp; Mountain Durability
          </h2>
          <p style={{ margin: "0 0 0.6rem", fontSize: "0.92rem" }}>
            Compares your <code>GAP / HR</code> efficiency in the <strong>first half</strong> vs. <strong>second half</strong> of a steady run (skipping the first 5 minutes as warmup):
          </p>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.92rem" }}>
            <li><strong>&lt; 5% drift:</strong> Strong aerobic base and durability at that duration.</li>
            <li><strong>5–10% drift:</strong> Moderate cardiac drift (normal as duration pushes your current limit).</li>
            <li><strong>&gt; 10% drift:</strong> Significant decoupling—signals late-race muscular fatigue, dehydration, or under-fueling (e.g., 16.97% over 5.5 hours at 5 Trails 50k).</li>
          </ul>
        </section>

        {/* 5. Shane Benzie */}
        <section id="benzie" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 700 }} className="mono">
            5. SHANE BENZIE (RUNNING REBORN) — ELASTIC BIOMECHANICS
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            Cadence, Ground Contact Time &amp; Vertical Oscillation
          </h2>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.92rem" }}>
            <li style={{ marginBottom: "0.45rem" }}>
              <strong>Cadence (175–185 spm on flat running):</strong> Eliminates overstriding and heel braking so your foot lands under your center of mass. *(Steep trail hiking naturally lowers whole-run cadence.)*
            </li>
            <li style={{ marginBottom: "0.45rem" }}>
              <strong>Ground Contact Time (&lt; 240 ms):</strong> Measures reactive elasticity—using the ground like a spring rather than collapsing into it.
            </li>
            <li>
              <strong>Vertical Oscillation (~7.5 cm):</strong> Controlled upward bounce so energy propels you forward rather than straight up.
            </li>
          </ul>
        </section>

        {/* 6. ACWR & Foster */}
        <section id="risk" className="card">
          <div style={{ fontSize: "0.75rem", color: "var(--accent-hard)", fontWeight: 700 }} className="mono">
            6. GABBETT (ACWR) &amp; FOSTER (MONOTONY / STRAIN)
          </div>
          <h2 className="serif" style={{ margin: "0.25rem 0 0.6rem", fontSize: "1.35rem" }}>
            Injury Risk &amp; Load Variability
          </h2>
          <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.92rem" }}>
            <li style={{ marginBottom: "0.45rem" }}>
              <strong>ACWR (Acute:Chronic Workload Ratio):</strong> 7-day load ÷ 28-day weekly average. <code>0.8–1.3</code> is the safe progressive zone; <code>&gt; 1.5</code> flags a dangerous volume spike; <code>&lt; 0.8</code> appears during intentional tapers or post-race recovery weeks.
            </li>
            <li>
              <strong>Foster Monotony &amp; Strain:</strong> <code>Monotony = mean daily load ÷ std dev</code> over 7 days. Keeping monotony <code>&lt; 1.5</code> (alternating hard, easy, and rest days) prevents repetitive overuse injury.
            </li>
          </ul>
        </section>

        <div style={{ paddingTop: "0.5rem" }} className="mono">
          <Link href="/">← Back to Training Log</Link>
        </div>
      </div>
    </main>
  );
}
