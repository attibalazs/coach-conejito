"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useState } from "react";

export function SiteHeader() {
  const pathname = usePathname();
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("conejito-theme") : null;
    if (saved === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      setDark(true);
    }
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    if (next) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("conejito-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("conejito-theme", "light");
    }
  };

  const navItems = [
    { href: "/", label: "Training Log" },
    { href: "/races/five-trails-2026", label: "5 Trails 50k" },
    { href: "/races/granite-peaks-2027", label: "Granite Peaks" },
    { href: "/methodology", label: "Methodology" },
  ];

  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="brand">
          <span className="brand-title">Coach Conejito</span>
          <span className="brand-tag">Endurance Log</span>
        </Link>

        <nav className="header-actions">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link${pathname === item.href ? " active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
          <button type="button" className="theme-btn" onClick={toggleTheme}>
            {dark ? "☀ Light" : "☾ Dark"}
          </button>
        </nav>
      </div>
    </header>
  );
}
