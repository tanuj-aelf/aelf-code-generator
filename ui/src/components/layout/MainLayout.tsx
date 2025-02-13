interface MainLayoutProps {
  children: React.ReactNode;
  fullScreen: boolean;
}

export const MainLayout = ({ children, fullScreen }: MainLayoutProps) => {
  return (
    <div className={`flex bg-gray-900 ${fullScreen ? 'h-full' : 'h-screen'}`}>
      <div className="flex-1 flex">{children}</div>
    </div>
  );
};
