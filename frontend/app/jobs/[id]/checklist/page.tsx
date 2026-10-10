"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import {
  formatCurrency,
  formatDate,
  getChecklist,
  getLocalProfile,
  type ChecklistItem,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export default function ChecklistPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { language, t } = useI18n();
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const profile = getLocalProfile();
    if (!profile) {
      setError(t("noProfile"));
      setLoading(false);
      return;
    }
    void getChecklist(id, profile)
      .then((response) => {
        const loaded = [...response.items];
        if (
          !loaded.some((item) => item.title.toLowerCase().includes("deadline"))
        ) {
          loaded.push({
            title: t("deadline"),
            status: "needs_check",
            message: t("unknownFee"),
          });
        }
        setItems(loaded);
      })
      .catch(() => setError(t("checklistUnavailable")))
      .finally(() => setLoading(false));
  }, [id, t]);

  return (
    <main className="page-wrap">
      <Link className="back-link" href={`/jobs/${id}`}>
        <ArrowLeft size={16} />
        {t("back")}
      </Link>
      <section className="detail-section">
        <p className="eyebrow">{t("checklist")}</p>
        <h1>{t("checklist")}</h1>
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
        {!loading && !error && items.length === 0 && (
          <p className="state-message">{t("notMeasured")}</p>
        )}
        <ul className="checklist-list">
          {items.map((item, index) => {
            const isChecked = checked[index] ?? item.status === "done";
            const titleKeys: Record<string, Parameters<typeof t>[0]> = {
              "Fee payment": "fee",
              "Documents ready": "documents",
              "Eligibility review": "eligibilityReview",
              "Deadline check": "deadline",
            };
            const titleKey = titleKeys[item.title];
            let message = item.message;
            if (language === "hi") {
              if (item.title === "Fee payment") {
                const amountText = item.message.match(/₹\s*([\d,.]+)/)?.[1];
                const amount = amountText
                  ? Number(amountText.replaceAll(",", ""))
                  : null;
                message =
                  amount == null
                    ? t("unknownFee")
                    : `${t("feeGuide")} ${formatCurrency(amount, language)}`;
              } else if (item.title === "Documents ready") {
                message = t("documentsGuide");
              } else if (item.title === "Eligibility review") {
                message = t("eligibilityGuide");
              } else if (item.title === "Deadline check") {
                const dateText = item.message.match(
                  /\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}/,
                )?.[0];
                message = dateText
                  ? t("deadlineGuide").replace(
                      "{date}",
                      formatDate(dateText, language),
                    )
                  : t("deadlineGuide").replace("{date}", t("unknown"));
              }
            }
            return (
              <li
                className={`check-row${isChecked ? " checked" : ""}`}
                key={`${item.title}-${index}`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={(event) =>
                    setChecked((current) => ({
                      ...current,
                      [index]: event.target.checked,
                    }))
                  }
                  aria-label={titleKey ? t(titleKey) : item.title}
                />
                <div>
                  <strong>{titleKey ? t(titleKey) : item.title}</strong>
                  <p>{message}</p>
                  <small>
                    {item.status === "done"
                      ? t("checklistDone")
                      : item.status === "warning"
                        ? t("checklistWarning")
                        : t("checklistPending")}
                  </small>
                </div>
              </li>
            );
          })}
        </ul>
        <p className="disclaimer">{t("disclaimer")}</p>
      </section>
    </main>
  );
}
