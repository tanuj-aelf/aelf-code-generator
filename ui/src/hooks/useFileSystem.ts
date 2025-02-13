import { useState } from 'react';

interface FolderStructure {
  [key: string]: string | FolderStructure;
}

export const useFileSystem = () => {
  const [folderStructure, setFolderStructure] = useState<FolderStructure>({});
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [selectedFilesArray, setSelectedFilesArray] = useState<string[]>([]);
  const [fileContent, setFileContent] = useState<string>("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const handleFileSelect = (path: string) => {
    setSelectedFile(path);
    setSelectedFilesArray((prev) =>
      prev.includes(path) ? prev : [...prev, path]
    );
    
    // Get content from folder structure
    const content = getFileContent(folderStructure, path);
    if (content) setFileContent(content);
  };

  const handleFileClose = (path: string) => {
    const newArray = selectedFilesArray.filter(file => file !== path);
    setSelectedFilesArray(newArray);
    
    // If we're closing the currently selected file
    if (path === selectedFile) {
      // Select the last file in the remaining array, or clear selection if empty
      if (newArray.length > 0) {
        const lastFile = newArray[newArray.length - 1];
        setSelectedFile(lastFile);
        const content = getFileContent(folderStructure, lastFile);
        if (content) setFileContent(content);
      } else {
        setSelectedFile("");
        setFileContent("");
      }
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
    const parts = path.split("/");
    let current: string | FolderStructure = structure;

    for (const part of parts) {
      if (typeof current === "string") return current;
      current = current[part];
      if (!current) return "";
    }

    return typeof current === "string" ? current : "";
  };

  const updateFolderStructure = (newStructure: FolderStructure) => {
    setFolderStructure(newStructure);
  };

  return {
    folderStructure,
    selectedFile,
    selectedFilesArray,
    fileContent,
    expandedFolders,
    handleFileSelect,
    handleFileClose,
    handleFolderToggle,
    updateFolderStructure,
    setFileContent,
  };
}; 