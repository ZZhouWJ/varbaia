import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Verbaia · 英语沉浸学习",
  description: "个人英语沉浸学习工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
