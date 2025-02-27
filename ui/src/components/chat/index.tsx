import { AgentResponse } from "@/types";
import { ChatHeader } from "./ChatHeader";
import { ChatInput } from "./ChatInput";
import { ChatSuggestions } from "./ChatSuggestions";
import { useChat } from "@/hooks/useChat";
import { db, FileContent } from "@/data/db";
import { useContract } from "@/context/ContractContext";
import { useWorkspaces } from "@/hooks/useWorkspaces";
import { Loader } from "../ui/icons";

interface ChatWindowProps {
  fullScreen?: boolean;
}

export const ChatWindow = ({ fullScreen = false }: ChatWindowProps) => {
  const { updateFiles } = useContract();
  const { data: workspaces } = useWorkspaces();

  const { messages, loading, inputValue, handleInputChange, handleSubmit } =
    useChat({
      onSuccess: async (data: AgentResponse) => {
        const allFiles: FileContent[] = extractFiles(data);
        updateFiles(allFiles);
        await saveWorkspaceData(workspaces?.length ?? 0, allFiles);
      },
    });

  const handleSuggestionClick = (prompt: string) => handleInputChange(prompt);

  return (
    <div className={`flex flex-col ${fullScreen ? "h-[80vh] bg-gray-800 rounded-2xl shadow-xl" : "h-full"}`}>
      <ChatHeader fullScreen={fullScreen} />
      <div className="flex-1 overflow-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
        {messages.length === 0 ? (
          <ChatSuggestions onSuggestionClick={handleSuggestionClick} />
        ) : (
          <div className="p-4 space-y-4">
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
            {loading && <LoadingIndicator />}
          </div>
        )}
      </div>
      <ChatInput
        value={inputValue}
        onChange={handleInputChange}
        onSubmit={handleSubmit}
        loading={loading}
        fullScreen={fullScreen}
      />
    </div>
  );
};

const extractFiles = (data: AgentResponse): FileContent[] => {
  return [
    data.test_contract?.generate._internal.output.contract,
    data.test_contract?.generate._internal.output.state,
    data.test_contract?.generate._internal.output.proto,
    data.test_contract?.generate._internal.output.reference,
    data.test_contract?.generate._internal.output.project,
    ...(data.test_contract?.generate._internal.output.metadata || []),
  ]
    .filter((file): file is { path: string; content: string } => Boolean(file?.path && file?.content))
    .map((file) => ({ path: file.path, contents: file.content }));
};

const saveWorkspaceData = async (workspaceCount: number, allFiles: FileContent[]) => {
  const workspace = `project-${workspaceCount + 1}`;
  await db.workspaces.add({ name: workspace, template: "", dll: "" });
  await db.files.bulkAdd(
    allFiles.map(({ path, contents }) => ({ path: `/workspace/${workspace}/${path}`, contents }))
  );
};

const ChatMessage = ({ message }: { message: { role: string; content: string } }) => (
  <div className={`flex items-start space-x-2 ${message.role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"}`}>
    <UserAvatar role={message.role} />
    <div className={`flex flex-col max-w-[75%] ${message.role === "user" ? "items-end" : "items-start"}`}>
      <MessageBubble message={message} />
      <span className="text-xs text-gray-500 mt-1">{message.role === "user" ? "You" : "Assistant"}</span>
    </div>
  </div>
);

const UserAvatar = ({ role }: { role: string }) => (
  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${role === "user" ? "bg-blue-600" : "bg-gray-700"}`}>
    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={role === "user" ? "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" : "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"} />
    </svg>
  </div>
);

const MessageBubble = ({ message }: { message: { role: string; content: string } }) => (
  <div className={`rounded-2xl px-4 py-2 shadow-md ${message.role === "user" ? "bg-blue-600 text-white rounded-br-none" : "bg-gray-800 text-gray-200 rounded-bl-none"}`}>
    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
  </div>
);

const LoadingIndicator = () => (
  <div className="flex items-start space-x-2">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
      <Loader className="mr-0 text-white"/>
    </div>
    <div className="bg-gray-800 text-gray-200 rounded-2xl rounded-bl-none px-4 py-2 shadow-md">
      <p className="text-sm">Generating code...</p>
    </div>
  </div>
);