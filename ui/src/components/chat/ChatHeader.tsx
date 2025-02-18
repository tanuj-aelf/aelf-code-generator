interface ChatHeaderProps {
  fullScreen?: boolean;
}

export const ChatHeader = ({ fullScreen = false }: ChatHeaderProps) => {
  return (
    <div className={`p-4 border-b border-gray-700 ${fullScreen ? 'text-center' : ''}`}>
      <h2 className="text-lg font-semibold text-white">Chat Bot</h2>
      {fullScreen && (
        <p className="text-sm text-gray-400">Start by describing your smart contract requirements or choose a template below</p>
      )}
    </div>
  );
};