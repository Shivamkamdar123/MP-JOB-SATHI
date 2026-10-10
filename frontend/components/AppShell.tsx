"use client";

import Link from "next/link";
import {
  BriefcaseBusiness,
  ChartNoAxesColumnIncreasing,
  Languages,
} from "lucide-react";
import { useI18n } from "@/lib/i18n";
import type { Language } from "@/lib/api";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { language, setLanguage, t } = useI18n();
  const nextLanguage: Language = language === "en" ? "hi" : "en";
  return (
    <>
      <header className="site-header">
        <Link className="brand" href="/" aria-label={t("brand")}>
          <span className="brand-stamp">MP</span>
          <span>
            <strong>{t("brand")}</strong>
            <small>{t("tagline")}</small>
          </span>
        </Link>
        <nav className="top-nav" aria-label={t("service")}>
          <Link href="/">
            <BriefcaseBusiness size={16} aria-hidden="true" />
            {t("feed")}
          </Link>
          <Link href="/stats">
            <ChartNoAxesColumnIncreasing size={16} aria-hidden="true" />
            {t("stats")}
          </Link>
        </nav>
        <button
          className="language-toggle"
          type="button"
          onClick={() => setLanguage(nextLanguage)}
          aria-label={`${t("language")}: ${nextLanguage}`}
        >
          <Languages size={17} aria-hidden="true" />
          <span>{language === "en" ? "हिन्दी" : "English"}</span>
        </button>
      </header>
      {children}
    </>
  );
}
