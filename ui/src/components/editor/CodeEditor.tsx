import MonacoEditor from "@monaco-editor/react";
import { EditorHeader } from "./EditorHeader";
import { EditorTabs } from "./EditorTabs";
import { db } from "@/data/db";
import React from "react";
import { useContract } from "@/context/ContractContext";
import { usePathname } from "next/navigation";
import { useRefreshFileExplorer } from "../file-explorer/file-explorer";

export const CodeEditor = () => {
  const workspaceName = usePathname();
  const workplaceId = workspaceName.replace("/", "");
  const { selectedFile, fileContent, setFileContent } = useContract();
  const refreshFileContent = useRefreshFileExplorer();

  // Helper function to determine language based on file extension
  const getLanguage = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "cs":
        return "csharp";
      case "proto":
        return "proto3";
      case "csproj":
        return "xml";
      default:
        return "plaintext";
    }
  };

  const onChange = async (value: string) => {
    try {
      setFileContent?.(value);
      await db.files.update(`/workspace/${workplaceId}/${selectedFile}`, {
        contents: value,
      });
      refreshFileContent();
    } catch (error) {
      console.log("error", error);
    }
  };
  return (
    <div className="flex-1 flex flex-col">
      <EditorHeader />
      <div className="flex items-center">
        <EditorTabs />
      </div>

      {selectedFile && (
        <div className="flex-1 p-4 file-result-container bg-gray-800">
          <MonacoEditor
            language={getLanguage(selectedFile)}
            value={fileContent}
            theme="vs-dark"
            onChange={(value) => onChange(value as string)}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 14,
              lineNumbers: "on",
              roundedSelection: false,
              scrollbar: {
                vertical: "visible",
                horizontal: "visible",
                useShadows: false,
                verticalScrollbarSize: 10,
                horizontalScrollbarSize: 10,
              },
              automaticLayout: true,
              wordWrap: "on",
              wrappingStrategy: "advanced",
              formatOnPaste: true,
              formatOnType: true,
            }}
          />
        </div>
      )}
    </div>
  );
};
