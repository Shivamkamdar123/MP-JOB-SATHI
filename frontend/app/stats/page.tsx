"use client";

import { useEffect, useState } from "react";
import { getStats, type StatsResponse } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Metric = {
  precision?: number | null;
  recall?: number | null;
  accuracy?: number | null;
};
type Benchmark = {
  n?: number;
  metrics?: Record<string, Metric>;
  failures?: Array<{
    document?: string;
    field?: string;
    expected?: unknown;
    actual?: unknown;
  }>;
};

function asBenchmark(data: Record<string, unknown>): Benchmark {
  return data as Benchmark;
}

export default function StatsPage() {
  const { language, t } = useI18n();
  const [result, setResult] = useState<StatsResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void getStats()
      .then(setResult)
      .catch(() => setError(t("loadError")))
      .finally(() => setLoading(false));
  }, [t]);

  const number = (value: number | null | undefined) =>
    value == null
      ? t("notMeasured")
      : new Intl.NumberFormat(language === "hi" ? "hi-IN" : "en-IN", {
          style: "percent",
          maximumFractionDigits: 1,
        }).format(value);
  return (
    <main className="page-wrap">
      <div className="page-heading">
        <div>
          <p className="eyebrow">{t("brand")}</p>
          <h1>{t("statsTitle")}</h1>
        </div>
      </div>
      {loading && (
        <p role="status" className="state-message">
          {t("loading")}
        </p>
      )}
      {error && (
        <p role="alert" className="state-message error-state">
          {error}
        </p>
      )}
      {!loading && !error && result?.items.length === 0 && (
        <p className="state-message">{t("notMeasured")}</p>
      )}
      {!loading &&
        !error &&
        result?.items.map((file) => {
          const data = asBenchmark(file.data);
          const generated = file.generated_at ?? result.generated_at;
          const formattedDate = new Intl.DateTimeFormat(
            language === "hi" ? "hi-IN" : "en-IN",
            { dateStyle: "medium", timeStyle: "short" },
          ).format(new Date(generated));
          const fields = Object.entries(data.metrics ?? {});
          return (
            <section className="stats-section" key={file.name}>
              <div className="stats-meta">
                <h2>{file.name}</h2>
                <span className="stats-date">
                  {t("generated")}: {formattedDate}
                </span>
              </div>
              <div className="stat-sample">
                <strong>{data.n ?? "—"}</strong>
                <span>{t("sampleCount")}</span>
              </div>
              {fields.length > 0 && (
                <div className="stats-table-wrap">
                  <table className="stats-table">
                    <thead>
                      <tr>
                        <th>{t("eligibility")}</th>
                        <th>{t("precision")}</th>
                        <th>{t("recall")}</th>
                        <th>{t("accuracy")}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fields.map(([field, metric]) => (
                        <tr key={field}>
                          <th scope="row">
                            {t(`stat_${field}` as Parameters<typeof t>[0]) ||
                              field.replaceAll("_", " ")}
                          </th>
                          <td className="stat-number">
                            {number(metric.precision)}
                          </td>
                          <td className="stat-number">
                            {number(metric.recall)}
                          </td>
                          <td className="stat-number">
                            {number(metric.accuracy)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <h3 className="stats-failures-heading">
                {t("failures")} ({data.failures?.length ?? 0})
              </h3>
              {data.failures?.length ? (
                <ul className="failure-list">
                  {data.failures.map((failure, index) => (
                    <li key={`${failure.document}-${failure.field}-${index}`}>
                      <strong>
                        {failure.document} · {failure.field}
                      </strong>
                      <span>
                        {t("expected")}: {JSON.stringify(failure.expected)};{" "}
                        {t("actual")}: {JSON.stringify(failure.actual)}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="stats-date">
                  {data.n ? t("noFailures") : t("notMeasured")}
                </p>
              )}
            </section>
          );
        })}
    </main>
  );
}
