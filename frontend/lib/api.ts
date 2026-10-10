export type Language = "en" | "hi";
export type EligibilityStatus = "eligible" | "likely" | "needs_check" | "not_eligible";

export type Qualification = {
  level: string;
  stream?: string | null;
  board?: string | null;
  year?: number | null;
  percentage?: number | null;
};

export type Profile = {
  name: string;
  date_of_birth: string;
  gender: string;
  category: string;
  mp_domicile: boolean;
  pwd: boolean;
  ex_serviceman: boolean;
  qualifications: Qualification[];
  experience_years: number;
  preferred_districts: string[];
  employment_exchange_registered: boolean;
  target_roles: string[];
  certificates?: string[];
  languages?: string[];
};

export type FieldProvenance = {
  source_page: number | null;
  snippet: string;
  confidence: number;
  method: "regex" | "table" | "llm" | "ocr";
};

export type Post = {
  title: string | null;
  vacancies: number | null;
  qualification_rules: Array<{
    level: string;
    stream?: string | null;
    min_percent?: number | null;
    required_certificate?: string | null;
  }>;
  age_min: number | null;
  age_max: number | null;
  category_vacancies: Record<string, number>;
};

export type Notification = {
  org: string | null;
  advertisement_no: string | null;
  title: string | null;
  posts: Post[];
  total_vacancies: number | null;
  category_vacancies: Record<string, number>;
  opens_date: string | null;
  last_date: string | null;
  fee_last_date: string | null;
  correction_window: string | null;
  exam_date: string | null;
  fee_by_category: Record<string, number>;
  portal_charges: number | null;
  age_limit: Record<string, string | number | null>;
  source_urls: string[];
  notification_pdf_url: string | null;
  source_kind: "official" | "fixture" | "lead";
  verified_by: "auto" | "curator";
  discrepancies: string[];
  field_provenance: Record<string, FieldProvenance>;
  review_required: boolean;
  status: string | null;
};

export type FeedItem = {
  id: number;
  notification: string | null;
  org: string | null;
  status: EligibilityStatus;
  matched_post: string | null;
  matched_posts: string[];
  last_date: string | null;
  days_left: number | null;
  source: string | null;
  reasons: Array<{ check: string; result: "pass" | "fail" | "unknown"; message: string }>;
  review_required: boolean;
  verification_notice: string | null;
  verification_status: "verified" | "auto" | "fixture";
};

export type EligibilityResult = {
  status: EligibilityStatus;
  reasons: Array<{ check: string; result: "pass" | "fail" | "unknown"; message: string }>;
  matched_post: string | null;
  matched_posts: string[];
  post_results: Array<{
    title: string | null;
    status: EligibilityStatus;
    reasons: Array<{ check: string; result: "pass" | "fail" | "unknown"; message: string }>;
  }>;
};

export type FeeBreakdown = {
  category: string;
  fee: number | null;
  portal_charges: number | null;
  total: number | null;
  needs_check: boolean;
  message: string | null;
};

export type ChecklistItem = { title: string; status: string; message: string };
export type NotificationDetail = { id: number; notification: Notification };
export type StatsFile = { name: string; generated_at: string | null; data: Record<string, unknown> };
export type StatsResponse = { generated_at: string; items: StatsFile[] };

const apiBaseUrl = "/backend-api";
const PROFILE_KEY = "mpjs.profile.v1";
const SAVED_JOBS_KEY = "mpjs.saved-jobs.v1";

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Network unavailable. Try again or open a saved job.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // Keep the status-based message for non-JSON errors.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export const getFeed = (profile: Profile) =>
  apiRequest<{ items: FeedItem[] }>("/feed", { method: "POST", body: JSON.stringify({ profile }) });

export async function getNotification(id: number): Promise<NotificationDetail> {
  try {
    return await apiRequest<NotificationDetail>(`/notifications/${id}`);
  } catch (error) {
    const saved = getSavedJob(id);
    if (saved) return saved;
    throw error;
  }
}

export const getEligibility = (id: number, profile: Profile) =>
  apiRequest<EligibilityResult>("/eligibility/check", { method: "POST", body: JSON.stringify({ notification_id: id, profile }) });

export const getFee = (id: number, category: string) =>
  apiRequest<FeeBreakdown>("/fee", { method: "POST", body: JSON.stringify({ notification_id: id, category }) });

export async function saveProfile(profile: Profile): Promise<{ offline: boolean }> {
  if (typeof localStorage !== "undefined") localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  try {
    await apiRequest("/profiles", { method: "POST", body: JSON.stringify({ profile }) });
  } catch (error) {
    if (error instanceof ApiError && error.status !== undefined) throw error;
    return { offline: true };
  }
  return { offline: false };
}

export function getLocalProfile(): Profile | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const value = localStorage.getItem(PROFILE_KEY);
    return value ? (JSON.parse(value) as Profile) : null;
  } catch {
    return null;
  }
}

export const getChecklist = (id: number, profile: Profile) =>
  apiRequest<{ items: ChecklistItem[] }>("/assist/pre-submit-checklist", {
    method: "POST",
    body: JSON.stringify({ notification_id: id, profile, category: profile.category }),
  });

export const getStats = () => apiRequest<StatsResponse>("/stats");

export function saveJobOffline(detail: NotificationDetail): void {
  if (typeof localStorage === "undefined") return;
  const jobs = getSavedJobs();
  localStorage.setItem(SAVED_JOBS_KEY, JSON.stringify({ ...jobs, [detail.id]: detail }));
}

export function getSavedJobs(): Record<number, NotificationDetail> {
  if (typeof localStorage === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(SAVED_JOBS_KEY) ?? "{}") as Record<number, NotificationDetail>;
  } catch {
    return {};
  }
}

export function getSavedJob(id: number): NotificationDetail | null {
  return getSavedJobs()[id] ?? null;
}

export function formatDate(value: string | null | undefined, language: Language): string {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(language === "hi" ? "hi-IN" : "en-IN", {
    day: "2-digit", month: "2-digit", year: "numeric", timeZone: "Asia/Kolkata",
  }).format(parsed);
}

export function formatCurrency(value: number | null | undefined, language: Language): string {
  if (value == null) return language === "hi" ? "उल्लेख नहीं" : "Not stated";
  return new Intl.NumberFormat(language === "hi" ? "hi-IN" : "en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 2,
  }).format(value);
}