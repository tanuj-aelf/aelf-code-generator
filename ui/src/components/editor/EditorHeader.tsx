import { Button } from "@/components/ui/button";

interface EditorHeaderProps {
  onDeploy?: () => void;
  onBuild?: () => void;
  isBuilding?: boolean;
  buildStatus?: 'idle' | 'success' | 'error';
}

export const EditorHeader = ({
  onDeploy,
  onBuild,
  isBuilding = false,
  buildStatus = 'idle'
}: EditorHeaderProps) => {
  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
      <div className="flex items-center space-x-4">
        {buildStatus === 'success' && (
          <span className="text-green-500 text-sm flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Build successful
          </span>
        )}
        {buildStatus === 'error' && (
          <span className="text-red-500 text-sm flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Build failed
          </span>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={onBuild}
          disabled={isBuilding}
        >
          {isBuilding ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Building...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Build
            </>
          )}
        </Button>
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={onDeploy}
        >
          <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          Deploy
        </Button>
      </div>
    </header>
  );
}; 