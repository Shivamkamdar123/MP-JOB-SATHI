import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EligibilityReasons, VerificationBadge } from "./ui";
import { I18nProvider, useI18n } from "@/lib/i18n";

function LanguageSwitch() {
  const { language, setLanguage, t } = useI18n();
  return (
    <>
      <p>{t("feed")}</p>
      <button onClick={() => setLanguage(language === "en" ? "hi" : "en")}>
        switch
      </button>
    </>
  );
}

describe("eligibility and verification presentation", () => {
  it("renders pass, fail, and unknown reasons with their messages", () => {
    render(
      <I18nProvider>
        <EligibilityReasons
          reasons={[
            { check: "age", result: "pass", message: "Age is within range." },
            {
              check: "domicile",
              result: "fail",
              message: "Domicile is required.",
            },
            { check: "fee", result: "unknown", message: "Fee needs checking." },
          ]}
        />
      </I18nProvider>,
    );
    expect(screen.getByText("Age is within range.")).toBeInTheDocument();
    expect(screen.getByText("Domicile is required.")).toBeInTheDocument();
    expect(screen.getByText("Fee needs checking.")).toBeInTheDocument();
    expect(document.querySelectorAll(".reason-row")).toHaveLength(3);
  });

  it.each([
    ["verified", "Verified from official notification"],
    ["auto", "Auto-extracted, verify before applying"],
    ["fixture", "Sample data (fixture)"],
  ] as const)("renders %s verification state", (status, text) => {
    render(
      <I18nProvider>
        <VerificationBadge status={status} />
      </I18nProvider>,
    );
    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it("switches language and stores the choice", () => {
    const { unmount } = render(
      <I18nProvider>
        <LanguageSwitch />
      </I18nProvider>,
    );
    expect(screen.getByText("For you")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "switch" }));
    expect(screen.getByText("आपके लिए")).toBeInTheDocument();
    expect(localStorage.getItem("mpjs.language")).toBe("hi");
    unmount();
    render(
      <I18nProvider>
        <LanguageSwitch />
      </I18nProvider>,
    );
    expect(screen.getByText("आपके लिए")).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("hi");
  });
});
