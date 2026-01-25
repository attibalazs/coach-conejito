# Tech Stack Comparison: Coach Conejito

**Goal:** Determine the "easiest" and most effective stack to build the personal AI coach, considering user familiarity (Flutter/Python) vs. project requirements (Data Ingestion, AI, Local Filesystem).

## 1. Python (Streamlit or FastAPI + HTMX)
*Recommended for: Speed of implementation & Data processing power.*

### Pros
- **Familiarity:** You are already comfortable with Python.
- **Data & AI:** Python is the native language of AI and data. Libraries like `fitparse` (for Garmin .FIT files) and `pandas` (for data aggregation) are mature and robust.
- **Speed (Streamlit):** You can build the Dashboard, Journal input, and Charts purely in Python without writing a single line of HTML or CSS.
- **Backend Logic:** Writing scripts to fetch Strava data and cron jobs is trivial in Python.

### Cons
- **Mobile Experience:** Streamlit is mobile-responsive but feels like a website, not a native app. It cannot be easily "installed" as a PWA with offline capabilities.
- **Interactivity:** Streamlit re-runs the script on every interaction, which can feel "laggy" compared to a React/Flutter app for complex UIs.

### Verdict
**Easiest Path.** If you want to get the logic working and see graphs *today*, this is it. The UI won't be "app-store quality" but it will be functional immediately.

---

## 2. Flutter
*Recommended for: Mobile User Experience.*

### Pros
- **Familiarity:** You know it well.
- **Mobile First:** Will deliver the best "Coach in your pocket" experience.
- **Cross-Platform:** Runs on MacOS (desktop) for the heavy data lifting and Mobile for viewing/journaling.

### Cons
- **File System complexity:** The architecture relies on "Local Filesystem" (JSON/MD files).
    - On **Mobile**, apps are sandboxed. You cannot easily just read/write to a shared folder where you dumped a Garmin file.
    - On **Web**, you have no file system access.
    - You would likely need to build a **Desktop** version for the "Server/Data Ingestion" part and a **Mobile** version for the UI, or build a separate backend.
- **Library Ecosystem:** Parsing binary `.FIT` or `.TCX` files in Dart has fewer library options than Python/Node.
- **OAuth:** Handling OAuth redirects (Strava) on mobile requires deep-linking configuration, which is more complex than a simple web callback.

### Verdict
**Hardest Path for this specific architecture.** While the UI would be great, the "backend" logic (parsing files, cron jobs, file I/O) fights against the grain of a typical client-side mobile app.

---

## 3. Next.js (React)
*Recommended for: The "Balanced" Web App (PWA).*

### Pros
- **Architecture Fit:** The current `architecture.md` was designed for this. Node.js (Server Components) handles the File System and API calls securely.
- **PWA:** Can be installed on mobile (Add to Home Screen) and looks 90% like a native app.
- **Vercel AI SDK:** Excellent integration with Gemini (streaming responses, easy state management).
- **One Codebase:** Frontend and Backend logic live in the same project.

### Cons
- **Learning Curve:** If you don't know React/TypeScript well, there is friction.
- **Boilerplate:** More setup code than a simple Python script.

### Verdict
**Best "Product" Path.** If you are willing to lean on AI to help write the React code, this delivers the best balance of a "real app" feel with the backend capabilities needed for file processing.

---

## Summary Recommendation

1.  **If you want the "Easiest" implementation:**
    **Go with Python (Streamlit).**
    - You can write the `ingest_strava.py` and `parse_garmin.py` logic easily.
    - The UI is just a layer on top of your scripts.
    - **Trade-off:** UI is basic, strictly web-based.

2.  **If you want the best "App":**
    **Go with Next.js (PWA).**
    - It handles the server-side logic (files, secrets) while giving a mobile-app feel.
    - **Trade-off:** You have to write JavaScript/TypeScript.

3.  **Avoid Flutter** for *this specific local-filesystem architecture* unless you plan to build a separate Python backend API to serve the Flutter app.
