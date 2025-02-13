import { INITIAL_SUGGESTIONS } from "@/lib/constants";

interface ChatSuggestionsProps {
  onSuggestionClick: (prompt: string) => void;
  fullScreen?: boolean;
}

export const ChatSuggestions = ({ onSuggestionClick, fullScreen = false }: ChatSuggestionsProps) => {
  return (
    <div className={`
      flex-1 p-4 overflow-auto
      scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800/40
      hover:scrollbar-thumb-gray-600 transition-colors duration-200
    `}>
      <div className="text-center mb-8">
        <h3 className="text-lg font-semibold text-white mb-2">
          Welcome to AElf Code Generator
        </h3>
        <p className="text-gray-400 text-sm">
          Choose a template below or describe your smart contract requirements
        </p>
      </div>
      
      <div className={`
        grid grid-cols-2 gap-4 
        ${fullScreen ? 'max-w-4xl mx-auto px-4' : 'max-w-full'}
      `}>
        {INITIAL_SUGGESTIONS.map((suggestion, index) => (
          <button
            key={index}
            className="flex flex-col p-4 bg-gray-800 rounded-lg 
              hover:bg-gray-750 transition-colors duration-200 
              text-left border border-gray-700 hover:border-gray-600
              h-full group"
            onClick={() => onSuggestionClick(suggestion.prompt)}
          >
            <h4 className="text-white font-medium mb-1 group-hover:text-blue-400 transition-colors duration-200">
              {suggestion.title}
            </h4>
            <p className="text-gray-400 text-sm group-hover:text-gray-300 transition-colors duration-200">
              {suggestion.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};