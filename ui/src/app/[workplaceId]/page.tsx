"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { FileExplorer } from "@/components/file-explorer/file-explorer";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { ChatWindow } from "@/components/chat";

export default function Workplace() {
  return (
    <MainLayout fullScreen={false} className={"pt-[70px]"}>
      <div className="flex-1 flex">
        <FileExplorer />
        <CodeEditor />
        <div className="w-[400px] flex flex-col border-l border-gray-700">
          <ChatWindow />
        </div>
      </div>
    </MainLayout>
  );
}
