import { FileContent } from "@/db/db";
import { FileIcon } from "./FileIcon";

interface FileExplorerProps {
  files: FileContent[];
  selectedFile: string;
  expandedFolders: Set<string>;
  onFileSelect: (path: string) => void;
  onFolderToggle: (path: string) => void;
}

export const FileExplorer = ({
  files,
  selectedFile,
  expandedFolders,
  onFileSelect,
  onFolderToggle,
}: FileExplorerProps) => {
  // Convert flat file list to folder structure
  const createFolderStructure = (files: FileContent[]) => {
    const structure: { [key: string]: any } = {};
    
    files.forEach(file => {
      const parts = file.path.split('/');
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

  const renderFolderStructure = (
    structure: any,
    parentPath = ""
  ) => {
    const sortedKeys = Object.keys(structure).sort((a, b) => {
      const isAFolder = typeof structure[a] === 'object';
      const isBFolder = typeof structure[b] === 'object';
      if (isAFolder && !isBFolder) return -1;
      if (!isAFolder && isBFolder) return 1;
      return a.localeCompare(b);
    });

    return sortedKeys.map((key) => {
      const currentPath = parentPath ? `${parentPath}/${key}` : key;
      const isFolder = typeof structure[key] === 'object';
      const isExpanded = expandedFolders.has(currentPath);

      if (isFolder) {
        return (
          <div key={currentPath} className="group">
            <div
              onClick={() => onFolderToggle(currentPath)}
              className="flex items-center gap-2 p-2 text-sm font-medium text-gray-300 cursor-pointer hover:bg-gray-800 rounded-md transition-colors duration-150 group-hover:text-white"
            >
              <span 
                className="inline-flex items-center justify-center w-4 h-4 transition-transform duration-200" 
                style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
              >
                <svg
                  width="6"
                  height="10"
                  viewBox="0 0 6 10"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M1 9L5 5L1 1"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <FileIcon type="folder" />
              <span className="truncate">{key}</span>
            </div>
            {isExpanded && (
              <div className="pl-6 border-l border-gray-700 ml-3">
                {renderFolderStructure(structure[key], currentPath)}
              </div>
            )}
          </div>
        );
      }

      return (
        <div
          key={currentPath}
          onClick={() => onFileSelect(currentPath)}
          className={`flex items-center gap-2 p-2 text-sm cursor-pointer rounded-md transition-colors duration-150
            ${
              selectedFile === currentPath
                ? "bg-blue-600/20 text-blue-400"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            }`}
        >
          <FileIcon type="file" />
          <span className="truncate">{key}</span>
        </div>
      );
    });
  };

  const folderStructure = createFolderStructure(files);

  return (
    <div className="flex-1 overflow-auto px-2 py-1">
      {renderFolderStructure(folderStructure)}
    </div>
  );
}; 