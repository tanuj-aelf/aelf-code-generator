"use client";

import useSWRImmutable from "swr/immutable";
import { z } from "zod";
import { FileContent } from "./db";
import { fileContentToZip } from "@/lib/file-content-to-zip";
import { v4 as uuidv4 } from "uuid";
import { useSearchParams } from "next/navigation";

export enum AuditType {
  DEFAULT = "default",
  SAVE_GAS_FEE = "saveGasFee",
}

const URL_CONFIG = {
  [AuditType.DEFAULT]: {
    uploadContractCode: "/api/api/playground/audit/uploadContractCode",
    auditContractCode: "/api/api/playground/audit/auditContractCode",
    report: "/api/api/playground/report",
  },
  [AuditType.SAVE_GAS_FEE]: {
    uploadContractCode: "/api/api/playground/adjustGasFee/uploadContractCode",
    auditContractCode: "/api/api/playground/adjustGasFee/execute",
    report: "/api/api/playground/adjustGasFee/report",
  },
};

const uploadContractCodeSchema = z.object({ codeHash: z.string() });

export async function uploadContractCode(
  auditType: AuditType,
  files: FileContent[]
) {
  const zippedData = fileContentToZip(files);

  const formData = new FormData();
  const filePath = uuidv4() + ".zip";
  formData.append(
    "contractFiles",
    new File([zippedData], filePath, { type: "application/zip" }),
    filePath
  );

  const requestInit: RequestInit = {
    method: "POST",
    body: formData,
    redirect: "follow",
  };

  const res = await fetch(
    URL_CONFIG[auditType].uploadContractCode,
    requestInit
  );

  const message = await res.clone().text();

  if (!res.ok) {
    throw new Error(message);
  }

  const data = await res.json();

  const { codeHash } = uploadContractCodeSchema.parse(data);

  return codeHash;
}

const auditSchema = z.object({ reportUrl: z.string() });

export function useAudit(
  auditType: AuditType,
  auditId?: string,
  transactionId?: string
) {
  return useSWRImmutable(
    auditId && transactionId
      ? `audit-${auditType}-${auditId}-${transactionId}`
      : undefined,
    async () => {
      const res = await fetch(
        `${URL_CONFIG[auditType].auditContractCode}?auditId=${auditId}&transactionId=${transactionId}`
      );

      const data = await res.json();

      const { reportUrl } = auditSchema.parse(data);

      return reportUrl;
    }
  );
}

const auditReportSchema = z.record(
  z.array(
    z.object({
      Description: z.string(),
      Content: z.string(),
      Detail: z
        .object({ Original: z.string(), Updated: z.string() })
        .or(z.null()),
    })
  )
);

export function useAuditReport(auditType?: AuditType, auditId?: string) {
  return useSWRImmutable(
    auditType && auditId ? `audit-report-${auditType}-${auditId}` : undefined,
    async () => {
      if (!auditType) return;

      const res = await fetch(`${URL_CONFIG[auditType].report}/${auditId}`);

      const data = await res.json();

      const report = auditReportSchema.parse(data);

      return report;
    },
    { errorRetryInterval: 10 }
  );
}

export function useAuditReportSearchParam() {
  const params = useSearchParams();
  const auditId = params.get("auditId");
  const auditType = params.get("auditType") as AuditType | null;
  return useAuditReport(auditType || undefined, auditId || undefined);
}
