"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Plus, ArrowLeft } from "lucide-react";
import { saveProfile, type Profile, type Qualification } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

type Draft = Omit<Profile, "qualifications"> & {
  qualifications: Qualification[];
};

const blankProfile: Draft = {
  name: "",
  date_of_birth: "",
  gender: "",
  category: "UR",
  mp_domicile: true,
  pwd: false,
  ex_serviceman: false,
  qualifications: [{ level: "", stream: "", percentage: null }],
  experience_years: 0,
  preferred_districts: [],
  employment_exchange_registered: false,
  target_roles: [],
};

export default function OnboardingPage() {
  const { t } = useI18n();
  const router = useRouter();
  const [step, setStep] = useState<"consent" | "profile">("consent");
  const [consent, setConsent] = useState(false);
  const [draft, setDraft] = useState<Draft>(blankProfile);
  const [districtText, setDistrictText] = useState("");
  const [roleText, setRoleText] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [offline, setOffline] = useState(false);

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function changeQualification(
    index: number,
    key: keyof Qualification,
    value: string,
  ) {
    setDraft((current) => ({
      ...current,
      qualifications: current.qualifications.map((qualification, itemIndex) =>
        itemIndex === index
          ? {
              ...qualification,
              [key]:
                key === "percentage"
                  ? value === ""
                    ? null
                    : Number(value)
                  : value,
            }
          : qualification,
      ),
    }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const date = new Date(`${draft.date_of_birth}T00:00:00`);
    if (
      !draft.name.trim() ||
      !draft.gender ||
      !draft.date_of_birth ||
      Number.isNaN(date.getTime()) ||
      date > new Date()
    ) {
      setError(t("invalidDate"));
      return;
    }
    if (
      draft.qualifications.some(
        (qualification) =>
          !qualification.level.trim() ||
          (qualification.percentage != null &&
            (qualification.percentage < 0 || qualification.percentage > 100)),
      )
    ) {
      setError(t("invalidProfile"));
      return;
    }
    const profile: Profile = {
      ...draft,
      name: draft.name.trim(),
      qualifications: draft.qualifications.map((item) => ({
        ...item,
        stream: item.stream?.trim() || null,
      })),
      preferred_districts: districtText
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
      target_roles: roleText
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
    };
    setSaving(true);
    try {
      const result = await saveProfile(profile);
      setOffline(result.offline);
      if (!result.offline) {
        router.push("/");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t("loadError"));
    } finally {
      setSaving(false);
    }
  }

  if (step === "consent")
    return (
      <main className="page-wrap">
        <section
          className="form-panel consent-copy"
          aria-labelledby="consent-title"
        >
          <p className="eyebrow">{t("consent")}</p>
          <h1 id="consent-title">{t("consentTitle")}</h1>
          <p className="form-intro">{t("consentBody")}</p>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            {t("consentCheck")}
          </label>
          <button
            className="button button-primary"
            type="button"
            disabled={!consent}
            onClick={() => setStep("profile")}
          >
            {t("continue")}
          </button>
        </section>
      </main>
    );

  return (
    <main className="page-wrap">
      <section className="form-panel">
        <Link className="back-link" href="/">
          <ArrowLeft size={16} />
          {t("back")}
        </Link>
        <p className="eyebrow">{t("profile")}</p>
        <h1>{t("profile")}</h1>
        <p className="form-intro">{t("consentBody")}</p>
        <form onSubmit={(event) => void submit(event)} noValidate>
          <div className="form-grid">
            <label className="form-field">
              <span>{t("name")}</span>
              <input
                required
                maxLength={120}
                value={draft.name}
                onChange={(event) => update("name", event.target.value)}
                autoComplete="name"
              />
            </label>
            <label className="form-field">
              <span>{t("dob")}</span>
              <input
                required
                type="date"
                value={draft.date_of_birth}
                onChange={(event) =>
                  update("date_of_birth", event.target.value)
                }
                autoComplete="bday"
              />
            </label>
            <label className="form-field">
              <span>{t("gender")}</span>
              <select
                required
                value={draft.gender}
                onChange={(event) => update("gender", event.target.value)}
              >
                <option value="">{t("select")}</option>
                <option value="male">{t("male")}</option>
                <option value="female">{t("female")}</option>
                <option value="other">{t("other")}</option>
              </select>
            </label>
            <label className="form-field">
              <span>{t("category")}</span>
              <select
                value={draft.category}
                onChange={(event) => update("category", event.target.value)}
              >
                {["UR", "OBC", "SC", "ST", "EWS"].map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <fieldset className="form-field field-full choice-field">
              <legend>{t("domicile")}</legend>
              <div className="choice-row">
                {[true, false].map((value) => (
                  <label key={String(value)}>
                    <input
                      type="radio"
                      name="domicile"
                      checked={draft.mp_domicile === value}
                      onChange={() => update("mp_domicile", value)}
                    />
                    {value ? t("yes") : t("no")}
                  </label>
                ))}
              </div>
            </fieldset>
            <fieldset className="form-field field-full choice-field">
              <legend>{t("pwd")}</legend>
              <div className="choice-row">
                {[true, false].map((value) => (
                  <label key={String(value)}>
                    <input
                      type="radio"
                      name="pwd"
                      checked={draft.pwd === value}
                      onChange={() => update("pwd", value)}
                    />
                    {value ? t("yes") : t("no")}
                  </label>
                ))}
              </div>
            </fieldset>
            <fieldset className="form-field field-full choice-field">
              <legend>{t("exServiceman")}</legend>
              <div className="choice-row">
                {[true, false].map((value) => (
                  <label key={String(value)}>
                    <input
                      type="radio"
                      name="ex-serviceman"
                      checked={draft.ex_serviceman === value}
                      onChange={() => update("ex_serviceman", value)}
                    />
                    {value ? t("yes") : t("no")}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="form-field field-full">
              <span className="field-label">{t("qualification")}</span>
              {draft.qualifications.map((qualification, index) => (
                <div className="qualification-block" key={index}>
                  <label className="form-field">
                    <span>{t("qualification")}</span>
                    <input
                      required
                      value={qualification.level}
                      onChange={(event) =>
                        changeQualification(index, "level", event.target.value)
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>{t("stream")}</span>
                    <input
                      value={qualification.stream ?? ""}
                      onChange={(event) =>
                        changeQualification(index, "stream", event.target.value)
                      }
                    />
                  </label>
                  <label className="form-field">
                    <span>{t("percentage")}</span>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={qualification.percentage ?? ""}
                      onChange={(event) =>
                        changeQualification(
                          index,
                          "percentage",
                          event.target.value,
                        )
                      }
                    />
                  </label>
                </div>
              ))}
              <button
                className="text-button add-row"
                type="button"
                onClick={() =>
                  update("qualifications", [
                    ...draft.qualifications,
                    { level: "", stream: "", percentage: null },
                  ])
                }
              >
                <Plus size={15} />
                {t("addQualification")}
              </button>
            </div>
            <label className="form-field">
              <span>{t("experience")}</span>
              <input
                type="number"
                min="0"
                max="60"
                step="0.5"
                value={draft.experience_years}
                onChange={(event) =>
                  update("experience_years", Number(event.target.value))
                }
              />
            </label>
            <label className="form-field">
              <span>{t("exchange")}</span>
              <select
                value={String(draft.employment_exchange_registered)}
                onChange={(event) =>
                  update(
                    "employment_exchange_registered",
                    event.target.value === "true",
                  )
                }
              >
                <option value="true">{t("yes")}</option>
                <option value="false">{t("no")}</option>
              </select>
            </label>
            <label className="form-field">
              <span>{t("districts")}</span>
              <input
                value={districtText}
                onChange={(event) => setDistrictText(event.target.value)}
              />
            </label>
            <label className="form-field">
              <span>{t("roles")}</span>
              <input
                value={roleText}
                onChange={(event) => setRoleText(event.target.value)}
              />
            </label>
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {offline && (
            <p className="offline-note" role="status">
              {t("profileStored")} <Link href="/">{t("feed")}</Link>
            </p>
          )}
          <div className="form-actions">
            <span className="form-hint">{t("consentBody")}</span>
            <button
              className="button button-primary"
              type="submit"
              disabled={saving}
            >
              {saving ? t("loading") : t("saveProfile")}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
