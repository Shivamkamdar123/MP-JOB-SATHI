import "./globals.css";

export const metadata = {
  title: "MP Job Saathi",
  description: "Official-source-first job discovery for Madhya Pradesh.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
