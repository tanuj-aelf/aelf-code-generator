import { Button } from "@/components/ui/button";

interface EditorHeaderProps {
  onDeploy?: () => void;
}

export const EditorHeader = ({ onDeploy }: EditorHeaderProps) => {
  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
      <div className="flex items-center space-x-4"></div>
      <div className="flex items-center space-x-2">
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={onDeploy}
        >
          Deploy
        </Button>
      </div>
    </header>
  );
}; 