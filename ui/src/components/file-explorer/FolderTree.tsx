interface FolderTreeProps {
  structure: FolderStructure;
  expandedFolders: Set<string>;
  selectedFile: string;
  onFileSelect: (path: string) => void;
  onFolderToggle: (path: string) => void;
}

export const FolderTree = ({
  structure,
  expandedFolders,
  selectedFile,
  onFileSelect,
  onFolderToggle,
}: FolderTreeProps) => {
  const renderFolderStructure = (
    structure: FolderStructure,
    parentPath = ""
  ) => {
    const sortedKeys = Object.keys(structure).sort((a, b) => {
      const isAFolder = typeof structure[a] !== "string";
      const isBFolder = typeof structure[b] !== "string";
      if (isAFolder && !isBFolder) return -1;
      if (!isAFolder && isBFolder) return 1;
      return a.localeCompare(b);
    });

    return sortedKeys.map((key) => {
      const currentPath = parentPath ? `${parentPath}/${key}` : key;
      const isFolder = typeof structure[key] !== "string";
      const isExpanded = expandedFolders.has(currentPath);

      if (isFolder) {
        return (
          <FolderItem
            key={currentPath}
            path={currentPath}
            isExpanded={isExpanded}
            onToggle={onFolderToggle}
          >
            {isExpanded && (
              <div className="pl-6 border-l border-gray-700 ml-3">
                {renderFolderStructure(
                  structure[key] as FolderStructure,
                  currentPath
                )}
              </div>
            )}
          </FolderItem>
        );
      }

      return (
        <FileItem
          key={currentPath}
          path={currentPath}
          isSelected={selectedFile === currentPath}
          onClick={() => onFileSelect(currentPath)}
        />
      );
    });
  };

  return (
    <div className="flex-1 overflow-auto px-2 py-1">
      {renderFolderStructure(structure)}
    </div>
  );
}; 