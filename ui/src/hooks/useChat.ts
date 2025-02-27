import { useState } from "react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface UseChatProps {
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export const useChat = ({ onSuccess, onError }: UseChatProps = {}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");

  const handleInputChange = (value: string) => {
    setInputValue(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    setLoading(true);
    try {
      // Create an AbortController with a 5-minute timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 5 minutes

      const response = await fetch("/api/copilotkit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [
            {
              role: "user",
              content: userMessage,
            },
          ],
        }),
        signal: controller.signal,
      });

      // Clear the timeout
      clearTimeout(timeoutId);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      if (!data.test_contract?.generate?._internal?.output) {
        throw new Error("Invalid response format from agent");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I have generated the code based on your requirements. You can view the files in the explorer.",
        },
      ]);

      onSuccess?.(data);
    } catch (error) {
      console.error("Error generating code:", error);
      
      // Handle AbortError specifically
      const errorMessage = error instanceof DOMException && error.name === "AbortError"
        ? "The request took too long to complete. Please try again with a simpler request."
        : "Sorry, there was an error generating the code. Please try again.";
      
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMessage,
        },
      ]);
      onError?.(error as Error);
    } finally {
      setLoading(false);
    }
  };

  return {
    messages,
    loading,
    inputValue,
    handleInputChange,
    handleSubmit,
    setMessages,
  };
};
