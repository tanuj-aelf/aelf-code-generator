"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import MonacoEditor from "@monaco-editor/react";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { useModelSelectorContext } from "@/lib/model-selector-provider";
import { AgentState } from "@/lib/types";

type FlatData = Record<string, string>;
type NestedObject = Record<string, any>;

interface FolderStructure {
  [key: string]: string | FolderStructure;
}

interface GeneratedFile {
  path: string;
  content: string;
  file_type: string;
}

interface AgentResponse {
  generate: {
    _internal: {
      output: {
        contract: GeneratedFile;
        state: GeneratedFile;
        proto: GeneratedFile;
        reference: GeneratedFile;
        project: GeneratedFile;
        metadata: GeneratedFile[];
      };
    };
  };
}

function formatFlatObject(flatData: FlatData): FolderStructure {
  const nestedObject: FolderStructure = {};

  for (const [path, content] of Object.entries(flatData)) {
    const keys = path.split("/");
    let current = nestedObject;

    keys.forEach((key, index) => {
      if (index === keys.length - 1) {
        current[key] = content;
      } else {
        if (!current[key] || typeof current[key] === 'string') {
          current[key] = {};
        }
        current = current[key] as FolderStructure;
      }
    });
  }

  return nestedObject;
}

function MainContent() {
  const [folderStructure, setFolderStructure] = useState<FolderStructure>({});
  const [selectedFilesArray, setSelectedFilesArray] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [fileContent, setFileContent] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    setLoading(true);
    try {
      console.log('Sending request to generate code:', userMessage);
      
      const response = await fetch('/api/copilotkit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: userMessage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      console.log('Received response:', data);

      if (!data.generate?._internal?.output) {
        throw new Error('Invalid response format from agent');
      }

      setMessages(prev => [...prev, { role: 'assistant', content: 'I have generated the code based on your requirements. You can view the files in the explorer.' }]);

      const output = data.generate._internal.output;
      const allFiles = [
        output.contract,
        output.state,
        output.proto,
        output.reference,
        output.project,
        ...(output.metadata || []),
      ].filter(Boolean);

      const newFolderStructure = allFiles.reduce((acc, file) => {
        acc[file.path] = file.content;
        return acc;
      }, {} as FlatData);

      setFolderStructure(formatFlatObject(newFolderStructure));
      if (allFiles.length > 0) {
        const firstFile = allFiles[0].path;
        setSelectedFile(firstFile);
        setSelectedFilesArray([firstFile]);
        setFileContent(allFiles[0].content);
      }
    } catch (error) {
      console.error('Error generating code:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, there was an error generating the code. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderToggle = (path: string) => {
    setExpandedFolders((prev) => {
      const newExpandedFolders = new Set(prev);
      if (newExpandedFolders.has(path)) {
        newExpandedFolders.delete(path);
      } else {
        newExpandedFolders.add(path);
      }
      return newExpandedFolders;
    });
  };

  const getFileContent = (structure: FolderStructure, path: string): string => {
    const parts = path.split('/');
    let current: string | FolderStructure = structure;
    
    for (const part of parts) {
      if (typeof current === 'string') return current;
      current = current[part];
      if (!current) return '';
    }
    
    return typeof current === 'string' ? current : '';
  };

  const renderFolderStructure = (structure: FolderStructure, parentPath = "") => {
    const sortedKeys = Object.keys(structure).sort((a, b) => {
      const isAFolder = typeof structure[a] !== 'string';
      const isBFolder = typeof structure[b] !== 'string';
      if (isAFolder && !isBFolder) return -1;
      if (!isAFolder && isBFolder) return 1;
      return a.localeCompare(b);
    });

    return sortedKeys.map((key) => {
      const currentPath = parentPath ? `${parentPath}/${key}` : key;
      const isFolder = typeof structure[key] !== 'string';
      const isExpanded = expandedFolders.has(currentPath);

      if (isFolder) {
        return (
          <div key={currentPath}>
            <div
              onClick={() => handleFolderToggle(currentPath)}
              className="flex items-center gap-2 p-2 text-sm font-bold bg-gray-800 text-gray-300 cursor-pointer mb-1"
            >
              {isExpanded ? "▼" : "▶"}
              <svg
                stroke="currentColor"
                fill="currentColor"
                strokeWidth="0"
                viewBox="0 0 512 512"
                height="1em"
                width="1em"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="32"
                  d="M440 432H72a40 40 0 0 1-40-40V120a40 40 0 0 1 40-40h75.89a40 40 0 0 1 22.19 6.72l27.84 18.56a40 40 0 0 0 22.19 6.72H440a40 40 0 0 1 40 40v240a40 40 0 0 1-40 40zM32 192h448"
                ></path>
              </svg>
              {key}
            </div>
            {isExpanded && (
              <div className="pl-2 mb-1">
                {renderFolderStructure(structure[key] as FolderStructure, currentPath)}
              </div>
            )}
          </div>
        );
      } else {
        return (
          <div
            key={currentPath}
            onClick={() => {
              setSelectedFile(currentPath);
              setSelectedFilesArray((prev) =>
                prev.includes(currentPath) ? prev : [...prev, currentPath]
              );
              setFileContent(structure[key] as string);
            }}
            className={`flex items-center gap-2 p-2 pl-7 text-sm cursor-pointer rounded-md hover:bg-gray-800 ${
              selectedFile === currentPath
                ? "bg-gray-700 text-white"
                : "text-gray-300"
            }`}
          >
            <svg
              stroke="currentColor"
              fill="currentColor"
              strokewidthstroke-linejoin="0"
              viewBox="0 0 256 256"
              height="1em"
              width="1em"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M48,180c0,11,7.18,20,16,20a14.24,14.24,0,0,0,10.22-4.66A8,8,0,0,1,85.78,206.4,30.06,30.06,0,0,1,64,216c-17.65,0-32-16.15-32-36s14.35-36,32-36a30.06,30.06,0,0,1,21.78,9.6,8,8,0,0,1-11.56,11.06A14.24,14.24,0,0,0,64,160C55.18,160,48,169,48,180ZM216,88V224a8,8,0,0,1-16,0V96H152a8,8,0,0,1-8-8V40H56v72a8,8,0,0,1-16,0V40A16,16,0,0,1,56,24h96a8,8,0,0,1,5.66,2.34l56,56A8,8,0,0,1,216,88Zm-56-8h28.69L160,51.31Zm8,88v16h8a8,8,0,0,1,0,16h-8v8a8,8,0,0,1-16,0v-8H136v8a8,8,0,0,1-16,0v-8h-8a8,8,0,0,1,0-16h8V168h-8a8,8,0,0,1,0-16h8v-8a8,8,0,0,1,16,0v8h16v-8a8,8,0,0,1,16,0v8h8a8,8,0,0,1,0,16Zm-16,0H136v16h16Z"></path>
            </svg>
            {key}
          </div>
        );
      }
    });
  };

  return (
    <div className="flex h-screen bg-gray-900">
      <div className="flex-1 flex">
        <div className="w-80 flex flex-col">
          <h1 className="text-xl p-4 font-bold text-white">AElf Code Generator</h1>
          <p className="border-y px-2 py-2 border-gray-700 text-white text-[12px]">
            Files
          </p>
          <div className="flex-1 overflow-auto space-y-2 p-3">
            {renderFolderStructure(folderStructure)}
          </div>
        </div>

        <div className="flex-1 flex flex-col border-x border-gray-700">
          <header className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
            <div className="flex items-center space-x-4"></div>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" className="text-gray-400 hover:text-white">
                Deploy
              </Button>
            </div>
          </header>

          <div className="flex items-center">
            {selectedFilesArray.length > 0 &&
              selectedFilesArray.map((name: string, index) => (
                <div
                  className={`flex items-center justify-between gap-5 px-4 py-2 border border-gray-700 text-white text-[12px] cursor-pointer ${
                    selectedFile === name ? "bg-gray-800" : ""
                  }`}
                  key={index}
                  onClick={() => {
                    setSelectedFile(name);
                    const content = getFileContent(folderStructure, name);
                    if (content) setFileContent(content);
                  }}
                >
                  <p>{name}</p>
                  <p className="text-[10px]" onClick={() => {}}>
                    X
                  </p>
                </div>
              ))}
          </div>

          {selectedFile && (
            <div className="flex-1 p-4 file-result-container bg-gray-800">
              <MonacoEditor
                language="csharp"
                value={fileContent}
                theme="vs-dark"
                onChange={(value) => setFileContent(value as string)}
              />
            </div>
          )}
        </div>
      </div>

      <div className="w-[400px] flex flex-col border-l border-gray-700">
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-200'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-gray-200 rounded-lg p-3">
                Generating code...
              </div>
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Describe your smart contract requirements..."
              className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <Button 
              type="submit" 
              disabled={loading || !inputValue.trim()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Send
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Home() {
  return <MainContent />;
}
