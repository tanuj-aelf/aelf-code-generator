interface EditorTabsProps {
  files: string[];
  selectedFile: string;
  onFileSelect: (file: string) => void;
  onFileClose: (file: string) => void;
}

export const EditorTabs = ({
  files,
  selectedFile,
  onFileSelect,
  onFileClose,
}: EditorTabsProps) => {
  return (
    <div className="flex items-center">
      {files.map((name: string, index) => (
        <div
          className={`flex items-center justify-between gap-5 px-4 py-2 border border-gray-700 text-white text-[12px] cursor-pointer ${
            selectedFile === name ? "bg-gray-800" : ""
          }`}
          key={index}
          onClick={() => onFileSelect(name)}
        >
          <p>{name}</p>
          <button
            className="hover:bg-gray-700 rounded p-1 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onFileClose(name);
            }}
          >
            <svg
              className="w-3 h-3 text-gray-400 hover:text-white transition-colors"
              viewBox="0 0 12 12"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M9 3L3 9M3 3L9 9"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}; 