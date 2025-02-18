// https://www.apollographql.com/docs/react/get-started#step-4-connect-your-client-to-react

import { env } from "@/data/env";
import { HttpLink, ApolloLink, ApolloClient, InMemoryCache, ApolloProvider } from "@apollo/client";

const tmrwdaoLink = new HttpLink({
  uri: env.TMRWDAO_GRAPHQL_ENDPOINT,
  fetchOptions: { cache: "no-store" },
});

const aelfscanLink = new HttpLink({
  uri: env.AELFSCAN_GRAPHQL_ENDPOINT,
  fetchOptions: { cache: "no-store" },
});

export const AELFSCAN_CLIENT_NAME = "aelfscanLink";

const client = new ApolloClient({
  cache: new InMemoryCache(),
  link: ApolloLink.split(
    (operation) => operation.getContext().clientName === AELFSCAN_CLIENT_NAME,
    aelfscanLink, //if above
    tmrwdaoLink
  ),
});

// you need to create a component to wrap your app in
export function ApolloWrapper({ children }: React.PropsWithChildren) {
  return (
    <ApolloProvider client={client}>
      {children}
    </ApolloProvider>
  );
}
