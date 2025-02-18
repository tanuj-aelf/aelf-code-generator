"use client";

import Link from "next/link";
import ProjectDropdown from "./project-dropdown";
import { Button } from "../ui/button";
import { useRouter } from "next/navigation";

export const Header = () => {
  const router = useRouter();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-sm border-b border-gray-700">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <Link href={"/"}>
            <h1 className="text-xl font-bold text-white">
              AElf Code Generator
            </h1>
          </Link>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            className="text-gray-300 hover:text-white"
            onClick={() => router.push("/deployments")}
          >
            Deployments
          </Button>
          <Button
            variant="ghost"
            className="text-gray-300 hover:text-white"
            onClick={() => router.push("/contract-viewer")}
          >
            Contract Viewer
          </Button>
          <Button
            variant="ghost"
            className="text-gray-300 hover:text-white"
            onClick={() => router.push("/wallet")}
          >
            Wallet
          </Button>
          <ProjectDropdown />
          {/* <Button
            variant="outline"
            className="text-white px-3 bg-gray-800 hover:bg-gray-700"
          >
            <BurgetMenu />
          </Button> */}
        </div>
      </div>
    </header>
  );
};
