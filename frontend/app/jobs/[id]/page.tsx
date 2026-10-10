"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowUpRight, Bookmark, FileText } from "lucide-react";
import {
  ApiError,
  formatCurrency,
  formatDate,
  getEligibility,
  getFee,
  getLocalProfile,
  getNotification,
  getSavedJob,
  saveJobOffline,
  type EligibilityResult,
  type FeeBreakdown,
  type Notification,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import {
  EligibilityReasons,
  StatusBadge,
  VerificationBadge,
} from "@/components/ui";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { language, t } = useI18n();
  const [notification, setNotification] = useState<Notification | null>(null);
  const [eligibility, setEligibility] = useState<EligibilityResult | null>(
    null,
  );
  const [fee, setFee] = useState<FeeBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const activeProfile = getLocalProfile();
    if (!Number.isInteger(id) || id < 1) {
      setError(t("noJobs"));
      setLoading(false);
      return;
    }
    void Promise.all([
      getNotification(id),
      activeProfile ? getEligibility(id, activeProfile) : Promise.resolve(null),
      activeProfile
        ? getFee(id, activeProfile.category)
        : Promise.resolve(null),
    ])
      .then(([detail, result, feeResult]) => {
        setNotification(detail.notification);
        setEligibility(result);
        setFee(feeResult);
      })
      .catch((cause: unknown) => {
        const saved = getSavedJob(id);
        if (saved) {
          setNotification(saved.notification);
          setOffline(true);
        } else
          setError(cause instanceof ApiError ? cause.message : t("loadError"));
      })
      .finally(() => setLoading(false));
  }, [id, t]);

  if (loading)
    return (
      <main className="page-wrap">
        <p role="status" className="state-message">
          {t("loading")}
        </p>
      </main>
    );
  if (!notification)
    return (
      <main className="page-wrap">
        <p role="alert" className="state-message error-state">
          {error || t("noJobs")}
        </p>
        <Link className="button button-secondary" href="/">
          {t("back")}
        </Link>
      </main>
    );
  const verification =
    notification.source_kind === "fixture"
      ? "fixture"
      : notification.verified_by === "curator"
        ? "verified"
        : "auto";

  return (
    <main className="page-wrap detail-page">
      <Link className="back-link" href="/">
        <ArrowLeft size={16} />
        {t("back")}
      </Link>
      <header className="detail-header">
        <div>
          <p className="eyebrow">
            {notification.org || t("unknown")}
            {notification.advertisement_no
              ? ` · ${notification.advertisement_no}`
              : ""}
          </p>
          <h1>{notification.title || t("noJobs")}</h1>
          <p>
            {notification.total_vacancies == null
              ? t("unknown")
              : `${notification.total_vacancies} ${t("vacancies")}`}
          </p>
          <VerificationBadge status={verification} />
        </div>
        <div className="detail-actions">
          <StatusBadge status={eligibility?.status ?? "needs_check"} />
          <button
            className="icon-button"
            type="button"
            aria-label={t("saveJob")}
            title={t("saveJob")}
            onClick={() => {
              saveJobOffline({ id, notification });
            }}
          >
            <Bookmark size={18} />
          </button>
        </div>
      </header>
      {offline && (
        <p className="offline-note" role="status">
          {t("serviceOffline")}
        </p>
      )}
      {notification.discrepancies.length > 0 && (
        <section
          className="detail-section"
          aria-labelledby="discrepancy-heading"
        >
          <h2 id="discrepancy-heading">{t("discrepancy")}</h2>
          <div className="warning-panel">
            <ul>
              {notification.discrepancies.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        </section>
      )}
      <section className="detail-section" aria-labelledby="dates-heading">
        <h2 id="dates-heading">{t("dates")}</h2>
        <div className="detail-grid">
          {[
            [t("opens"), notification.opens_date],
            [t("deadline"), notification.last_date],
            [t("feeDeadline"), notification.fee_last_date],
            [t("examDate"), notification.exam_date],
          ].map(([label, value]) => (
            <div className="detail-fact" key={label}>
              <span>{label}</span>
              <strong>
                {value ? formatDate(value, language) : t("notMeasured")}
              </strong>
            </div>
          ))}
          <div className="detail-fact">
            <span>{t("feeTotal")}</span>
            <strong>
              {fee ? formatCurrency(fee.total, language) : t("unknown")}
            </strong>
            {fee?.needs_check && <small>{t("unknownFee")}</small>}
          </div>
        </div>
      </section>
      <section className="detail-section" aria-labelledby="eligibility-heading">
        <div className="section-heading-row">
          <h2 id="eligibility-heading">{t("eligibility")}</h2>
          <Link
            className="button button-secondary"
            href={`/jobs/${id}/checklist`}
          >
            {t("checklist")} <ArrowUpRight size={16} />
          </Link>
        </div>
        {eligibility?.post_results.length ? (
          eligibility.post_results.map((post, index) => (
            <div className="post-result" key={`${post.title}-${index}`}>
              <div className="section-heading-row">
                <h3>{post.title || t("unknown")}</h3>
                <StatusBadge status={post.status} />
              </div>
              <EligibilityReasons reasons={post.reasons} />
            </div>
          ))
        ) : (
          <p>{t("unknown")}</p>
        )}
      </section>
      <section className="detail-section" aria-labelledby="sources-heading">
        <h2 id="sources-heading">{t("officialSource")}</h2>
        <div className="source-links">
          {notification.source_urls.map((url) => (
            <a
              className="button button-secondary"
              href={url}
              key={url}
              target="_blank"
              rel="noreferrer"
            >
              {t("officialSource")} <ArrowUpRight size={16} />
            </a>
          ))}
          {notification.notification_pdf_url && (
            <a
              className="button button-secondary"
              href={notification.notification_pdf_url}
              target="_blank"
              rel="noreferrer"
            >
              <FileText size={16} />
              {t("pdf")}
            </a>
          )}
          {!notification.source_urls.length &&
            !notification.notification_pdf_url && (
              <span>{t("sourceNotProvided")}</span>
            )}
        </div>
        <p className="disclaimer">{t("disclaimer")}</p>
      </section>
    </main>
  );
}
