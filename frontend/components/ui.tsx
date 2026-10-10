import { CircleCheck, CircleHelp, CircleX } from "lucide-react";
import type { EligibilityStatus, FeedItem } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

const statusKeys: Record<
  EligibilityStatus,
  "eligible" | "likely" | "needs_check" | "not_eligible"
> = {
  eligible: "eligible",
  likely: "likely",
  needs_check: "needs_check",
  not_eligible: "not_eligible",
};

export function StatusBadge({ status }: { status: EligibilityStatus }) {
  const { t } = useI18n();
  return (
    <span className={`status-badge status-${status}`}>
      {t(statusKeys[status])}
    </span>
  );
}

export function VerificationBadge({
  status,
}: {
  status: FeedItem["verification_status"];
}) {
  const { t } = useI18n();
  const key =
    status === "verified"
      ? "verification_verified"
      : status === "fixture"
        ? "verification_fixture"
        : "verification_auto";
  return (
    <span className={`verification-badge verification-${status}`}>
      <CircleCheck size={14} aria-hidden="true" />
      {t(key)}
    </span>
  );
}

export function EligibilityReasons({
  reasons,
}: {
  reasons: Array<{
    check: string;
    result: "pass" | "fail" | "unknown";
    message: string;
  }>;
}) {
  const { language, t } = useI18n();
  const icon = {
    pass: <CircleCheck size={18} aria-hidden="true" />,
    fail: <CircleX size={18} aria-hidden="true" />,
    unknown: <CircleHelp size={18} aria-hidden="true" />,
  };
  return (
    <ul className="reason-list">
      {reasons.map((reason, index) => (
        <li
          className={`reason-row reason-${reason.result}`}
          key={`${reason.check}-${index}`}
        >
          {icon[reason.result]}
          <div>
            <strong>
              {t(`check_${reason.check}` as Parameters<typeof t>[0]) ||
                (language === "hi"
                  ? "जाँच"
                  : reason.check.replaceAll("_", " "))}
            </strong>
            <p>{reason.message}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
