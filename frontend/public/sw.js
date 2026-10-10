const CACHE_NAME = "mp-job-saathi-v1";
const SHELL = [
  "/",
  "/offline.html",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  const isApiRead =
    url.pathname.startsWith("/backend-api/notifications/") ||
    url.pathname === "/backend-api/stats";
  const isRouteData =
    url.origin === self.location.origin &&
    (url.searchParams.has("_rsc") || request.headers.get("RSC") === "1");
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            void caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(
          async () =>
            (await caches.match(request)) ||
            (await caches.match("/offline.html")),
        ),
    );
    return;
  }

  if (isApiRead || isRouteData) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok)
            void caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, response.clone()));
          return response;
        })
        .catch(async () => (await caches.match(request)) || Response.error()),
    );
    return;
  }

  const cacheableAsset =
    url.origin === self.location.origin &&
    ["script", "style", "image", "font"].includes(request.destination);
  if (cacheableAsset) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok)
            void caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, response.clone()));
          return response;
        })
        .catch(async () => (await caches.match(request)) || Response.error()),
    );
  }
});
