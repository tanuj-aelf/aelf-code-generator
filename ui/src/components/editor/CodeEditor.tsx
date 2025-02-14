import MonacoEditor from "@monaco-editor/react";
import { EditorHeader } from "./EditorHeader";
import { EditorTabs } from "./EditorTabs";
import { db, FileContent } from "@/db/db";
import React from "react";

interface CodeEditorProps {
  files: string[];
  selectedFile: string;
  content: string;
  onFileSelect: (file: string) => void;
  onFileClose: (file: string) => void;
  onContentChange?: (value: string) => void;
  onDeploy?: () => void;
  onBuild?: () => void;
  isBuilding?: boolean;
  buildStatus?: 'idle' | 'success' | 'error';
  workplaceId: string;
}

export const CodeEditor = ({
  files,
  selectedFile,
  content,
  onFileSelect,
  onFileClose,
  onContentChange,
  onDeploy,
  onBuild,
  isBuilding,
  buildStatus,
  workplaceId
}: CodeEditorProps) => {
  // Helper function to determine language based on file extension
  const getLanguage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'cs':
        return 'csharp';
      case 'proto':
        return 'proto3';
      case 'csproj':
        return 'xml';
      default:
        return 'plaintext';
    }
  };

  console.log("selectedFile",selectedFile)

  const onChange = React.useCallback(
    async (value: string) => {
      onContentChange?.(value)
      await db.files.update(`/workspace/${workplaceId}/${selectedFile}`, { contents: value });
    },
    [workplaceId]
  );
  return (
    <>
      <EditorHeader 
        onDeploy={onDeploy}
        onBuild={onBuild}
        isBuilding={isBuilding}
        buildStatus={buildStatus}
      />
      
      <div className="flex items-center">
        <EditorTabs />
      </div>

      {selectedFile && (
        <div className="flex-1 p-4 file-result-container bg-gray-800">
          <MonacoEditor
            language={getLanguage(selectedFile)}
            value={content}
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
    </>
  );
}; 