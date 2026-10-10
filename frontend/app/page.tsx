"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ArrowUpRight,
  Bookmark,
  CalendarDays,
  CircleAlert,
  RefreshCw,
  WifiOff,
} from "lucide-react";
import {
  ApiError,
  formatCurrency,
  formatDate,
  getFeed,
  getFee,
  getLocalProfile,
  getSavedJobs,
  saveJobOffline,
  getNotification,
  type FeedItem,
  type FeeBreakdown,
  type Profile,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { StatusBadge, VerificationBadge } from "@/components/ui";

export default function HomePage() {
  const { language, t } = useI18n();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [items, setItems] = useState<FeedItem[]>([]);
  const [fees, setFees] = useState<Record<number, FeeBreakdown>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savedIds, setSavedIds] = useState<number[]>([]);
  const savedJobs = Object.values(getSavedJobs());

  const loadFeed = useCallback(
    async (activeProfile: Profile) => {
      setLoading(true);
      setError("");
      try {
        const result = await getFeed(activeProfile);
        setItems(result.items);
        const feePairs = await Promise.all(
          result.items.map(async (item) => {
            try {
              return [
                item.id,
                await getFee(item.id, activeProfile.category),
              ] as const;
            } catch {
              return [item.id, null] as const;
            }
          }),
        );
        setFees(
          Object.fromEntries(
            feePairs.filter(
              (pair): pair is readonly [number, FeeBreakdown] =>
                pair[1] !== null,
            ),
          ),
        );
      } catch (cause) {
        setError(cause instanceof ApiError ? cause.message : t("loadError"));
      } finally {
        setLoading(false);
      }
    },
    [t],
  );

  useEffect(() => {
    const savedProfile = getLocalProfile();
    setProfile(savedProfile);
    setSavedIds(Object.keys(getSavedJobs()).map(Number));
    if (savedProfile) void loadFeed(savedProfile);
    else setLoading(false);
  }, [loadFeed]);

  if (!profile)
    return (
      <main className="welcome-band">
        <div className="welcome-copy">
          <p className="eyebrow">{t("brand")}</p>
          <h1>{t("tagline")}</h1>
          <p>{t("noProfile")}</p>
          <Link className="button button-primary" href="/onboarding">
            {t("start")} <ArrowUpRight size={17} aria-hidden="true" />
          </Link>
        </div>
        <div className="welcome-mark" aria-hidden="true">
          <span>MP</span>
          <i>01</i>
        </div>
      </main>
    );

  const groups: Array<{ status: FeedItem["status"]; label: string }> = [
    { status: "eligible", label: t("eligible") },
    { status: "likely", label: t("likely") },
    { status: "needs_check", label: t("needs_check") },
    { status: "not_eligible", label: t("not_eligible") },
  ];

  return (
    <main className="page-wrap feed-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{t("brand")}</p>
          <h1>{t("feed")}</h1>
        </div>
        <button
          className="icon-button"
          type="button"
          onClick={() => void loadFeed(profile)}
          aria-label={t("retry")}
          title={t("retry")}
        >
          <RefreshCw size={18} />
        </button>
      </div>
      <div className="feed-meta">
        <span>{profile.name}</span>
        <span>{profile.category}</span>
        <span>{profile.preferred_districts.join(" · ")}</span>
      </div>
      {loading && (
        <p className="state-message" role="status">
          {t("loading")}
        </p>
      )}
      {!loading && error && (
        <>
          <div className="state-message error-state" role="alert">
            <WifiOff size={18} />
            {error}
            <button
              className="text-button"
              onClick={() => void loadFeed(profile)}
            >
              {t("retry")}
            </button>
          </div>
          {savedJobs.length > 0 && (
            <section className="offline-saved" aria-label={t("saved")}>
              <h2>{t("saved")}</h2>
              <ul>
                {savedJobs.map(({ id, notification }) => (
                  <li key={id}>
                    <Link href={`/jobs/${id}`}>
                      {notification.title || t("noJobs")}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
      {!loading && !error && items.length === 0 && (
        <div className="empty-state">
          <CalendarDays size={23} />
          <p>{t("emptyFeed")}</p>
        </div>
      )}
      {!loading && items.length > 0 && (
        <div className="feed-groups">
          {groups.map((group) => {
            const grouped = items.filter(
              (item) => item.status === group.status,
            );
            if (!grouped.length) return null;
            return (
              <section
                className="feed-group"
                key={group.status}
                aria-labelledby={`group-${group.status}`}
              >
                <h2 id={`group-${group.status}`}>
                  <span className={`status-dot status-${group.status}`} />
                  {group.label}
                  <span className="group-count">{grouped.length}</span>
                </h2>
                <ul className="job-list">
                  {grouped.map((item) => {
                    const fee = fees[item.id];
                    const closingSoon =
                      item.days_left !== null &&
                      item.days_left >= 0 &&
                      item.days_left <= 7;
                    return (
                      <li className="job-row" key={item.id}>
                        <div className="job-main">
                          <div className="job-title-row">
                            <h3>{item.notification || t("noJobs")}</h3>
                            <StatusBadge status={item.status} />
                          </div>
                          <p className="job-org">
                            {item.org || t("unknown")}{" "}
                            {item.matched_post ? (
                              <span>· {item.matched_post}</span>
                            ) : null}
                          </p>
                          <div className="job-facts">
                            {item.last_date && (
                              <span>
                                <CalendarDays size={14} aria-hidden="true" />
                                {formatDate(item.last_date, language)}
                              </span>
                            )}
                            {item.days_left !== null && (
                              <span
                                className={closingSoon ? "deadline-soon" : ""}
                              >
                                {item.days_left} {t("daysLeft")}
                                {closingSoon && <b>{t("closingSoon")}</b>}
                              </span>
                            )}
                            <span>
                              {fee
                                ? formatCurrency(fee.total, language)
                                : t("unknown")}
                            </span>
                          </div>
                          <VerificationBadge
                            status={item.verification_status}
                          />
                        </div>
                        <div className="job-actions">
                          <Link
                            className="button button-secondary"
                            href={`/jobs/${item.id}`}
                          >
                            {t("viewDetails")}{" "}
                            <ArrowUpRight size={16} aria-hidden="true" />
                          </Link>
                          <button
                            className="icon-button"
                            type="button"
                            aria-label={
                              savedIds.includes(item.id)
                                ? t("saved")
                                : t("saveJob")
                            }
                            title={
                              savedIds.includes(item.id)
                                ? t("saved")
                                : t("saveJob")
                            }
                            onClick={async () => {
                              try {
                                saveJobOffline(await getNotification(item.id));
                                setSavedIds((current) => [
                                  ...new Set([...current, item.id]),
                                ]);
                              } catch {
                                setError(t("loadError"));
                              }
                            }}
                          >
                            <Bookmark
                              size={17}
                              fill={
                                savedIds.includes(item.id)
                                  ? "currentColor"
                                  : "none"
                              }
                            />
                          </button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </section>
            );
          })}
          {items.some(
            (item) => item.status === "eligible" || item.status === "likely",
          ) && (
            <p className="feed-note">
              <CircleAlert size={16} />
              {t("disclaimer")}
            </p>
          )}
        </div>
      )}
      <footer className="page-footer">
        <Link href="/stats">{t("stats")}</Link>
        <Link href="/onboarding">{t("profile")}</Link>
      </footer>
    </main>
  );
}
