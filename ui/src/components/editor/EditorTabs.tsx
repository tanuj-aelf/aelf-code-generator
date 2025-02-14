import { useContract } from "@/context/ContractContext";

export const EditorTabs = () => {
  const { selectedFilesArray, selectedFile, handleFileSelect, handleFileClose } = useContract();

  // Helper function to get the file name from path
  const getFileName = (path: string) => {
    return path.split('/').pop() || path;
  };

  // Helper function to get file type icon
  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'cs':
        return (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11.5,15.97L11.91,18.41C11.65,18.55 11.23,18.68 10.67,18.8C10.1,18.93 9.43,19 8.66,19C6.45,18.96 4.79,18.3 3.68,17.04C2.56,15.77 2,14.16 2,12.21C2.05,9.9 2.72,8.13 4,6.89C5.32,5.64 7.23,5 9.74,5C11.05,5 12.09,5.07 12.85,5.21L13.13,7.94C12.51,7.81 11.8,7.75 11,7.75C9.47,7.79 8.89,8.22 8.26,9.03C7.63,9.84 7.31,10.9 7.31,12.21C7.31,13.5 7.62,14.56 8.24,15.38C8.85,16.2 9.93,16.62 11.46,16.62C11.8,16.62 12.34,16.57 13.08,16.46L12.84,14.06L9.61,14.06L9.61,11.71H15.97L16.45,13.53L16.45,15.97H11.5Z" />
          </svg>
        );
      case 'proto':
        return (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.89,3L14.85,3.4L11.11,21L9.15,20.6L12.89,3M19.59,12L16,8.41V5.58L22.42,12L16,18.41V15.58L19.59,12M1.58,12L8,5.58V8.41L4.41,12L8,15.58V18.41L1.58,12Z" />
          </svg>
        );
      case 'csproj':
        return (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6,2A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2H6M6,4H13V9H18V20H6V4M8,12V14H16V12H8M8,16V18H13V16H8Z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z" />
          </svg>
        );
    }
  };

  return (
    <div className="flex-1 flex overflow-x-auto bg-gray-900 border-b border-gray-700">
      {selectedFilesArray.map((file) => (
        <div
          key={file}
          className={`group flex items-center gap-2 px-4 py-2 border-r border-gray-700 cursor-pointer
            hover:bg-gray-800 transition-colors duration-150 min-w-0
            ${selectedFile === file ? "bg-gray-800 text-white" : "text-gray-400"}
          `}
          onClick={() => handleFileSelect(file)}
        >
          <span className="text-gray-400">
            {getFileIcon(file)}
          </span>
          <span className="truncate text-sm">
            {getFileName(file)}
          </span>
          <button
            className={`p-1 rounded-md opacity-0 group-hover:opacity-100
              hover:bg-gray-700 transition-all duration-150
              ${selectedFile === file ? "text-gray-300" : "text-gray-500"}
            `}
            onClick={(e) => {
              e.stopPropagation();
              handleFileClose(file);
            }}
          >
            <svg
              className="w-3 h-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}; 