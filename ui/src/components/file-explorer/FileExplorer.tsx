import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { mutate } from "swr";

import { useContract } from "@/context/ContractContext";
import { db, FileContent } from "@/data/db";
import { FolderIcon, getFileIcon } from "@/lib/file";
import { AddFile, AddFolder, Collapse, ExpandableIcon } from "../ui/icons";
import { Button } from "../ui/button";
import { FileContextMenu, FolderContextMenu, IAction } from "./context-menu";
import Rename from "./rename";
import Delete from "./delete";
import NewFile from "./new-file";

export const FileExplorer = () => {
  const workspaceName = usePathname();
  const workplaceId = workspaceName.replace("/", "");
  const getFiles = useRefreshFileExplorer();
  const {
    files,
    selectedFile,
    expandedFolders,
    handleFileSelect,
    handleFolderToggle,
    handleCollapseFolder,
  } = useContract();

  const [state, setState] = useState<{
    showRename: boolean;
    showDelete: boolean;
    showAdd: boolean;
    type: "folder" | "file" | undefined;
    path: string;
  }>({
    showRename: false,
    showDelete: false,
    showAdd: false,
    type: undefined,
    path: "",
  });

  const handleClick = (
    action: IAction,
    path: string,
    type: "folder" | "file"
  ) => {
    switch (action) {
      case IAction.DELETE:
        setState((prev) => ({
          ...prev,
          showDelete: true,
          path: path,
          type: type,
        }));
        break;
      case IAction.RENAME:
        setState((prev) => ({
          ...prev,
          showRename: true,
          path: path,
          type: type,
        }));
        break;
      case IAction.NEW_FILE:
        setState((prev) => ({
          ...prev,
          showAdd: true,
          path: path ?? `${path}/`,
          type: type,
        }));
        break;
      case IAction.NEW_FOLDER:
        setState((prev) => ({
          ...prev,
          showAdd: true,
          path: path,
          type: type,
        }));
        break;
    }
  };

  useEffect(() => {
    getFiles();
  }, [workplaceId]);

  // Convert flat file list to folder structure
  const createFolderStructure = (files: FileContent[]) => {
    const structure: { [key: string]: any } = {};

    files.forEach((file) => {
      const parts = file.path.split("/");
      let current = structure;

      // Create nested folders
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (!current[part]) {
          current[part] = {};
        }
        current = current[part];
      }

      // Add file at the end
      const fileName = parts[parts.length - 1];
      current[fileName] = file.contents;
    });

    return structure;
  };

  const renderFolderStructure = (structure: any, parentPath = "") => {
    const sortedKeys = Object.keys(structure).sort((a, b) => {
      const isAFolder = typeof structure[a] === "object";
      const isBFolder = typeof structure[b] === "object";
      if (isAFolder && !isBFolder) return -1;
      if (!isAFolder && isBFolder) return 1;
      return a.localeCompare(b);
    });

    return sortedKeys.map((key) => {
      const currentPath = parentPath ? `${parentPath}/${key}` : key;
      const isFolder = typeof structure[key] === "object";
      const isExpanded = expandedFolders.has(currentPath);

      if (isFolder) {
        return (
          <FolderContextMenu
            handleClick={(action) => handleClick(action, currentPath, "folder")}
            key={currentPath}
          >
            <div className="group mb-1">
              <div
                onClick={() => handleFolderToggle(currentPath)}
                className="flex items-center gap-2 p-2 text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-800 rounded-md transition-colors duration-150 group-hover:text-white"
              >
                <ExpandableIcon isExpanded={isExpanded} />
                <FolderIcon />
                <span className="truncate">{key}</span>
              </div>
              {isExpanded && (
                <div className="pl-6 border-l border-gray-700 ml-3">
                  {renderFolderStructure(structure[key], currentPath)}
                </div>
              )}
            </div>
          </FolderContextMenu>
        );
      }

      return (
        <FileContextMenu
          handleClick={(action) => handleClick(action, currentPath, "file")}
          key={currentPath}
        >
          <div
            onClick={() => handleFileSelect(currentPath)}
            className={`flex items-center gap-2 p-2 text-sm cursor-pointer rounded-md transition-colors duration-150 mb-1
            ${
              selectedFile === currentPath
                ? "bg-gray-800 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            }`}
          >
            {getFileIcon(key)}
            <span className="truncate">{key}</span>
          </div>
        </FileContextMenu>
      );
    });
  };

  const folderStructure = createFolderStructure(files);

  return (
    <div className="w-[320px] flex flex-col bg-gray-900 border-r border-gray-700">
      <div className="flex items-center justify-between pr-2 border-b border-gray-700">
        <h3 className="text-xl p-4 font-bold text-white truncate text-ellipsis">{workplaceId}</h3>
        <div className="flex items-center gap-1">
          <Button
            className="h-8 px-2 text-white"
            variant="ghost"
            onClick={() => handleClick(IAction.NEW_FILE, "", "file")}
          >
            <AddFile />
          </Button>
          {/* <Button className="h-8 px-2 text-white" variant="ghost">
            <AddFolder />
          </Button> */}
          <Button
            className="h-8 px-2 text-white"
            variant="ghost"
            onClick={handleCollapseFolder}
          >
            <Collapse />
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-auto px-1 py-2">
        {renderFolderStructure(folderStructure)}
      </div>
      <Rename
        type={state.type}
        path={state.path}
        isOpen={state.showRename}
        setIsOpen={() => {
          setState((prev) => ({
            ...prev,
            showRename: false,
            path: "",
            type: undefined,
          }));
        }}
      />
      <Delete
        type={state.type}
        path={state.path}
        isOpen={state.showDelete}
        setIsOpen={() =>
          setState((prev) => ({
            ...prev,
            showDelete: false,
            path: "",
            type: undefined,
          }))
        }
      />
      <NewFile
        defaultPath={state.path}
        isOpen={state.showAdd}
        setIsOpen={() =>
          setState((prev) => ({
            ...prev,
            showAdd: false,
          }))
        }
      />
    </div>
  );
};

export const useRefreshFileExplorer = () => {
  const workspaceName = usePathname();
  const workplaceId = workspaceName.replace("/", "");
  const { updateFiles } = useContract();

  const getFiles = async () => {
    const files = await db.files.filter((file) =>
      file.path.startsWith("/workspace/" + workplaceId + "/")
    );
    const filesArray = await files.toArray();
    const allFiles = filesArray.map((i) => {
      const decodedPath = decodeURIComponent(
        i.path.replace(`/workspace/${workplaceId}/`, "")
      );
      return {
        path: decodedPath,
        contents: i.contents,
      };
    });
    updateFiles(allFiles);
  };

  return getFiles;
};
