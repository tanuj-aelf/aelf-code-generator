'use client';

import { CopilotTextarea } from "@copilotkit/react-textarea";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useState } from "react";

function MainContent() {
  const [prompt, setPrompt] = useState("");

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl md:text-6xl">
            AElf Code Generator
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Generate smart contracts, dApps, and more for the AElf ecosystem using AI
          </p>
        </div>

        <div className="mt-16">
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <textarea
                className="w-full h-64 p-4 text-gray-900 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe what you want to build..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Generate Code
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <CopilotSidebar
      defaultOpen={true}
      instructions={"I am an AI assistant specialized in helping you generate and understand code for the AElf blockchain ecosystem. I can help you with smart contracts, dApps, and other blockchain-related development tasks."}
      labels={{
        title: "AElf Assistant",
        initial: "How can I help you with your AElf development today?",
      }}
    >
      <MainContent />
    </CopilotSidebar>
  );
} 