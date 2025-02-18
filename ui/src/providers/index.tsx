"use client";

import { PropsWithChildren } from "react";
import { ApolloWrapper } from "./apollo-wrapper";
import { ContractProvider } from "@/context/ContractContext";

export default function Providers({ children }: PropsWithChildren) {
  return (
    <ContractProvider>
      <ApolloWrapper>{children}</ApolloWrapper>
    </ContractProvider>
  );
}
