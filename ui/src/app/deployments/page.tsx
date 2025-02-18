"use client";

import React, { useMemo } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { useContractList } from "@/data/graphql";
import { useWallet } from "@/data/wallet";
import DeploymentCard from "@/components/ui/deployment-card";

const Deployments = () => {
  const wallet = useWallet();
  const { data, loading } = useContractList(wallet?.wallet.address);

  const deployments = useMemo(() => {
    if (data) {
      return data.contractList.items.map((i) => ({
        time: i.metadata.block.blockTime,
        address: i.address,
      }));
    }
    return null;
  }, [data]);

  return (
    <MainLayout className="flex flex-col min-h-screen bg-gray-900 p-8 pt-[100px]">
      <div className="container mx-auto">
        <h2 className="text-2xl text-white font-semibold mb-6">
          Deployment History
        </h2>

        {loading ? (
          <div className="text-white">Loading...</div>
        ) : (
          deployments && (
            <div className="mb-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {deployments.map((deployment, index) => (
                  <DeploymentCard key={index} deployment={deployment}/>
                ))}
              </div>
            </div>
          )
        )}
      </div>
    </MainLayout>
  );
};

export default Deployments;
