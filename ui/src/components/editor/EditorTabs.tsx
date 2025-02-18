import { useContract } from "@/context/ContractContext";
import { getFileIcon, getFileName } from "@/lib/file";

export const EditorTabs = () => {
  const {
    selectedFilesArray,
    selectedFile,
    handleFileSelect,
    handleFileClose,
  } = useContract();
  return (
    selectedFile && (
      <div className="flex-1 flex overflow-x-auto bg-gray-900 border-b border-gray-700">
        {selectedFilesArray.map((file) => (
          <div
            key={file}
            className={`group flex items-center gap-2 pl-3 pr-2 py-2 border-r border-gray-700 cursor-pointer
            hover:bg-gray-800 transition-colors duration-150 min-w-0
            ${
              selectedFile === file ? "bg-gray-800 text-white" : "text-gray-400"
            }
          `}
            onClick={() => handleFileSelect(file)}
          >
            <span className="text-gray-400">{getFileIcon(file)}</span>
            <span className="truncate text-sm">{getFileName(file)}</span>
            <button
              className={`p-1 rounded-md
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
    )
  );
};
