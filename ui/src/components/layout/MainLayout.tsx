interface MainLayoutProps {
  children?: React.ReactNode;
  fullScreen?: boolean;
  className?: string;
}

export const MainLayout = ({ children, fullScreen, className }: MainLayoutProps) => {
  return (
    <div className={`flex bg-gray-900 ${fullScreen ? 'h-full' : 'h-screen'} ${className}`}>
      <div className="flex-1 flex">{children}</div>
    </div>
  );
};
