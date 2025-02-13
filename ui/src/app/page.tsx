"use client";

import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { FileExplorer } from "@/components/file-explorer/FileExplorer";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { ChatWindow } from "@/components/chat";
import { useFileSystem } from "@/hooks/useFileSystem";
import { useChat } from "@/hooks/useChat";
import { AgentResponse } from "@/types";
import { motion, AnimatePresence } from "framer-motion"; // You'll need to install framer-motion
import { benifits } from "@/lib/constants";

const formatFlatObject = (flatData: Record<string, string>) => {
  const nestedObject: Record<string, any> = {};

  for (const [path, content] of Object.entries(flatData)) {
    const keys = path.split("/");
    let current = nestedObject;

    keys.forEach((key, index) => {
      if (index === keys.length - 1) {
        current[key] = content;
      } else {
        if (!current[key] || typeof current[key] === "string") {
          current[key] = {};
        }
        current = current[key] as Record<string, any>;
      }
    });
  }

  return nestedObject;
};

function MainContent() {
  const [hasCode, setHasCode] = useState(false);
  const {
    folderStructure,
    selectedFile,
    selectedFilesArray,
    fileContent,
    handleFileSelect,
    handleFileClose,
    expandedFolders,
    handleFolderToggle,
    updateFolderStructure,
    setFileContent,
  } = useFileSystem();

  const {
    messages,
    loading,
    inputValue,
    handleInputChange,
    handleSubmit,
  } = useChat({
    onSuccess: (data: AgentResponse) => {
      const output = data.generate._internal.output;
      const allFiles = [
        output.contract,
        output.state,
        output.proto,
        output.reference,
        output.project,
        ...(output.metadata || []),
      ].filter((file) => file.file_type && file.path);

      const newFolderStructure = allFiles.reduce((acc, file) => {
        acc[file.path] = file.content;
        return acc;
      }, {} as Record<string, string>);

      updateFolderStructure(formatFlatObject(newFolderStructure));

      // Select the first file by default
      if (allFiles.length > 0) {
        const firstFile = allFiles[0].path;
        handleFileSelect(firstFile);
        setHasCode(true); // Show the file explorer and editor
      }
    },
  });

  const handleDeploy = () => {
    console.log("Deploy clicked");
  };

  return (
    <MainLayout fullScreen={!hasCode}>
       <AnimatePresence mode="wait">
        {!hasCode ? (
          // Full-screen chat when no code is generated
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex-1 flex flex-col items-center justify-center min-h-screen bg-gray-900 p-6"
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="mb-8 text-center"
            >
              <h1 className="text-4xl font-bold text-white mb-4">
                AElf Code Generator
              </h1>
              <p className="text-gray-400 text-lg max-w-2xl">
                Generate smart contracts effortlessly using csharp language. 
                Describe your requirements or choose from our templates below.
              </p>
            </motion.div>

            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="w-full max-w-3xl bg-gray-800/50 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700"
            >
              <ChatWindow
                messages={messages}
                loading={loading}
                inputValue={inputValue}
                onInputChange={handleInputChange}
                onSubmit={handleSubmit}
                fullScreen
              />
            </motion.div>

            {/* Optional: Add some features or benefits section */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-12 grid grid-cols-3 gap-6 max-w-3xl"
            >
              {benifits.map((feature, index) => (
                <div
                  key={index}
                  className="text-center p-4 rounded-lg bg-gray-800/30 border border-gray-700"
                >
                  <div className="text-3xl mb-2">{feature.icon}</div>
                  <h3 className="text-white font-medium mb-1">{feature.title}</h3>
                  <p className="text-gray-400 text-sm">{feature.description}</p>
                </div>
              ))}
            </motion.div>
          </motion.div>
        ) : (
          // Regular layout when code is available
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex-1 flex"
          >
            {/* File Explorer Section */}
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="w-80 flex flex-col bg-gray-900 border-r border-gray-700"
            >
              <h1 className="text-xl p-4 font-bold text-white border-b border-gray-700">
                AElf Code Generator
              </h1>
              <div className="px-4 py-2 text-sm font-medium text-gray-400">
                Files
              </div>
              <FileExplorer
                structure={folderStructure}
                selectedFile={selectedFile}
                expandedFolders={expandedFolders}
                onFileSelect={handleFileSelect}
                onFolderToggle={handleFolderToggle}
              />
            </motion.div>

            {/* Editor Section */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex-1 flex flex-col border-x border-gray-700"
            >
              <CodeEditor
                files={selectedFilesArray}
                selectedFile={selectedFile}
                content={fileContent}
                onFileSelect={handleFileSelect}
                onFileClose={handleFileClose}
                onContentChange={setFileContent}
                onDeploy={handleDeploy}
              />
            </motion.div>

            {/* Chat Section */}
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              className="w-[400px] flex flex-col border-l border-gray-700"
            >
              <ChatWindow
                messages={messages}
                loading={loading}
                inputValue={inputValue}
                onInputChange={handleInputChange}
                onSubmit={handleSubmit}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </MainLayout>
  );
}

export default function Home() {
  return <MainContent />;
}