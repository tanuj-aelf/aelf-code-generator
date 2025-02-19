//@ts-nocheck
import ReCAPTCHA from "react-google-recaptcha"; // Import reCAPTCHA
import { useState, useCallback, useRef, useEffect } from "react";
import { Copy, CopyCheck, Link2, ShieldCheck, TestTube2 } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useCliCommands } from "@/hooks/useCliActions";
import { Deploy, Export, HandCoins, Loader, Terminal } from "../ui/icons";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { useWallet } from "@/data/wallet";
import { env } from "@/data/env";
import ProgressBar from "./Progressbar";
import { FormatErrors } from "@/lib/format-errors";
import { AuditType, useAudit, useAuditReport } from "@/data/audit";
import { cn } from "@/lib/utils";
import "./style.css";
import { useLogs, useProposalsInfo, useTransactionResult } from "@/data/client";

const faucetUrl = env.FAUCET_API_URL;
const captchaSitekey = env.GOOGLE_CAPTCHA_SITEKEY;
const PROPOSAL_TIMEOUT = 15 * 60 * 1000; // proposal expires after 15 minutes

export const EditorHeader = () => {
  const [buildStatus, setBuildStatus] = useState<"idle" | "success" | "error">(
    "idle"
  );
  const [deployStatus, setDeployStatus] = useState<"" | "success" | "error">(
    ""
  );
  const recaptchaRef = useRef<ReCAPTCHA>(null);
  const [captchaType, setCaptchaType] = useState<"" | "audit" | "deploy">("");
  const [checkingBalance, setCheckingBalance] = useState<
    "" | "audit" | "deploy"
  >("");
  const [isRecaptchaCheck, setIsRecaptchaCheck] = useState(false);

  const [buildMessage, setBuildMessage] = useState("");
  const [isBuildModalOpen, setBuildModalOpen] = useState(false);
  const [isBuildingCompleted, setBuildingCompleted] = useState(false);

  const [testMessage, setTestMessage] = useState("");
  const [isTestModalOpen, setTestModalOpen] = useState(false);
  const [isTestingCompleted, setTestingCompleted] = useState(false);

  const [auiditResponse, setAuiditResponse] = useState<{
    success: boolean;
    codeHash: string;
    auditType: AuditType | "";
    transactionId: string;
    message: string;
  }>({
    success: false,
    codeHash: "",
    auditType: "",
    transactionId: "",
    message: "",
  });

  const [isAuiditModalOpen, setAuiditModalOpen] = useState(false);
  const [isAuiditing, setIsAuiditing] = useState(false);

  const [isSaveGasFeeModalOpen, setSaveGasFeeModalOpen] = useState(false);
  const [isSaveGasFeeAuditing, setIsSaveGasFeeAuditing] = useState(false);

  const [isDeployModalOpen, setDeployModalOpen] = useState(false);
  const [deployMessage, setDeployMessage] = useState("");
  const [isDeploymentCompleted, setDeploymentCompleted] = useState(false);

  const [isShareModalOpen, setShareModalOpen] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);
  const [shareLink, setShareLink] = useState("");
  const [shareMessage, setShareMessage] = useState("");
  const [copied, setCopied] = useState(false);

  const { build, deploy, exportProject, test, share, audit } = useCliCommands();
  const wallet = useWallet();

  const onBuild = useCallback(async () => {
    setBuildModalOpen(true);

    const result = await build();
    setBuildStatus(result?.success ? "success" : "error");
    setBuildMessage(result?.message || "");
    setBuildingCompleted(true);
  }, [build]);

  const onTest = useCallback(async () => {
    setTestModalOpen(true);

    const result = await test();
    setTestMessage(result || "");
    setTestingCompleted(true);
  }, [test]);

  const handleShare = async () => {
    setShareLoading(true);
    setShareModalOpen(true);
    const result = await share();
    if (result.success) {
      setShareLink(result.link);
    }
    setShareMessage(result.message);
    setShareLoading(false);
  };

  const resetBuild = useCallback(() => {
    setBuildModalOpen(false);
    setBuildingCompleted(false);
    setBuildStatus("idle");
    setBuildMessage("");
  }, []);

  const resetTest = useCallback(() => {
    setTestModalOpen(false);
    setTestingCompleted(false);
    setTestMessage("");
  }, []);

  const resetShare = useCallback(() => {
    setShareModalOpen(false);
    setShareMessage("");
    setShareLink("");
  }, []);

  const resetDeploy = useCallback(() => {
    setDeployModalOpen(false);
    setDeploymentCompleted(false);
    setDeployStatus("");
    setDeployMessage("");
  }, []);

  const resetAuidit = useCallback(() => {
    setAuiditModalOpen(false);
    setAuiditResponse({
      success: false,
      codeHash: "",
      auditType: "",
      transactionId: "",
      message: "",
    });
  }, []);

  const resetSaveGasFee = useCallback(() => {
    setSaveGasFeeModalOpen(false);
    setAuiditResponse({
      success: false,
      codeHash: "",
      auditType: "",
      transactionId: "",
      message: "",
    });
  }, []);

  const isBalanceAvailable = async (type: "" | "audit" | "deploy") => {
    try {
      setCheckingBalance(type);
      const tokenContract = await wallet?.getTokenContract();
      const balance = await tokenContract.GetBalance.call({
        symbol: "ELF",
        owner: wallet?.wallet.address,
      });
      if (balance.balance === 0) {
        console.log("Don't have balance");
        return false;
      } else {
        setCheckingBalance("");
        return true;
      }
    } catch (error) {
      return false;
    }
  };

  const showGoogleCaptcha = (type: "audit" | "deploy") => {
    setCaptchaType(type);
    setIsRecaptchaCheck(true);
  };

  const handleDeploy = async () => {
    try {
      setDeployModalOpen(true);
      const result = await deploy();
      setDeployStatus(result?.success ? "success" : "error");
      setDeployMessage(result?.message || "");
    } catch (error) {
      setDeployStatus("error");
      if (error instanceof Error) {
        setDeployMessage(error?.message || "");
      }
    } finally {
      setDeploymentCompleted(true);
    }
  };

  const onDeploy = async () => {
    const balance = await isBalanceAvailable("deploy");
    if (!balance) {
      showGoogleCaptcha("deploy");
    } else {
      handleDeploy();
    }
  };

  const getTokenBalance = async (captchaToken: string) => {
    try {
      const result = await (
        await fetch(
          `${faucetUrl}/api/claim?walletAddress=${wallet?.wallet.address}&recaptchaToken=${captchaToken}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Platform: "Playground", // Add the custom header here
            },
          }
        )
      ).json();
      return result.isSuccess;
    } catch (err) {
      return false;
    }
  };

  const checkBalanceRecursive = async () => {
    let hasBalance = await isBalanceAvailable();
    if (!hasBalance) {
      // wait 1s before checking again
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return await checkBalanceRecursive();
    }
    return true;
  };

  const handleCaptchaSuccess = async (captchaToken: string) => {
    try {
      const res = await getTokenBalance(captchaToken);
      await checkBalanceRecursive();
      if (res) {
        if (captchaType === "deploy") {
          handleDeploy();
        } else {
          handleAudit();
        }
      }
    } catch (err) {
    } finally {
      closeRecaptcha();
      setDeploymentCompleted(true);
    }
  };

  const onReCAPTCHAChange = (token: string | null) => {
    if (token) {
      setIsRecaptchaCheck(false);
      handleCaptchaSuccess(token);
    }
  };

  const closeRecaptcha = () => {
    setIsRecaptchaCheck(false);
    setCheckingBalance("");
    setCaptchaType("");
  };

  const handleAudit = async () => {
    try {
      setAuiditModalOpen(true);
      setIsAuiditing(true);
      const result = await audit(AuditType.DEFAULT);
      if (result?.success) {
        setAuiditResponse({
          success: true,
          codeHash: result.codeHash,
          auditType: result.auditType,
          transactionId: result.transactionId,
          message: result.message,
        });
      } else {
        setAuiditResponse((prev) => ({
          ...prev,
          message: result.message,
        }));
      }
    } catch (error) {
    } finally {
      setIsAuiditing(false);
    }
  };

  const onAudit = async () => {
    const balance = await isBalanceAvailable("audit");
    if (!balance) {
      showGoogleCaptcha("audit");
    } else {
      handleAudit();
    }
  };

  const handleSaveGasFees = async () => {
    try {
      setSaveGasFeeModalOpen(true);
      setIsSaveGasFeeAuditing(true);
      const result = await audit(AuditType.SAVE_GAS_FEE);
      if (result?.success) {
        setAuiditResponse({
          success: true,
          codeHash: result.codeHash,
          auditType: result.auditType,
          transactionId: result.transactionId,
          message: result.message,
        });
      } else {
        setAuiditResponse((prev) => ({
          ...prev,
          message: result.message,
        }));
      }
    } catch (error) {
    } finally {
      setIsSaveGasFeeAuditing(false);
    }
  };

  const HEADER_BUTTONS = [
    {
      title: "AI Auidit",
      disabled: checkingBalance === "audit",
      onClick: onAudit,
      icon:
        checkingBalance === "audit" ? (
          <Loader />
        ) : (
          <ShieldCheck className="w-4 h-4 xl:mr-2" />
        ),
    },
    {
      title: "Save Gas Fees",
      disabled: isSaveGasFeeAuditing,
      onClick: handleSaveGasFees,
      icon: <HandCoins className="w-4 h-4 xl:mr-2" />,
    },
    {
      title: "Build",
      disabled: isBuildModalOpen,
      onClick: onBuild,
      icon: <Terminal />,
    },
    {
      title: "Test",
      disabled: isTestModalOpen,
      onClick: onTest,
      icon: <TestTube2 className="w-4 h-4 xl:mr-2" />,
    },
    {
      title: "Deploy",
      disabled: checkingBalance === "deploy",
      onClick: onDeploy,
      icon: checkingBalance === "deploy" ? <Loader /> : <Deploy />,
    },
    {
      title: "Export",
      disabled: false,
      onClick: exportProject,
      icon: <Export />,
    },
    {
      title: "Share",
      disabled: false,
      onClick: handleShare,
      icon: <Link2 className="w-4 h-4 xl:mr-2" />,
    },
  ];
  return (
    <header className="flex items-center justify-end px-4 py-3 border-b border-gray-700">
      <div className="flex items-center space-x-2">
        {HEADER_BUTTONS.map((data, index) => (
          <Button
            key={index}
            variant="ghost"
            className="text-[0px] xl:text-[12px] 2xl:text-[14px] px-3 xl:px-2 2xl:px-4 text-gray-400 hover:text-white"
            onClick={data.onClick}
            disabled={data.disabled}
          >
            {data.icon} {data.title}
          </Button>
        ))}
      </div>

      <Dialog open={isAuiditModalOpen} onOpenChange={resetAuidit}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">AI Auidit report</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md p-10 auidit-result scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
            {isAuiditing ? (
              <div className="flex items-center justify-center text-sm">
                <Loader /> Loading Report...
              </div>
            ) : (
              <AuditReport
                auditType={auiditResponse.auditType}
                codeHash={auiditResponse.codeHash}
                transactionId={auiditResponse.transactionId}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isSaveGasFeeModalOpen} onOpenChange={resetSaveGasFee}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">Save Gas Fees report</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md p-10 auidit-result scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
            {isAuiditing ? (
              <div className="flex items-center justify-center text-sm">
                <Loader /> Loading Report...
              </div>
            ) : (
              <AuditReport
                auditType={auiditResponse.auditType}
                codeHash={auiditResponse.codeHash}
                transactionId={auiditResponse.transactionId}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isBuildModalOpen} onOpenChange={resetBuild}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Build</DialogTitle>
            <ProgressBar isProcessCompleted={isBuildingCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <div>
                <p
                  className={cn(
                    "text-sm",
                    buildStatus === "success"
                      ? "text-green-400"
                      : buildStatus === "error"
                      ? "text-red-400"
                      : "text-white"
                  )}
                >
                  {!isBuildingCompleted ? "Building..." : buildMessage}
                </p>
              </div>
            </div>
          </div>
          {buildStatus === "success" && isBuildingCompleted && (
            <Button
              variant="outline"
              className="border-gray-700 text-white"
              onClick={() => {
                resetBuild();
                onDeploy();
              }}
            >
              Deploy Now
            </Button>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isTestModalOpen} onOpenChange={resetTest}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="mb-4">Running tests...</DialogTitle>
            <ProgressBar isProcessCompleted={isTestingCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <DialogDescription className="text-white overflow-auto">
                {!isTestingCompleted ? (
                  "Loading..."
                ) : (
                  <FormatErrors inputString={testMessage} />
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isShareModalOpen} onOpenChange={resetShare}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Generate Share Link</DialogTitle>
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <div className="p-3">
              <DialogDescription className="text-white overflow-auto py-3">
                {shareLoading ? (
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
                    {shareMessage}
                  </div>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={isDeployModalOpen} onOpenChange={resetDeploy}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Contract Deployment</DialogTitle>
            <ProgressBar isProcessCompleted={isDeploymentCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <DialogDescription
                className={
                  deployStatus === "error" ? "text-red-400" : "text-white"
                }
              >
                {!isDeploymentCompleted ? (
                  "Deploying..."
                ) : (
                  <div>
                    <p className="text-[13px]">TransactionId: </p>
                    <Link
                      className="text-[12px] underline text-sky-400 block mb-4"
                      href={`https://testnet.aelfscan.io/tDVW/tx/${deployMessage}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {deployMessage}
                    </Link>
                    <Deployment id={deployMessage} />
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
    </header>
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
      <Button variant={"outline"} className="border-gray-600 bg-gray-800 mt-2 text-[13px] px-3">{data.address}</Button>
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
