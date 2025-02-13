import MonacoEditor from "@monaco-editor/react";
import { EditorHeader } from "./EditorHeader";
import { EditorTabs } from "./EditorTabs";

interface CodeEditorProps {
  files: string[];
  selectedFile: string;
  content: string;
  onFileSelect: (file: string) => void;
  onFileClose: (file: string) => void;
  onContentChange?: (value: string) => void;
  onDeploy?: () => void;
}

export const CodeEditor = ({
  files,
  selectedFile,
  content,
  onFileSelect,
  onFileClose,
  onContentChange,
  onDeploy,
}: CodeEditorProps) => {
  return (
    <>
      <EditorHeader onDeploy={onDeploy} />
      
      <div className="flex items-center">
        <EditorTabs
          files={files}
          selectedFile={selectedFile}
          onFileSelect={onFileSelect}
          onFileClose={onFileClose}
        />
      </div>

      {selectedFile && (
        <div className="flex-1 p-4 file-result-container bg-gray-800">
          <MonacoEditor
            language="csharp"
            value={content}
            theme="vs-dark"
            onChange={(value) => onContentChange?.(value as string)}
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
            }}
          />
        </div>
      )}
    </>
  );
}; 