import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "다락",
  description: "다락 입지분석 서비스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
