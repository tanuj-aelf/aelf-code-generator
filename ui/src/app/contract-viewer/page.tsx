"use client";

import React from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { useWallet } from "@/data/wallet";
import { useSearchParams } from "next/navigation";
// @ts-ignore
import { ContractView } from "aelf-smartcontract-viewer";
import "./style.css";

const sideChainTestnetRpc = "https://tdvw-test-node.aelf.io";

const ContractViewer = () => {
  const wallet = useWallet();
  const searchParams = useSearchParams();
  const contractViewerAddress = searchParams.get("address");

  return (
    <MainLayout className="flex flex-col min-h-screen bg-gray-900 p-8 pt-[100px]">
      <div className="container mx-auto">
        {wallet && (
          <ContractView
            headerTitle="Contract Viewer"
            wallet={wallet.wallet}
            address={contractViewerAddress || ""}
            rpcUrl={sideChainTestnetRpc}
            theme="dark"
          />
        )}
      </div>
    </MainLayout>
  );
};

export default ContractViewer;
