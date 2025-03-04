import { usePathname, useSearchParams } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import { saveAs } from "file-saver";

import { db, FileContent } from "@/data/db";
import { fileContentToZip } from "@/lib/file-content-to-zip";
import { useWallet } from "@/data/wallet";
import { AuditType, uploadContractCode } from "@/data/audit";
import { Message } from "@copilotkit/runtime-client-gql";

export function useCliCommands() {
  const workspaceName = usePathname().replace("/", "");
  const wallet = useWallet();
  const searchParams = useSearchParams();

  const buildService = async (files: FileContent[]) => {
    const zippedData = fileContentToZip(files);

    const formData = new FormData();
    const filePath = uuidv4() + ".zip";
    formData.append(
      "contractFiles",
      new File([zippedData], filePath, { type: "application/zip" }),
      filePath
    );

    const requestInit: RequestInit = {
      method: "POST",
      body: formData,
      redirect: "follow",
    };

    const response = await fetch("/api/playground/build", requestInit);

    if (!response.ok) {
      const { message } = await response.json();
      throw new Error(message);
    }

    const content = await response.text();

    if (
      content.includes("Determining projects to restore") ||
      content.includes("file found") ||
      content.includes("Build FAILED")
    ) {
      return { dll: "", success: false, message: content };
    }

    return { dll: content, success: true, message: "Build Success" };
  };

  const testService = async (files: FileContent[]) => {
    const zippedData = fileContentToZip(files);

    const formData = new FormData();
    const filePath = uuidv4() + ".zip";
    formData.append(
      "contractFiles",
      new File([zippedData], filePath, { type: "application/zip" }),
      filePath
    );

    const requestInit: RequestInit = {
      method: "POST",
      body: formData,
      redirect: "follow",
    };

    const response = await fetch("/api/playground/test", requestInit);

    return { message: await response.text() };
  };

  const createShare = async (files: FileContent[]) => {
    const zippedData = fileContentToZip(files);

    const formData = new FormData();
    const filePath = uuidv4() + ".zip";
    formData.append(
      "file",
      new File([zippedData], filePath, { type: "application/zip" }),
      filePath
    );

    const requestInit: RequestInit = {
      method: "POST",
      body: formData,
      redirect: "follow",
    };

    const response = await fetch(`/api/playground/share/create`, requestInit);

    return await response.json();
  };

  const actions = {
    audit: async (auditType: AuditType) => {
      const start = `/workspace/${workspaceName}/`;
      const files = (
        await db.files.filter((file) => file.path.startsWith(start)).toArray()
      )
        .map((file) => ({
          path: decodeURIComponent(file.path.replace(start, "")),
          contents: file.contents,
        }))
        .filter((i) => i.path.startsWith("src"));

      try {
        const codeHash = await uploadContractCode(auditType, files);

        if (!wallet) return;

        const params = new URLSearchParams(searchParams);
        params.set("auditId", codeHash);
        params.set("auditType", auditType);

        const { TransactionId } = await wallet.auditTransfer(codeHash);

        return {
          success: true,
          codeHash: codeHash,
          auditType: auditType,
          transactionId: TransactionId,
          message: "",
        };
      } catch (err) {
        return {
          success: false,
          message: err instanceof Error ? err.message : "Something Went Wrong",
        };
      }
    },
    build: async () => {
      if (typeof workspaceName !== "string")
        throw new Error("id is not string");
      await db.workspaces.update(workspaceName, {
        dll: undefined,
      });
      const start = `/workspace/${workspaceName}/`;
      const files = (
        await db.files.filter((file) => file.path.startsWith(start)).toArray()
      )
        .map((file) => ({
          path: decodeURIComponent(file.path.replace(start, "")),
          contents: file.contents,
        }))
        .filter((i) => i.path.startsWith("src"));
      try {
        let dll: string | undefined;
        const buildResult = await buildService(files);
        if (buildResult.success && buildResult.dll) {
          if (typeof dll === "string") {
            await db.workspaces.update(workspaceName, { dll });
            return { success: true, message: "Build successful." };
          }
        } {
          return { success: false, message: buildResult.message };
        }
      } catch (err) {
        let message;
        if (err instanceof Error) {
          message = err.message;
        } else {
          message = "Build failed";
        }
        return { success: false, message: message };
      }
    },
    deploy: async () => {
      if (typeof workspaceName !== "string") {
        return {
          success: false,
          message: `Workspace ${workspaceName} not found.`,
        };
      }
      const { dll, template } = (await db.workspaces.get(workspaceName)) || {};
      if (!dll) {
        return { success: false, message: "Contract not built." };
      }
      if (!wallet) {
        return { success: false, message: "Wallet not ready." };
      }
      const { TransactionId } = await wallet.deploy(
        dll,
        template === "solidity" ? 1 : 0
      );

      return { success: true, message: TransactionId };
    },
    exportProject: async () => {
      if (typeof workspaceName !== "string") {
        throw new Error("id is not string");
      }
      const start = `/workspace/${workspaceName}/`;
      const files = (
        await db.files.filter((file) => file.path.startsWith(start)).toArray()
      ).map((file) => ({
        path: decodeURIComponent(file.path.replace(start, "")),
        contents: file.contents,
      }));

      const zip = fileContentToZip(files);
      const file = new File(
        [zip],
        `${workspaceName?.split("/")?.pop() || "export"}.zip`,
        {
          type: "data:application/octet-stream;base64,",
        }
      );
      saveAs(file);
    },
    test: async () => {
      if (typeof workspaceName !== "string") {
        throw new Error("id is not string");
      }

      const start = `/workspace/${workspaceName}/`;

      const files = (
        await db.files.filter((file) => file.path.startsWith(start)).toArray()
      ).map((file) => ({
        path: decodeURIComponent(file.path.replace(start, "")),
        contents: file.contents,
      }));

      try {
        const { message } = await testService(files);

        return message;
      } catch (err) {
        if (err instanceof Error) {
          return err.message;
        } else {
          return "Something went wrong!";
        }
      }
    },
    share: async () => {
      if (typeof workspaceName !== "string")
        throw new Error("id is not string");
      const start = `/workspace/${workspaceName}/`;
      const files = (
        await db.files.filter((file) => file.path.startsWith(start)).toArray()
      ).map((file) => ({
        path: decodeURIComponent(file.path.replace(start, "")),
        contents: file.contents,
      }));

      try {
        const { id } = await createShare(files);

        if (!id) throw new Error("error");

        return {
          success: true,
          link: `${window.location.origin}?share=${id}`,
          message: "",
        };
      } catch (err) {
        return {
          success: false,
          link: "",
          message:
            err instanceof Error
              ? err.message?.trim() ||
                "There was an error generating the share link. Please try again later."
              : "Something went wrong!",
        };
      }
    },
  };

  return actions;
}
