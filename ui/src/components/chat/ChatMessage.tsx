interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export const ChatMessage = ({ role, content }: ChatMessageProps) => {
  return (
    <div className={`flex items-start space-x-2 ${
      role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"
    }`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
        ${role === "user" ? "bg-blue-600" : "bg-gray-700"}`}>
        {role === "user" ? (
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
        role === "user" ? "items-end" : "items-start"
      }`}>
        <div className={`rounded-2xl px-4 py-2 shadow-md ${
          role === "user"
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-800 text-gray-200 rounded-bl-none"
        }`}>
          <p className="text-sm">{content}</p>
        </div>
        <span className="text-xs text-gray-500 mt-1">
          {role === "user" ? "You" : "Assistant"}
        </span>
      </div>
    </div>
  );
}; 