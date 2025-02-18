import ReCAPTCHA from "react-google-recaptcha"; // Import reCAPTCHA
import { useState, useCallback, useRef } from "react";
import { Copy, CopyCheck, Link2, TestTube2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCliCommands } from "@/hooks/useCliActions";
import { Deploy, Export, Loader, Terminal } from "../ui/icons";
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

const faucetUrl = env.FAUCET_API_URL;
const captchaSitekey = env.GOOGLE_CAPTCHA_SITEKEY;

export const EditorHeader = () => {
  const [buildStatus, setBuildStatus] = useState<"idle" | "success" | "error">(
    "idle"
  );
  const [deployStatus, setDeployStatus] = useState<"" | "success" | "error">(
    ""
  );
  const recaptchaRef = useRef<ReCAPTCHA>(null);

  const [buildMessage, setBuildMessage] = useState("");
  const [isBuildModalOpen, setBuildModalOpen] = useState(false);
  const [isBuildingCompleted, setBuildingCompleted] = useState(false);

  const [testMessage, setTestMessage] = useState("");
  const [isTestModalOpen, setTestModalOpen] = useState(false);
  const [isTestingCompleted, setTestingCompleted] = useState(false);

  const [checkingBalance, setCheckingBalance] = useState<boolean>(false);
  const [isRecaptchaCheck, setIsRecaptchaCheck] = useState(false);

  const [isDeployModalOpen, setDeployModalOpen] = useState(false);
  const [deployMessage, setDeployMessage] = useState("");
  const [isDeploymentCompleted, setDeploymentCompleted] = useState(false);

  const [isShareModalOpen, setShareModalOpen] = useState(false);
  const [shareLoading, setShareLoading] = useState(false);
  const [shareLink, setShareLink] = useState("");
  const [shareMessage, setShareMessage] = useState("");
  const [copied, setCopied] = useState(false);

  const { build, deploy, exportProject, test, share } = useCliCommands();
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
  },[])
  
  const resetDeploy = useCallback(() => {
    setDeployModalOpen(false);
    setDeploymentCompleted(false);
    setDeployStatus("");
    setDeployMessage("");
  }, []);

  const isBalanceAvailable = async () => {
    try {
      setCheckingBalance(true);
      const tokenContract = await wallet?.getTokenContract();
      const balance = await tokenContract.GetBalance.call({
        symbol: "ELF",
        owner: wallet?.wallet.address,
      });
      if (balance.balance === 0) {
        console.log("Don't have balance");
        return false;
      } else {
        setCheckingBalance(false);
        return true;
      }
    } catch (error) {
      return false;
    }
  };

  const showGoogleCaptcha = () => {
    setIsRecaptchaCheck(true);
  };

  const handleDeploy = async () => {
    const balance = await isBalanceAvailable();
    if (!balance) {
      showGoogleCaptcha();
    } else {
      try {
        setDeployModalOpen(true);
        const result = await deploy();
        console.log("result", result);
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
      setDeployModalOpen(true);
      const res = await getTokenBalance(captchaToken);
      await checkBalanceRecursive();
      setCheckingBalance(false);
      if (res) {
        const result = await deploy();
        setDeployStatus(result?.success ? "success" : "error");
        setDeployMessage(result?.message || "");
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
    setCheckingBalance(false);
  };


  return (
    <header className="flex items-center justify-end px-4 py-3 border-b border-gray-700">
      <div className="flex items-center space-x-2">
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={onBuild}
          disabled={isBuildModalOpen}
        >
          <Terminal /> Build
        </Button>
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={onTest}
          disabled={isBuildModalOpen}
        >
          <TestTube2 className="w-4 h-4 mr-2" /> Test
        </Button>
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={handleDeploy}
          disabled={checkingBalance}
        >
          {checkingBalance ? <Loader /> : <Deploy />} Deploy
        </Button>
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={exportProject}
        >
          <Export />
          Export
        </Button>
        <Button
          variant="ghost"
          className="text-gray-400 hover:text-white"
          onClick={handleShare}
        >
          <Link2 className="w-4 h-4 mr-2" />
          Share
        </Button>
      </div>

      <Dialog open={isBuildModalOpen} onOpenChange={resetBuild}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="mb-4">Build</DialogTitle>
            <ProgressBar isProcessCompleted={isBuildingCompleted} />
          </DialogHeader>
          <div className="w-full border border-gray-700 rounded-md">
            <p className="mb-1 text-sm p-2 py-1 bg-gray-700">Output</p>
            <div className="p-3">
              <DialogDescription
                className={
                  buildStatus === "success"
                    ? "text-green-400"
                    : buildStatus === "error"
                    ? "text-red-400"
                    : "text-white"
                }
              >
                {!isBuildingCompleted ? "Building..." : buildMessage}
              </DialogDescription>
            </div>
          </div>
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
                  deployStatus === "success"
                    ? "text-green-400"
                    : deployStatus === "error"
                    ? "text-red-400"
                    : "text-white"
                }
              >
                {!isDeploymentCompleted ? (
                  "Deploying..."
                ) : (
                  <div className="flex">
                    <p className="mr-1">Deployment Successfull: </p>
                    <a
                      href={`https://testnet.aelfscan.io/tDVW/tx/${deployMessage}`}
                      target="_blank"
                      className="text-white underline"
                    >
                      Click Here
                    </a>
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
