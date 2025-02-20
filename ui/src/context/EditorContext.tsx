"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { AuditType } from "@/data/audit";

type STATUS = "" | "success" | "error";
type CAPTHA = "" | "audit" | "deploy";
type MODAL = "" | "build" | "deploy" | "test" | "audit" | "saveGas" | "share";
export type AUDIT_RESPONSE_TYPE = {
  success: boolean;
  codeHash: string | undefined;
  auditType: AuditType | "" | undefined;
  transactionId: string | undefined;
  message: string;
};

interface EditorContextType {
  buildDeployStatus: STATUS;
  captchaType: CAPTHA;
  checkingBalance: CAPTHA;
  isRecaptchaCheck: boolean;
  modalOpen: MODAL;
  actionMessage: string;
  isActionCompleted: boolean;
  auiditResponse: AUDIT_RESPONSE_TYPE;
  isActionRunning: boolean;
  shareLink: string;
  setBuildDeployStatus: (status: STATUS) => void;
  setCaptchaType: (type: CAPTHA) => void;
  setCheckingBalance: (type: CAPTHA) => void;
  setIsRecaptchaCheck: (val: boolean) => void;
  setModalOpen: (type: MODAL) => void;
  setActionMessage: (val: string) => void;
  setActionCompleted: (val: boolean) => void;
  setAuiditResponse: (values: AUDIT_RESPONSE_TYPE) => void;
  setActionRunning: (val: boolean) => void;
  setShareLink: (val: string) => void;
}

const EditorContext = createContext<EditorContextType | undefined>(undefined);

export const EditorProvider = ({ children }: { children: ReactNode }) => {
  const [captchaType, setCaptchaType] = useState<CAPTHA>("");
  const [checkingBalance, setCheckingBalance] = useState<CAPTHA>("");

  const [buildDeployStatus, setBuildDeployStatus] = useState<STATUS>("");

  const [isRecaptchaCheck, setIsRecaptchaCheck] = useState<boolean>(false);

  const [modalOpen, setModalOpen] = useState<MODAL>("");

  const [actionMessage, setActionMessage] = useState<string>("");
  const [isActionCompleted, setActionCompleted] = useState<boolean>(false);
  const [isActionRunning, setActionRunning] = useState<boolean>(false);

  const [shareLink, setShareLink] = useState<string>("");
  const [auiditResponse, setAuiditResponse] = useState<AUDIT_RESPONSE_TYPE>({
    success: false,
    codeHash: "",
    auditType: "",
    transactionId: "",
    message: "",
  });

  return (
    <EditorContext.Provider
      value={{
        buildDeployStatus,
        captchaType,
        checkingBalance,
        isRecaptchaCheck,
        modalOpen,
        actionMessage,
        isActionCompleted,
        auiditResponse,
        isActionRunning,
        shareLink,
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
      }}
    >
      {children}
    </EditorContext.Provider>
  );
};

export const useEditorContext = () => {
  const context = useContext(EditorContext);
  if (!context) {
    throw new Error("useContract must be used within a EditorProvider");
  }
  return context;
};
