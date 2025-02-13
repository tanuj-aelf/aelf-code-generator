interface ChatHeaderProps {
  fullScreen?: boolean;
}

export const ChatHeader = ({ fullScreen = false }: ChatHeaderProps) => {
  return (
    <div className={`p-4 border-b border-gray-700 ${fullScreen ? 'text-center' : ''}`}>
      <h2 className="text-lg font-semibold text-white">AElf Code Generator</h2>
      <p className="text-sm text-gray-400">
        {fullScreen 
          ? "Start by describing your smart contract requirements or choose a template below"
          : "Describe your smart contract requirements"
        }
      </p>
    </div>
  );
};