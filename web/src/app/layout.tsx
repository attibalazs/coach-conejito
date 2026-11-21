import type { Metadata } from "next";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Coach Conejito — Endurance & Trail Log",
  description: "AstroPaper-inspired running log powered by Albon Dual-Load, SWAP, Uphill Athlete, and Benzie biomechanics.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
