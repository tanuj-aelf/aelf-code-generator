import { ReactNode } from "react";
import { Inter } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";
import { ModelSelectorProvider } from "@/lib/model-selector-provider";
import { ContractProvider } from "@/context/ContractContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "AElf Code Generator",
  description: "AI-powered code generator for AElf ecosystem",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ContractProvider>
          <CopilotKit 
            runtimeUrl="/api/copilotkit"
            agent="aelf_code_generator"
          >
            <ModelSelectorProvider>
              {children}
            </ModelSelectorProvider>
          </CopilotKit>
        </ContractProvider>
      </body>
    </html>
  );
} 