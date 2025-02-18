"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatWindow } from "@/components/chat";
import { motion, AnimatePresence } from "framer-motion";
import { db } from "@/data/db";
import { benifits } from "@/lib/constants";
import { Header } from "@/components/header";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader } from "@/components/ui/icons";
import { useEffect } from "react";
import { useShare } from "@/data/client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Home() {
  const searchParams = useSearchParams();
  const shareId = searchParams.get("share");
  const { data, isLoading } = useShare(shareId || "");

  const router = useRouter();

  useEffect(() => {
    if (shareId) {
      const importWorkspace = async () => {
        if (!data?.files || !shareId) return;

        const existing = await db.workspaces.get(shareId);

        if (existing) {
          router.push(`/${shareId}`);
        } else {
          await db.workspaces.add({
            name: shareId,
            template: shareId,
            dll: "",
          });

          await db.files.bulkAdd(
            data.files.map(({ path, contents }) => ({
              path: `/workspace/${shareId}/${path}`,
              contents,
            }))
          );
          router.push(`/${shareId}`);
        }
      };

      importWorkspace();
    }
  }, [shareId, data?.files]);

  if (shareId) {
    if (data?.success === false) {
      return (
        <Dialog open onOpenChange={() => router.push("/")}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Error</DialogTitle>
              <DialogDescription>{data.message}</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
    }
    if (isLoading) {
      return (
        <MainLayout fullScreen>
          <div className="flex h-screen w-full items-center justify-center">
            <h3 className="text-white flex items-center gap-2 text-sm bg-gray-800 py-3 px-7 rounded-full">
              <Loader /> Getting Shared Details...
            </h3>
          </div>
        </MainLayout>
      );
    }
  }

  return (
    <MainLayout fullScreen={true} className={"pt-5"}>
      <Header />
      <AnimatePresence mode="wait">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="flex-1 flex flex-col items-center justify-center min-h-screen bg-gray-900 p-6 pt-20 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900 overflow-hidden"
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
            <ChatWindow fullScreen />
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
