"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatWindow } from "@/components/chat";
import { useChat } from "@/hooks/useChat";
import { AgentResponse } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { db, FileContent } from "@/db/db";
import { benifits } from "@/lib/constants";
import { useWorkspaces } from "@/hooks/useWorkspaces";
import { Header } from "@/components/header";
import { useContract } from "@/context/ContractContext";
import { useRouter } from "next/navigation";

export default function Home() {
  const { data: workspaces } = useWorkspaces();
  const { handleFileSelect, updateFiles } = useContract();
  const router = useRouter();
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

        const projectName = `project-${(workspaces?.length ?? 0) + 1}`;

        await db.workspaces.add({
          name: projectName,
          template: "",
          dll: "",
        });

        await db.files.bulkAdd(
          allFiles.map(({ path, contents }) => ({
            path: `/workspace/${projectName}/${path}`,
            contents,
          }))
        );

        router.push(`/${projectName}`);

        // Select the first file by default
        if (allFiles.length > 0) {
          const firstFile = allFiles[0].path;
          handleFileSelect(firstFile);
        }
      },
    });

  return (
    <MainLayout fullScreen={true} className={"pt-5"}>
      <Header />
      <AnimatePresence mode="wait">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="flex-1 flex flex-col items-center justify-center min-h-screen bg-gray-900 p-6 pt-20"
        >
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="mb-8 text-center"
          >
            <p className="text-gray-400 text-lg max-w-2xl">
              Generate smart contracts effortlessly using C# language. Describe
              your requirements or choose from our templates below.
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
      </AnimatePresence>
    </MainLayout>
  );
}
