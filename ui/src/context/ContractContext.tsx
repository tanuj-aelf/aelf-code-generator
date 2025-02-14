"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { FileContent } from '@/db/db';

interface ContractContextType {
  files: FileContent[];
  selectedFile: string;
  fileContent: string;
  expandedFolders: Set<string>;
  selectedFilesArray: string[];
  handleFileSelect: (path: string) => void;
  handleFileClose: (path: string) => void;
  handleFolderToggle: (path: string) => void;
  updateFiles: (newFiles: FileContent[]) => void;
  setFileContent: (content: string) => void;
}

const ContractContext = createContext<ContractContextType | undefined>(undefined);

export const ContractProvider = ({ children }: { children: ReactNode }) => {
  const [files, setFiles] = useState<FileContent[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [fileContent, setFileContent] = useState<string>("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedFilesArray, setSelectedFilesArray] = useState<string[]>([]);

  const handleFileSelect = (path: string) => {
    if (!selectedFilesArray.includes(path)) {
      setSelectedFilesArray((prev) => [...prev, path]);
    }
    setSelectedFile(path);
    const file = files.find(f => f.path === path);
    if (file) setFileContent(file.contents);
  };

  const handleFileClose = (path: string) => {
    setSelectedFilesArray((prev) => prev.filter(file => file !== path));
    
    if (path === selectedFile) {
      const newArray = selectedFilesArray.filter(file => file !== path);
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

  return (
    <ContractContext.Provider value={{
      files,
      selectedFile,
      fileContent,
      expandedFolders,
      selectedFilesArray,
      handleFileSelect,
      handleFileClose,
      handleFolderToggle,
      updateFiles,
      setFileContent,
    }}>
      {children}
    </ContractContext.Provider>
  );
};

export const useContract = () => {
  const context = useContext(ContractContext);
  if (!context) {
    throw new Error("useContract must be used within a ContractProvider");
  }
  return context;
}; 