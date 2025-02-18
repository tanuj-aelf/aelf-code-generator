"use client";

import useSWR from "swr";
import { db } from "./db";
import AElf from "aelf-sdk";

const aelf = new AElf(
  new AElf.providers.HttpProvider("https://tdvw-test-node.aelf.io")
);

export function useWallet() {
  const { data: privateKey } = useSWR("wallet", async () => {
    const existingWallets = await db.wallet.toArray();

    if (existingWallets.length === 0) {
      const newWallet = AElf.wallet.createNewWallet();
      await db.wallet.add({ privateKey: newWallet.privateKey });
      return newWallet.privateKey as string;
    } else {
      return existingWallets[0].privateKey;
    }
  });

  if (!privateKey) return;

  return new Wallet(privateKey);
}

class Wallet {
  privateKey;
  wallet;
  cached: Record<string, any> = {};

  constructor(privateKey: string) {
    this.privateKey = privateKey;
    this.wallet = AElf.wallet.getWalletByPrivateKey(privateKey);
  }

  private async getChainStatus() {
    return await aelf.chain.getChainStatus();
  }

  private getContract(address: string) {
    return aelf.chain.contractAt(address, this.wallet);
  }

  private async getGenesisContract() {
    const chainStatus = await this.getChainStatus();
    return await this.getContract(chainStatus.GenesisContractAddress);
  }

  async deploy(code: string, category = 0): Promise<{ TransactionId: string }> {
    const genesisContract = await this.getGenesisContract();

    return await genesisContract.DeployUserSmartContract({
      category: String(category),
      code,
    });
  }

  private async getContractAddressByName(name: string) {
    const genesisContract = await this.getGenesisContract();

    return await genesisContract.GetContractAddressByName.call(
      AElf.utils.sha256(name)
    );
  }

  private async getTokenContractAddress() {
    return await this.getContractAddressByName("AElf.ContractNames.Token");
  }

  async getTokenContract() {
    const address = await this.getTokenContractAddress();

    return this.getContract(address);
  }

  async transfer(
    to: string,
    amount: number,
    memo: string
  ): Promise<{ TransactionId: string }> {
    const tokenContract = await this.getTokenContract();

    return await tokenContract.Transfer({
      symbol: "ELF",
      to,
      amount: String(amount),
      memo,
    });
  }

  async auditTransfer(codeHash: string) {
    return await this.transfer(
      `ASh2Wt7nSEmYqnGxPPzp4pnVDU4uhj1XW9Se5VeZcX2UDdyjx`,
      1,
      codeHash
    );
  }
}