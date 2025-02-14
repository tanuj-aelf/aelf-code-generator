import { ChatMessage } from "@/types";
import { ChatHeader } from "./ChatHeader";
import { ChatInput } from "./ChatInput";
import { ChatSuggestions } from "./ChatSuggestions";

interface ChatWindowProps {
    messages: ChatMessage[];
    loading: boolean;
    inputValue: string;
    onInputChange: (value: string) => void;
    onSubmit: (e: React.FormEvent) => void;
    fullScreen?: boolean;
  }
  
  export const ChatWindow = ({
    messages,
    loading,
    inputValue,
    onInputChange,
    onSubmit,
    fullScreen = false,
  }: ChatWindowProps) => {
    
  const handleSuggestionClick = (prompt: string) => {
    onInputChange(prompt);
  };

  return (
    <div className={`flex flex-col ${fullScreen ? 'h-[80vh] bg-gray-800 rounded-2xl shadow-xl' : 'h-full'}`}>
      <ChatHeader fullScreen={fullScreen} />
      
      <div className="flex-1 overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
        {messages.length === 0 ? (
          <ChatSuggestions onSuggestionClick={handleSuggestionClick} />
        ) : (
          <div className="p-4 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start space-x-2 ${
                  message.role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"
                }`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${message.role === "user" ? "bg-blue-600" : "bg-gray-700"}`}
                >
                  {message.role === "user" ? (
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  )}
                </div>
                
                <div className={`flex flex-col max-w-[75%] ${
                  message.role === "user" ? "items-end" : "items-start"
                }`}>
                  <div className={`rounded-2xl px-4 py-2 shadow-md ${
                    message.role === "user"
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-gray-800 text-gray-200 rounded-bl-none"
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <span className="text-xs text-gray-500 mt-1">
                    {message.role === "user" ? "You" : "Assistant"}
                  </span>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                  <svg className="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
                <div className="bg-gray-800 text-gray-200 rounded-2xl rounded-bl-none px-4 py-2 shadow-md">
                  <p className="text-sm">Generating code...</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <ChatInput
        value={inputValue}
        onChange={onInputChange}
        onSubmit={onSubmit}
        loading={loading}
        fullScreen={fullScreen}
      />
    </div>
  );
}; 