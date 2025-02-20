import React, {
  PropsWithChildren,
  useEffect,
  useRef,
  useState,
} from "react";
import { Copy, CopyCheck } from "lucide-react";
//@ts-ignore
import ReCAPTCHA from "react-google-recaptcha"; // Import reCAPTCHA
import Link from "next/link";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader } from "@/components/ui/icons";
import { useEditorContext } from "@/context/EditorContext";
import { AuditType, useAudit, useAuditReport } from "@/data/audit";
import { Button } from "@/components/ui/button";
import { FormatErrors } from "@/lib/format-errors";
import { useLogs, useProposalsInfo, useTransactionResult } from "@/data/client";
import { cn } from "@/lib/utils";
import { env } from "@/data/env";
import ProgressBar from "./Progressbar";

const captchaSitekey = env.GOOGLE_CAPTCHA_SITEKEY;
const PROPOSAL_TIMEOUT = 15 * 60 * 1000; // proposal expires after 15 minutes

const Dialogs = ({
  handleCaptchaSuccess,
  onDeploy,
  closeRecaptcha,
}: {
  handleCaptchaSuccess: (token: string) => void;
  onDeploy: () => void;
  closeRecaptcha: () => void;
}) => {
  const [copied, setCopied] = useState(false);
  const recaptchaRef = useRef<ReCAPTCHA>(null);

  const {
    buildDeployStatus,
    isRecaptchaCheck,
    modalOpen,
    actionMessage,
    isActionCompleted,
    isActionRunning,
    auiditResponse,
    shareLink,
    setBuildDeployStatus,
    setIsRecaptchaCheck,
    setModalOpen,
    setActionMessage,
    setActionCompleted,
    setAuiditResponse,
    setShareLink,
  } = useEditorContext();

  const onReCAPTCHAChange = (token: string | null) => {
    if (token) {
      setIsRecaptchaCheck(false);
      handleCaptchaSuccess(token);
    }
  };

  const resetState = () => {
    setModalOpen("");
    setActionCompleted(false);
    setBuildDeployStatus("");
    setActionMessage("");
    setShareLink("");
    setAuiditResponse({
      success: false,
      codeHash: "",
      auditType: "",
      transactionId: "",
      message: "",
    });
  };

  return (
    <div>
      <Dialog open={modalOpen === "audit"} onOpenChange={resetState}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">AI Auidit report</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md p-10 auidit-result scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
            {isActionRunning ? (
              <div className="flex items-center justify-center text-sm">
                <Loader /> Loading Report...
              </div>
            ) : (
              auiditResponse.auditType && (
                <AuditReport
                  auditType={auiditResponse.auditType}
                  codeHash={auiditResponse?.codeHash || ""}
                  transactionId={auiditResponse?.transactionId || ""}
                />
              )
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={modalOpen === "saveGas"} onOpenChange={resetState}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">Save Gas Fees report</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md p-10 auidit-result scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
            {isActionRunning ? (
              <div className="flex items-center justify-center text-sm">
                <Loader /> Loading Report...
              </div>
            ) : (
              auiditResponse.auditType && (
                <AuditReport
                  auditType={auiditResponse.auditType}
                  codeHash={auiditResponse?.codeHash || ""}
                  transactionId={auiditResponse?.transactionId || ""}
                />
              )
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={modalOpen === "build"} onOpenChange={resetState}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Build</DialogTitle>
            <ProgressBar isProcessCompleted={isActionCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <div>
                <p
                  className={cn(
                    "text-sm",
                    buildDeployStatus === "success"
                      ? "text-green-400"
                      : buildDeployStatus === "error"
                      ? "text-red-400"
                      : "text-white"
                  )}
                >
                  {!isActionCompleted ? "Building..." : actionMessage}
                </p>
              </div>
            </div>
          </div>
          {buildDeployStatus === "success" && isActionCompleted && (
            <Button
              variant="outline"
              className="border-gray-700 text-white"
              onClick={() => {
                resetState();
                onDeploy();
              }}
            >
              Deploy Now
            </Button>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={modalOpen === "test"} onOpenChange={resetState}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">Running tests...</DialogTitle>
            <ProgressBar isProcessCompleted={isActionCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <DialogDescription className="text-white overflow-auto">
                {!isActionCompleted ? (
                  "Loading..."
                ) : (
                  <FormatErrors inputString={actionMessage} />
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={modalOpen === "share"} onOpenChange={resetState}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Generate Share Link</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <div className="p-3">
              <DialogDescription className="text-white overflow-auto py-3">
                {isActionRunning ? (
                  <div className="flex items-center justify-center">
                    <Loader /> Loading...
                  </div>
                ) : shareLink ? (
                  <div className="flex w-full items-center justify-between rounded-md bg-gray-800 p-2 border border-gray-600">
                    <p className="text-[13px] text-sky-500">{shareLink}</p>
                    {copied ? (
                      <CopyCheck className="w-4 h-4 mx-2" />
                    ) : (
                      <Copy
                        className="w-4 h-4 mx-2 cursor-pointer"
                        onClick={() => {
                          navigator.clipboard.writeText(shareLink);
                          setCopied(true);
                        }}
                      />
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    {actionMessage}
                  </div>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={modalOpen === "deploy"} onOpenChange={resetState}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Contract Deployment</DialogTitle>
            <ProgressBar isProcessCompleted={isActionCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <DialogDescription
                className={
                  buildDeployStatus === "error" ? "text-red-400" : "text-white"
                }
              >
                {!isActionCompleted ? (
                  "Deploying..."
                ) : (
                  <div>
                    <p className="text-[13px]">TransactionId: </p>
                    <Link
                      className="text-[12px] underline text-sky-400 block mb-4"
                      href={`https://testnet.aelfscan.io/tDVW/tx/${actionMessage}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {actionMessage}
                    </Link>
                    <Deployment id={actionMessage} />
                  </div>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isRecaptchaCheck} onOpenChange={closeRecaptcha}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Human Varification</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center min-h-[90px]">
            <ReCAPTCHA
              ref={recaptchaRef}
              sitekey={captchaSitekey as string}
              onChange={onReCAPTCHAChange}
            />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

function Loading({ children }: PropsWithChildren) {
  return (
    <div className="flex items-center gap-1">
      <Loader /> {children}
    </div>
  );
}

function Deploying() {
  return <Loading>Deploying...</Loading>;
}

function Deployment({ id }: { id: string }) {
  const [shouldPoll, setShouldPoll] = useState(true);
  const { data, error } = useTransactionResult(
    id,
    shouldPoll ? 1000 : undefined
  );
  const { Status } = data || {};

  useEffect(() => {
    if (Status === "MINED" || !!error) setShouldPoll(false);
  }, [Status, error]);

  if (error) return <p>Error: {error.Error}</p>;
  if (!data || Status === "PENDING") return <Deploying />;

  return <CheckProposalId id={id} />;
}

function CheckProposalId({ id }: { id: string }) {
  const [shouldPoll, setShouldPoll] = useState(true);
  const { data } = useLogs(id, shouldPoll ? 1000 : undefined);
  const { proposalId } = data || {};

  useEffect(() => {
    if (proposalId) setShouldPoll(false);
  }, [proposalId]);

  if (!proposalId) return <Deploying />;

  return <CheckProposalInfo id={proposalId} />;
}

function CheckProposalInfo({ id }: { id: string }) {
  const [releasedTxId, setReleasedTxId] = useState<string>();
  const [timedOut, setTimedOut] = useState(false);

  const { data, loading } = useProposalsInfo(
    [id],
    releasedTxId ? undefined : 1000
  );

  useEffect(() => {
    const releasedTxId =
      data?.getNetworkDaoProposalReleasedIndex.data?.[0]?.transactionInfo
        .transactionId;
    setReleasedTxId(releasedTxId);
  }, [loading, data]);

  useEffect(() => {
    setTimedOut(false);
    const timer = setTimeout(() => {
      setTimedOut(true);
    }, PROPOSAL_TIMEOUT);
    return () => clearTimeout(timer);
  }, [id]);

  const url = `https://test.tmrwdao.com/network-dao/proposal/${id}?chainId=tDVW`;

  if (timedOut)
    return (
      <p>
        Timed out. Proposal ID:{" "}
        <Link href={url} target="_blank" rel="noopener noreferrer">
          {id}
        </Link>
        .
      </p>
    );

  return (
    <>
      <p>Proposal status: {releasedTxId ? "released" : "pending"}</p>
      {releasedTxId ? (
        <DeployedContractDetails id={releasedTxId} />
      ) : (
        <Deploying />
      )}
    </>
  );
}

function DeployedContractDetails({ id }: { id?: string }) {
  const { data } = useLogs(id);

  if (!data) return <Deploying />;

  return (
    <div className="mt-3">
      <p>Contract Address:</p>
      <Button
        variant={"outline"}
        className="border-gray-600 bg-gray-800 mt-2 text-[13px] px-3"
      >
        {data.address}
      </Button>
    </div>
  );
}

const AuditReport = ({
  auditType,
  codeHash,
  transactionId,
}: {
  auditType: AuditType;
  codeHash: string;
  transactionId: string;
}) => {
  const { isLoading, error } = useAudit(auditType, codeHash, transactionId);

  if (isLoading || !!error)
    return (
      <div className="flex items-center justify-center text-sm">
        <Loader /> Loading Report...
      </div>
    );

  return <AuditReportResult auditType={auditType} codeHash={codeHash} />;
};

const AuditReportResult = ({
  auditType,
  codeHash,
}: {
  auditType: AuditType;
  codeHash: string;
}) => {
  const { data, isLoading } = useAuditReport(auditType, codeHash);

  if (isLoading || !data)
    return (
      <div className="flex items-center justify-center text-sm">
        <Loader /> Loading Report...
      </div>
    );

  return (
    <>
      <table>
        <thead>
          <tr>
            <th className="p-2">Item</th>
            <th className="p-2">Suggestion</th>
          </tr>
        </thead>
        {Object.entries(data).map(([k, v]) => (
          <tr key={k} className="border border-gray-700">
            <td className="p-2">{k}</td>
            <td className="p-2">
              {v.map((i, index) => (
                <div
                  key={index}
                  className={cn("border-gray-700 p-2", {
                    "border-t-0": index !== 0,
                  })}
                >
                  {i.Detail ? (
                    <>
                      <p>Original: {i.Detail.Original}</p>
                      <p>Suggested: {i.Detail.Updated}</p>
                    </>
                  ) : null}
                </div>
              ))}
            </td>
          </tr>
        ))}
      </table>
    </>
  );
};

export default Dialogs;
