import { useCallback } from "react";
import { Link2, ShieldCheck, TestTube2 } from "lucide-react";

import { useCliCommands } from "@/hooks/useCliActions";
import { useWallet } from "@/data/wallet";
import { env } from "@/data/env";
import { AuditType } from "@/data/audit";
import { useEditorContext } from "@/context/EditorContext";
import { Deploy, Export, HandCoins, Loader, Terminal } from "../../ui/icons";
import HeadeButtons from "./header-buttons";
import Dialogs from "./dailogs";
import "./style.css";

const faucetUrl = env.FAUCET_API_URL;

export const EditorHeader = () => {
  const wallet = useWallet();
  const {
    captchaType,
    checkingBalance,
    modalOpen,
    isActionRunning,
    setBuildDeployStatus,
    setCaptchaType,
    setCheckingBalance,
    setIsRecaptchaCheck,
    setModalOpen,
    setActionMessage,
    setActionCompleted,
    setAuiditResponse,
    setActionRunning,
    setShareLink,
  } = useEditorContext();
  const { build, deploy, exportProject, test, share, audit } = useCliCommands();

  const onBuild = useCallback(async () => {
    setModalOpen("build");
    const result = await build();
    setBuildDeployStatus(result?.success ? "success" : "error");
    setActionMessage(result?.message || "");
    setActionCompleted(true);
  }, [build]);

  const onTest = useCallback(async () => {
    setModalOpen("test");
    const result = await test();
    setActionMessage(result || "");
    setActionCompleted(true);
  }, [test]);

  const handleShare = async () => {
    setActionRunning(true);
    setModalOpen("share");
    const result = await share();
    if (result.success) {
      setShareLink(result.link);
    }
    setActionMessage(result.message);
    setActionRunning(false);
  };

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
      setModalOpen("deploy");
      const result = await deploy();
      setBuildDeployStatus(result?.success ? "success" : "error");
      setActionMessage(result?.message || "");
    } catch (error) {
      setBuildDeployStatus("error");
      if (error instanceof Error) {
        setActionMessage(error?.message || "");
      }
    } finally {
      setActionCompleted(true);
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
    let hasBalance = await isBalanceAvailable(captchaType);
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
          handleAudit(AuditType.DEFAULT);
        }
      }
    } catch (err) {
    } finally {
      closeRecaptcha();
      setActionCompleted(true);
    }
  };

  const closeRecaptcha = () => {
    setIsRecaptchaCheck(false);
    setCheckingBalance("");
    setCaptchaType("");
  };

  const handleAudit = async (type: AuditType) => {
    try {
      setModalOpen(type === AuditType.DEFAULT ? "audit" : "saveGas");
      setActionRunning(true);
      const result = await audit(type);
      if (result?.success) {
        setAuiditResponse({
          success: true,
          codeHash: result.codeHash,
          auditType: result.auditType,
          transactionId: result.transactionId,
          message: result.message,
        });
      } else {
        setAuiditResponse({
          success: false,
          codeHash: "",
          auditType: "",
          transactionId: "",
          message: result?.message || "",
        });
      }
    } catch (error) {
    } finally {
      setActionRunning(false);
    }
  };

  const onAudit = async () => {
    const balance = await isBalanceAvailable("audit");
    if (!balance) {
      showGoogleCaptcha("audit");
    } else {
      handleAudit(AuditType.DEFAULT);
    }
  };

  const HEADER_BUTTONS = [
    {
      title: "AI Audit",
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
      disabled: isActionRunning,
      onClick: () => handleAudit(AuditType.SAVE_GAS_FEE),
      icon: <HandCoins className="w-4 h-4 xl:mr-2" />,
    },
    {
      title: "Build",
      disabled: modalOpen === "build",
      onClick: onBuild,
      icon: <Terminal />,
    },
    {
      title: "Test",
      disabled: modalOpen === "test",
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
        <HeadeButtons headerButtons={HEADER_BUTTONS} />
      </div>
      <Dialogs
        handleCaptchaSuccess={handleCaptchaSuccess}
        onDeploy={onDeploy}
        closeRecaptcha={closeRecaptcha}
      />
    </header>
  );
};
