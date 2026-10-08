export default function HomePage() {
  return (
    <main
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "2rem 1rem",
        fontFamily: "sans-serif",
      }}
    >
      <p
        style={{
          fontSize: "0.8rem",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#026d55",
        }}
      >
        MP Job Saathi
      </p>
      <h1 style={{ fontSize: "2.4rem", margin: "0.5rem 0 1rem" }}>
        For you feed
      </h1>
      <p style={{ lineHeight: 1.7, color: "#334155" }}>
        Official-source-first government alerts, fast eligibility checks, and a
        simple mobile-first feed for Madhya Pradesh job seekers.
      </p>
      <section style={{ display: "grid", gap: "1rem", marginTop: "2rem" }}>
        <div
          style={{
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: 16,
            padding: 18,
          }}
        >
          <strong>Eligible now</strong>
          <p style={{ marginBottom: 0 }}>Junior Engineer (Civil) — MPESB</p>
        </div>
        <div
          style={{
            background: "#f8fafc",
            border: "1px solid #cbd5e1",
            borderRadius: 16,
            padding: 18,
          }}
        >
          <strong>Deadline warning</strong>
          <p style={{ marginBottom: 0 }}>
            State Services exam closes in 7 days
          </p>
        </div>
      </section>
    </main>
  );
}
