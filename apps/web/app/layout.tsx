import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rhymes — SecondEar",
  description: "Evidence-based phonetic analysis for English lyrics.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
