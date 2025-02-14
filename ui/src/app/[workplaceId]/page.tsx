"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { FileExplorer } from "@/components/file-explorer/FileExplorer";
import { CodeEditor } from "@/components/editor/CodeEditor";
import { ChatWindow } from "@/components/chat";
import { useChat } from "@/hooks/useChat";
import { AgentResponse } from "@/types";
import { db, FileContent } from "@/db/db";
import { useWorkspaces } from "@/hooks/useWorkspaces";
import { Header } from "@/components/header";
import { use, useEffect } from "react";
import { useContract } from "@/context/ContractContext";

interface PageProps {
  params: Promise<{ workplaceId: string }>;
}

export default function Workplace({ params }: PageProps) {
  const { workplaceId } = use(params);
  const { data: workspaces } = useWorkspaces();
  const {
    files,
    selectedFile,
    fileContent,
    handleFileSelect,
    handleFileClose,
    expandedFolders,
    handleFolderToggle,
    updateFiles,
    setFileContent,
  } = useContract();

  const getFiles = async (workplaceId: string) => {
    const files = await db.files.filter((file) =>
      file.path.startsWith("/workspace/" + workplaceId + "/")
    );
    const filesArray = await files.toArray();
    const allFiles = filesArray.map((i) => {
        const decodedPath = decodeURIComponent(i.path.replace(`/workspace/${workplaceId}/`, ""));
        return {
            path: decodedPath,
            contents: i.contents
        }
    });
    updateFiles(allFiles);
  };

  useEffect(() => {
    getFiles(workplaceId);
  }, [workplaceId]);

  const { messages, loading, inputValue, handleInputChange, handleSubmit } =
    useChat({
      onSuccess: async (data: AgentResponse) => {
        // Convert the API response to our FileContent format
        const allFiles = [
          data.generate._internal.output.contract,
          data.generate._internal.output.state,
          data.generate._internal.output.proto,
          data.generate._internal.output.reference,
          data.generate._internal.output.project,
          ...(data.generate._internal.output.metadata || []),
        ]
          .filter(
            (
              file
            ): file is { path: string; content: string; file_type: string } =>
              Boolean(file?.path && file?.content)
          )
          .map(
            (file): FileContent => ({
              path: file.path,
              contents: file.content,
            })
          );

        // Update files in the file system
        updateFiles(allFiles);
        await db.workspaces.add({
          name: `project-${(workspaces?.length ?? 0) + 1}`,
          template: "",
          dll: "",
        });

        await db.files.bulkAdd(
          allFiles.map(({ path, contents }) => ({
            path: `/workspace/project/${path}`,
            contents,
          }))
        );

        // Select the first file by default
        if (allFiles.length > 0) {
          const firstFile = allFiles[0].path;
          handleFileSelect(firstFile);
        }
      },
    });

  const handleDeploy = () => {
    console.log("Deploy clicked");
  };

  return (
    <MainLayout fullScreen={false} className={"pt-[70px]"}>
      <Header />
      <div className="flex-1 flex">
        <div className="w-[320px] flex flex-col bg-gray-900 border-r border-gray-700">
          <h1 className="text-xl p-4 font-bold text-white border-b border-gray-700">
            AElf Code Generator
          </h1>
          <div className="px-4 py-2 text-sm font-medium text-gray-400">
            Files
          </div>
          <FileExplorer
            files={files}
            selectedFile={selectedFile}
            expandedFolders={expandedFolders}
            onFileSelect={handleFileSelect}
            onFolderToggle={handleFolderToggle}
          />
        </div>

        {/* Editor Section */}
        <div className="editor-container flex-1 flex flex-col border-x border-gray-700">
          <CodeEditor
            files={files.map((file) => file.path)}
            selectedFile={selectedFile}
            content={fileContent}
            onFileSelect={handleFileSelect}
            onFileClose={handleFileClose}
            onContentChange={setFileContent}
            onDeploy={handleDeploy}
            workplaceId={workplaceId}
          />
        </div>

        {/* Chat Section */}
        <div className="w-[400px] flex flex-col border-l border-gray-700">
          <ChatWindow
            messages={messages}
            loading={loading}
            inputValue={inputValue}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          />
        </div>
      </div>
    </MainLayout>
  );
}
