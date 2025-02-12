
interface Suggestion {
    title: string;
    description: string;
    prompt: string;
  }
  
  const INITIAL_SUGGESTIONS: Suggestion[] = [
    {
      title: "Create NFT Contract",
      description: "Generate a basic NFT smart contract with minting functionality",
      prompt: "Create an NFT smart contract with basic minting functionality and token management",
    },
    {
      title: "Token Contract",
      description: "Generate a fungible token contract with transfer and approval features",
      prompt: "Create a fungible token smart contract with transfer and approval functionality following ERC20-like standard",
    },
    {
      title: "Marketplace Contract",
      description: "Create a marketplace contract for trading NFTs",
      prompt: "Generate a marketplace smart contract for listing and trading NFTs with basic features like listing, buying, and canceling listings",
    },
    {
      title: "DAO Contract",
      description: "Generate a basic DAO contract with voting mechanism",
      prompt: "Create a DAO smart contract with proposal creation and voting functionality",
    },
  ];
  
  interface ChatSuggestionsProps {
    onSuggestionClick: (prompt: string) => void;
  }
  
  export const ChatSuggestions = ({ onSuggestionClick }: ChatSuggestionsProps) => {
    return (
      <div className="flex-1 p-4 overflow-auto">
        <div className="text-center mb-8">
          <h3 className="text-lg font-semibold text-white mb-2">
            Welcome to AElf Code Generator
          </h3>
          <p className="text-gray-400 text-sm">
            Choose a template below or describe your smart contract requirements
          </p>
        </div>
        
        <div className="grid grid-cols-1 gap-4 max-w-lg mx-auto">
          {INITIAL_SUGGESTIONS.map((suggestion, index) => (
            <button
              key={index}
              className="flex flex-col p-4 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors duration-200 text-left border border-gray-700 hover:border-gray-600"
              onClick={() => onSuggestionClick(suggestion.prompt)}
            >
              <h4 className="text-white font-medium mb-1">{suggestion.title}</h4>
              <p className="text-gray-400 text-sm">{suggestion.description}</p>
            </button>
          ))}
        </div>
      </div>
    );
  }; 