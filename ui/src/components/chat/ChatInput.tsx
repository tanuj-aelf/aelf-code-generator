import { useRef, useEffect } from 'react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  fullScreen?: boolean;
}

export const ChatInput = ({
  value,
  onChange,
  onSubmit,
  loading,
  fullScreen = false,
}: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [value]);

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!loading && value.trim()) {
      onSubmit(e);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className={`
        p-4 border-t border-gray-700 bg-gray-900
        ${fullScreen ? 'rounded-b-lg shadow-lg' : ''}
      `}
    >
      <div className={`
        flex gap-2 items-end
        ${fullScreen ? 'max-w-2xl mx-auto' : ''}
      `}>
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={fullScreen 
              ? "Describe your smart contract requirements in detail..."
              : "Type your message..."
            }
            rows={1}
            className={`
              w-full bg-gray-800 text-white rounded-2xl pl-4 pr-12
              focus:outline-none focus:ring-1 focus:ring-blue-500 
              focus:bg-gray-750 transition-all duration-200
              resize-none overflow-hidden
              ${fullScreen ? 'py-4 text-lg' : 'py-3 text-base'}
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            style={{
              minHeight: fullScreen ? '64px' : '48px',
              maxHeight: '200px'
            }}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !value.trim()}
            className={`
              absolute right-2 bottom-2
              bg-blue-600 text-white rounded-xl
              hover:bg-blue-700 disabled:opacity-50 
              disabled:hover:bg-blue-600 transition-all duration-200
              flex items-center justify-center mb-[6px]
              ${fullScreen ? 'p-3' : 'p-2'}
            `}
          >
            {loading ? (
              <svg 
                className={`animate-spin ${fullScreen ? 'w-6 h-6' : 'w-5 h-5'}`}
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle 
                  className="opacity-25" 
                  cx="12" 
                  cy="12" 
                  r="10" 
                  stroke="currentColor" 
                  strokeWidth="4"
                />
                <path 
                  className="opacity-75" 
                  fill="currentColor" 
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg 
                className={`${fullScreen ? 'w-6 h-6' : 'w-5 h-5'}`}
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M5 12h14M12 5l7 7-7 7"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="mt-3 text-center text-sm text-gray-400">
        {fullScreen ? (
          "Press Enter to send, Shift + Enter for new line"
        ) : (
          <div className="flex justify-between text-xs px-1">
            <span>Shift + Enter for new line</span>
            <span>Enter to send</span>
          </div>
        )}
      </div>
    </form>
  );
};