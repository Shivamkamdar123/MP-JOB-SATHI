import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest, getNotification, getSavedJob, saveJobOffline, saveProfile, type NotificationDetail, type Profile } from "./api";

const profile: Profile = {
  name: "Asha Patel", date_of_birth: "1998-04-12", gender: "female", category: "OBC",
  mp_domicile: true, pwd: false, ex_serviceman: false, qualifications: [{ level: "Graduate", stream: "Arts" }],
  experience_years: 1, preferred_districts: ["Bhopal"], employment_exchange_registered: false, target_roles: ["Assistant"],
};

beforeEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe("typed API client", () => {
  it("returns typed JSON and sends JSON request headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiRequest<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ headers: { "Content-Type": "application/json" } });
  });

  it("surfaces typed HTTP failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Not found" }), { status: 404 })));
    await expect(apiRequest("/missing")).rejects.toMatchObject({ message: "Not found", status: 404 });
  });

  it("stores profiles locally when the API is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(saveProfile(profile)).resolves.toEqual({ offline: true });
    expect(JSON.parse(localStorage.getItem("mpjs.profile.v1") ?? "null")).toEqual(profile);
  });

  it("returns a saved job when notification GET is offline", async () => {
    const detail = { id: 7, notification: { title: "Offline notice" } } as NotificationDetail;
    saveJobOffline(detail);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(getNotification(7)).resolves.toEqual(detail);
    expect(getSavedJob(7)).toEqual(detail);
  });
});