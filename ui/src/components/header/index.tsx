"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "../ui/button";

const NAV_ARRAY = [
  {
    id: "1",
    name: "Deployments",
    url: "/deployments",
  },
  {
    id: "2",
    name: "Contract Viewer",
    url: "/contract-viewer",
  },
  {
    id: "3",
    name: "Wallet",
    url: "/wallet",
  },
  {
    id: "4",
    name: "Projects",
    url: "/projects",
  },
];

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
        <div className="flex items-center space-x-2">
          {NAV_ARRAY.map(({ name, url, id }) => (
            <Button
              key={id}
              variant="ghost"
              className="text-gray-300 hover:text-white"
              onClick={() => router.push(url)}
            >
              {name}
            </Button>
          ))}
        </div>
      </div>
    </header>
  );
};
