import React from "react";
import { Button } from "./button";
import { BurgetMenu, Copy } from "./icons";
import Link from "next/link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { useRouter } from "next/navigation";

interface IProps {
  deployment: { time: string; address: string };
}

const formatTime = (utcTime: string) => {
  return new Date(utcTime).toLocaleString();
};

const DeploymentCard = (props: IProps) => {
  const { address, time } = props.deployment;
  const router = useRouter();

  return (
    <div className="group relative p-4 rounded-xl shadow-lg cursor-pointer backdrop-blur-xl bg-opacity-20 border border-gray-700 transition-transform transform hover:border-blue-500">
      <div className="flex right-2 top-2 absolute justify-end">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="text-gray-300 hover:text-white px-2">
              <BurgetMenu />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56">
            <DropdownMenuItem
              onClick={() => router.push(`/contract-viewer?address=${address}`)}
            >
              Contract Viewer
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="relative z-10">
        <h2 className="text-sm text-white pl-1 my-1">Address:</h2>
        <Button
          variant="outline"
          className="text-[13px] text-white mt-2 p-3 mb-10 w-full justify-between"
          onClick={() => {
            navigator.clipboard.writeText(address);
          }}
        >
          {address}
          <Copy />
        </Button>
        <p className="text-gray-400 text-sm mt-2">{formatTime(time)}</p>
      </div>
    </div>
  );
};

export default DeploymentCard;
