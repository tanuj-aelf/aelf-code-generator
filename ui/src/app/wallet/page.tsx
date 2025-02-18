"use client";

import { useState } from "react";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import Link from "next/link";

import { useWallet } from "@/data/wallet";
import { Loader } from "@/components/ui/icons";
import { MainLayout } from "@/components/layout/MainLayout";

export default function Wallet() {
  const wallet = useWallet();

  return (
    <MainLayout className="flex flex-col min-h-screen bg-gray-900 p-8 pt-[100px] text-white">
      <div className="container mx-auto">
        <h1 className="text-2xl mb-2">Wallet information</h1>
        {wallet ? (
          <div>
            <p className="mt-3">
              Wallet address:{" "}
              <ViewAddressOnExplorer address={wallet?.wallet.address} />
            </p>
            <p className="mt-2">Privatekey:</p>
            <ViewPrivatekey privateKey={wallet?.wallet.privateKey} />
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <Loader /> Loading...
          </div>
        )}
      </div>
    </MainLayout>
  );
}

function ViewPrivatekey({ privateKey }: { privateKey: string }) {
  const [isVisibleKey, setIsVisibleKey] = useState(false);

  const toggleKey = () => setIsVisibleKey((prev: boolean) => !prev);

  return (
    <div className="flex gap-4 private-key py-2 px-4 mt-1 rounded-xl border-solid border-2 border-grey-900">
      <p className={isVisibleKey ? "key-visible" : ""}>{privateKey}</p>
      <EyeIcon
        className={`cursor-pointer ${isVisibleKey ? "hidden" : ""}`}
        onClick={toggleKey}
      />
      <EyeOffIcon
        className={`cursor-pointer ${!isVisibleKey ? "hidden" : ""}`}
        onClick={toggleKey}
      />
    </div>
  );
}

function ViewAddressOnExplorer({ address }: { address: string }) {
  return (
    <Link
      className="hover:underline"
      href={`https://testnet.aelfscan.io/tDVW/address/ELF_${address}_tDVW`}
      title="View on aelf Explorer"
      target="_blank"
      rel="noopener noreferrer"
    >
      AELF_{address}_tDVW
    </Link>
  );
}
