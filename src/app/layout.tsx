import { ReactNode } from "react";
import { Inter } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";
import { Analytics } from "@vercel/analytics/react";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "AElf Code Generator",
  description: "AI-powered code generator for AElf ecosystem",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CopilotKit runtimeUrl="/api/copilotkit">
          {children}
          <Analytics />
        </CopilotKit>
      </body>
    </html>
  );
} 