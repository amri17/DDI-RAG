import type { Metadata } from "next";

import AppShell from "@/components/appshell";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ICU-Q",
    template: "%s | ICU-Q",
  },

  description: "ICU queue and patient risk monitoring system.",

  icons: {
    icon: "/icuq.png",
    shortcut: "/favicon.ico",
    apple: "/icuq.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

