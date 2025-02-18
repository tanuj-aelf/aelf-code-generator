"use client";

import useSWR from "swr";
import { FileContent } from "./db";
import AElf from "aelf-sdk";
import { strFromU8, unzipSync } from "fflate";

const aelf = new AElf(
  new AElf.providers.HttpProvider("https://tdvw-test-node.aelf.io")
);

export function useShare(id?: string) {
  return useSWR<{ files?: FileContent[]; message?: string; success: boolean }>(
    id ? `get-share-${id}` : undefined,
    async () => {
      try {
        if (!id) {
          return { success: false, message: "Share Id is missing" };
        }
        const res = await fetch(`/api/playground/share/get/${id}`);

        const data = await res.arrayBuffer();

        const unzipped = unzipSync(Buffer.from(data));

        let files: FileContent[] = [];

        Object.entries(unzipped).forEach(([k, v]) => {
          files.push({
            path: k,
            contents: strFromU8(v),
          });
        });

        return { files, success: true };
      } catch (err) {
        let error = "An error occurred.";
        if (err instanceof Error) {
          error = err.message;

          if (error === "invalid zip data")
            error = "This share ID is not available.";
        }

        return { message: error, success: false };
      }
    }
  );
}
