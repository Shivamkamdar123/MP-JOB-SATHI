import "./globals.css";
import { AppShell } from "@/components/AppShell";
import { ServiceWorker } from "@/components/ServiceWorker";
import { I18nProvider } from "@/lib/i18n";

export const metadata = {
  title: "MP Job Saathi",
  description: "Official-source-first job discovery for Madhya Pradesh.",
  manifest: "/manifest.webmanifest",
};

export const viewport = { themeColor: "#17483f" };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          <ServiceWorker />
          <AppShell>{children}</AppShell>
        </I18nProvider>
      </body>
    </html>
  );
}
