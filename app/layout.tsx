import "./globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "LLM Price Predictor",
  description: "IB CS IA Project",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}