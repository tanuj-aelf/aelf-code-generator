import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface FileNode {
  path: string;
  content: string;
  file_type: string;
}

interface FileExplorerProps {
  files: FileNode[];
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  files,
  selectedFile,
  onFileSelect,
}) => {
  const getFileName = (path: string) => path.split('/').pop() || path;

  const selectedFileContent = files.find(f => f.path === selectedFile);

  return (
    <div className="flex h-full">
      {/* File Tree */}
      <div className="w-64 bg-[#1e1e1e] border-r border-gray-700 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-white text-sm font-semibold mb-4">Generated Files</h3>
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.path}
                className={`cursor-pointer p-2 rounded text-sm ${
                  selectedFile === file.path
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
                onClick={() => onFileSelect(file.path)}
              >
                {getFileName(file.path)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Code Content */}
      <div className="flex-1 overflow-auto">
        {selectedFileContent ? (
          <SyntaxHighlighter
            language={selectedFileContent.file_type}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              minHeight: '100%',
              background: '#1e1e1e',
            }}
          >
            {selectedFileContent.content}
          </SyntaxHighlighter>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Select a file to view its content
          </div>
        )}
      </div>
    </div>
  );
}; 