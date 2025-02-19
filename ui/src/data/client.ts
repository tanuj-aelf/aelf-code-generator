"use client";

import useSWR from "swr";
import AElf from "aelf-sdk";
import { strFromU8, unzipSync } from "fflate";
import { FileContent } from "./db";
import { useProposalReleaseInfo } from "./graphql";

//@ts-ignore
const { deserializeLog } = AElf.pbUtils;

const aelf = new AElf(
  new AElf.providers.HttpProvider("https://tdvw-test-node.aelf.io")
);

export function useShare(id?: string) {
  return useSWR<{ files?: FileContent[]; message?: string; success: boolean }>(
    id ? `get-share-${id}` : undefined,
    async () => {
      try {
        if (!id) {
          return { success: false, message: "Share Id is missing" };
        }
        const res = await fetch(`/api/playground/share/get/${id}`);

        const data = await res.arrayBuffer();

        const unzipped = unzipSync(Buffer.from(data));

        let files: FileContent[] = [];

        Object.entries(unzipped).forEach(([k, v]) => {
          files.push({
            path: k,
            contents: strFromU8(v),
          });
        });

        return { files, success: true };
      } catch (err) {
        let error = "An error occurred.";
        if (err instanceof Error) {
          error = err.message;

          if (error === "invalid zip data")
            error = "This share ID is not available.";
        }

        return { message: error, success: false };
      }
    }
  );
}

export function useTransactionResult(id?: string, refreshInterval?: number) {
  return useSWR<
    {
      TransactionId: string;
      Status: string;
      Logs: Array<{
        Address: string;
        Name: string;
        Indexed: Array<string>;
        NonIndexed: string;
      }>;
      Bloom: string;
      BlockNumber: number;
      BlockHash: string;
      Transaction: {
        From: string;
        To: string;
        RefBlockNumber: number;
        RefBlockPrefix: string;
        MethodName: string;
        Params: string;
        Signature: string;
      };
      ReturnValue: string;
      Error: any;
      TransactionSize: number;
    },
    {
      TransactionId: string;
      Status: string;
      Logs: [];
      Bloom: null;
      BlockNumber: 0;
      BlockHash: null;
      Transaction: null;
      ReturnValue: "";
      Error: string;
      TransactionSize: 0;
    }
  >(
    id ? `tx-${id}` : undefined,
    async () => {
      const res = await aelf.chain.getTxResult(id as string);

      switch (res?.Status) {
        case "NOTEXISTED":
        case "NODEVALIDATIONFAILED":
          throw res;
      }

      return res;
    },
    { refreshInterval }
  );
}

export function useProposalsInfo(ids?: string[], refreshInterval?: number) {
  return useProposalReleaseInfo(ids, refreshInterval);
}

export function useLogs(id?: string, refreshInterval?: number) {
  const { data: txResult } = useTransactionResult(id);
  return useSWR(
    id && !!txResult ? `get-logs-${id}` : undefined,
    async () => {
      const services = await Promise.all(
        txResult!.Logs.map(async ({ Address }: { Address: string }) =>
          //@ts-ignore
          AElf.pbjs.Root.fromDescriptor(
            await aelf.chain.getContractFileDescriptorSet(Address)
          )
        )
      );

      const deserializedLogs: Array<{ proposalId: string }> =
        await deserializeLog(txResult!.Logs, services);

      return deserializedLogs.reduce(
        (acc, cur) => ({ ...acc, ...cur }),
        {} as Record<string, string>
      );
    },
    { refreshInterval }
  );
}
