import "./globals.css";

export const metadata = {
  title: "LLM Price Predictor",
  description: "IB CS IA Project",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
