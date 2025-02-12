"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { CopilotChat } from "@copilotkit/react-ui";
import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import MonacoEditor from "@monaco-editor/react";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { useModelSelectorContext } from "@/lib/model-selector-provider";
import { AgentState } from "@/lib/types";

type FlatData = Record<string, string>;
type NestedObject = Record<string, any>;

function formatFlatObject(flatData: FlatData): NestedObject {
  const nestedObject: NestedObject = {};

  for (const [path, content] of Object.entries(flatData)) {
    const keys = path.split("/"); // Split the path into folders and file names
    let current = nestedObject;

    keys.forEach((key, index) => {
      if (index === keys.length - 1) {
        // Last key: assign content
        current[key] = content;
      } else {
        // Intermediate key: create nested object if it doesn't exist
        if (!current[key]) {
          current[key] = {};
        }
        current = current[key];
      }
    });
  }

  return nestedObject;
}

function MainContent() {
  const [folderStructure, setFolderStructure] = useState({});
  const [selectedFilesArray, setSelectedFilesArray] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [fileContent, setFileContent] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set()
  );
  const { model, agent } = useModelSelectorContext();
  const { run: runResearchAgent, state: agentState } = useCoAgent<AgentState>({
    name: agent,
    initialState: {
      model,
    },
  });

  console.log("agentState", agentState);

  const handleResearch = (query: string) => {
    runResearchAgent(() => {
      return new TextMessage({
        role: MessageRole.User,
        content: query,
      });
    });
  };

  // useCopilotAction(
  // {
  //   name: "aelf_code_generator",
  //   description: "Create a contract with all saperate files like cs, state, proto files and etc.",
  //       description: `Generate a smart contract project using Aelf blockchain in dotnet with the following folder structure:
  // src/
  // ├── Protobuf/
  // │   ├── contract/
  // │   │   └── {{SmartContract Name in small letter}}_contract.proto
  // │   ├── message/
  // │   │   └── {{SmartContract Name in small letter}}_message.proto
  // │   ├── reference/
  // │       └── acs12.proto
  // │
  // ├── {{SmartContract Name}}Contract.cs
  // ├── {{SmartContract Name}}ContractState.cs
  // └── {{SmartContract Name}}Contract.csproj`,
  // parameters: [
  //   {
  //     name: "generate",
  //     type: "object",
  //     // description: "Code for each file in the smart contract",
  //     required: true,
  //   },
  // ],
  // handler: async (data) => {
  //   console.log("data",data)
  // const { code } = data;
  // console.log("Generated Project Details", data);
  // const formattedObject = formatFlatObject(code as FlatData);
  // setFolderStructure(formattedObject);
  // if (Object.keys(code).length > 0) {
  //   const firstFile = Object.keys(code)[0];
  //   setSelectedFile(firstFile);
  //   setSelectedFilesArray([firstFile]);
  //   setFileContent(code[firstFile]);
  // }
  //     },
  //   },
  //   []
  // );

  const handleFolderToggle = (path: string) => {
    setExpandedFolders((prev) => {
      const newExpandedFolders = new Set(prev);
      if (newExpandedFolders.has(path)) {
        newExpandedFolders.delete(path); // Collapse the folder
      } else {
        newExpandedFolders.add(path); // Expand the folder
      }
      return newExpandedFolders;
    });
  };

  const renderFolderStructure = (structure: any, parentPath = "") => {
    // Separate folders and files for sorting
    const sortedKeys = Object.keys(structure).sort((a, b) => {
      const isAFolder = typeof structure[a] === "object";
      const isBFolder = typeof structure[b] === "object";
      if (isAFolder && !isBFolder) return -1; // Folders first
      if (!isAFolder && isBFolder) return 1; // Files later
      return a.localeCompare(b); // Alphabetical order
    });

    return sortedKeys.map((key) => {
      const currentPath = parentPath ? `${parentPath}/${key}` : key;
      const isFolder = typeof structure[key] === "object";
      const isExpanded = expandedFolders.has(currentPath);

      if (isFolder) {
        // Render folders
        return (
          <div key={currentPath}>
            <div
              onClick={() => handleFolderToggle(currentPath)}
              className="flex items-center gap-2 p-2 text-sm font-bold bg-gray-800 text-gray-300 cursor-pointer mb-1"
            >
              {isExpanded ? "▼" : "▶"} {/* Arrow icon for folder */}
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
                {renderFolderStructure(structure[key], currentPath)}
              </div>
            )}
          </div>
        );
      } else {
        // Render files
        return (
          <div
            key={currentPath}
            onClick={() => {
              setSelectedFile(currentPath);
              setSelectedFilesArray((prev) =>
                prev.includes(currentPath) ? prev : [...prev, currentPath]
              );
              setFileContent(structure[key]);
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
    <div className="flex h-screen bg-gray-900 main-content">
      <div className="w-80">
        <h1 className="text-xl p-4 font-bold text-white">
          AElf Code Generator
        </h1>
        <p className="border-y px-2 py-2 border-gray-700 text-white text-[12px]">
          Files
        </p>
        <div className="space-y-2 p-3">
          {renderFolderStructure(folderStructure)}
        </div>
      </div>
      <div className="flex-1 flex flex-col border-x border-gray-700">
        <header className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex items-center space-x-4"></div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              className="text-gray-400 hover:text-white"
              onClick={() =>
                handleResearch(
                  "Create a contract for the todo dapp with all saperate files like cs, state, proto files and etc."
                )
              }
            >
              Build
            </Button>
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
                  setFileContent(folderStructure[name]);
                }}
              >
                <p>{name}</p>
                <p className="text-[10px]" onClick={() => {}}>
                  X
                </p>
              </div>
            ))}
        </div>

        {/* {selectedFile && (
          <div className="flex-1 p-4 file-result-container bg-gray-800">
            <MonacoEditor
              language="csharp"
              value={fileContent}
              theme="vs-dark"
              onChange={(value) => setFileContent(value as string)}
            />
          </div>
        )} */}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="flex">
      <MainContent />
      <div
        className="w-[500px] h-screen"
        style={
          {
            "--copilot-kit-background-color": "#111827",
            "--copilot-kit-secondary-color": "rgb(31 41 55 / 1)",
            "--copilot-kit-secondary-contrast-color": "#FFFFFF",
            "--copilot-kit-primary-color": "rgb(31 41 55 / 1)",
            "--copilot-kit-contrast-color": "#FFFFFF",
            "--copilot-kit-separator-color": "#FFF3",
          } as any
        }
      >
        <CopilotChat
          className="h-full"
          instructions="I am an AI assistant specialized in helping you generate and understand code for the Aelf blockchain ecosystem. I can help you with smart contracts, dApps, and other blockchain-related development tasks."
          labels={{
            title: "AElf Assistant",
            initial: "How can I help you with your Aelf development today?",
          }}
        />
      </div>
    </div>
  );
}
