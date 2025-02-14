import { useState } from 'react';
import { FileContent } from '@/db/db';

export const useFileSystem = () => {
  const [files, setFiles] = useState<FileContent[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [selectedFilesArray, setSelectedFilesArray] = useState<string[]>([]);
  const [fileContent, setFileContent] = useState<string>("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const handleFileSelect = (path: string) => {
    setSelectedFile(path);
    setSelectedFilesArray((prev) =>
      prev.includes(path) ? prev : [...prev, path]
    );
    
    // Get content from files array
    const file = files.find(f => f.path === path);
    if (file) setFileContent(file.contents);
  };

  const handleFileClose = (path: string) => {
    const newArray = selectedFilesArray.filter(file => file !== path);
    setSelectedFilesArray(newArray);
    
    if (path === selectedFile) {
      if (newArray.length > 0) {
        const lastFile = newArray[newArray.length - 1];
        setSelectedFile(lastFile);
        const file = files.find(f => f.path === lastFile);
        if (file) setFileContent(file.contents);
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

  const updateFiles = (newFiles: FileContent[]) => {
    setFiles(newFiles);
  };

  return {
    files,
    selectedFile,
    selectedFilesArray,
    fileContent,
    expandedFolders,
    handleFileSelect,
    handleFileClose,
    handleFolderToggle,
    updateFiles,
    setFileContent,
  };
}; 