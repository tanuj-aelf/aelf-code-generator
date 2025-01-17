'use client';

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotContext } from "@copilotkit/react-core";

function MainContent() {
  const [activeTab, setActiveTab] = useState("code");
  const [code, setCode] = useState("");

  return (
    <div className="flex h-screen bg-[#1E1E1E]">
      <div className="flex-1 flex flex-col">
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-white">AElf Code Generator</h1>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" className="text-gray-400 hover:text-white">
              Preview
            </Button>
            <Button variant="ghost" className="text-gray-400 hover:text-white">
              Deploy
            </Button>
          </div>
        </header>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <div className="border-b border-gray-800">
            <TabsList className="bg-transparent border-b border-gray-800">
              <TabsTrigger value="code" className="text-gray-400 data-[state=active]:text-white">
                Code
              </TabsTrigger>
              <TabsTrigger value="console" className="text-gray-400 data-[state=active]:text-white">
                Console
              </TabsTrigger>
            </TabsList>
          </div>
          
          <TabsContent value="code" className="flex-1 p-4">
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full h-full bg-[#1E1E1E] text-white font-mono resize-none focus:outline-none"
              placeholder="// Write or generate your code here..."
              spellCheck={false}
            />
          </TabsContent>
          
          <TabsContent value="console" className="flex-1 p-4 bg-[#1E1E1E] text-gray-300">
            <div className="font-mono">
              No console output available to display
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
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