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
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      if (!data.validate?.generate?._internal?.output) {
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
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, there was an error generating the code. Please try again.",
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
