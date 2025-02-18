import { ReactNode } from "react";
import { Open_Sans } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

import { ModelSelectorProvider } from "@/lib/model-selector-provider";
import { Header } from "@/components/header";
import Providers from "@/providers";
import "./globals.css";


const openSans = Open_Sans({ subsets: ["latin"] });

export const metadata = {
  title: "AElf Code Generator",
  description: "AI-powered code generator for AElf ecosystem",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={openSans.className}>
        <Providers>
          <CopilotKit runtimeUrl="/api/copilotkit" agent="aelf_code_generator">
            <Header />
            <ModelSelectorProvider>{children}</ModelSelectorProvider>
          </CopilotKit>
        </Providers>
      </body>
    </html>
  );
}
