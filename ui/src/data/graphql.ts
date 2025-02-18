import { AELFSCAN_CLIENT_NAME } from "@/providers/apollo-wrapper";
import { useQuery, gql } from "@apollo/client";

interface GetNetworkDaoProposalReleasedIndexResponse {
  getNetworkDaoProposalReleasedIndex: {
    data: Array<{
      proposalId: string;
      orgType: string;
      transactionInfo: {
        transactionId: string;
      };
    }>;
  };
}

export const useProposalReleaseInfo = (
  proposalIds: string[] = [],
  pollInterval: number = 0
) => {
  return useQuery<GetNetworkDaoProposalReleasedIndexResponse>(
    gql`
      query GetNetworkDaoProposalReleasedIndex(
        $input: GetNetworkDaoProposalReleasedIndexInput!
      ) {
        getNetworkDaoProposalReleasedIndex(input: $input) {
          data {
            proposalId
            orgType
            transactionInfo {
              transactionId
            }
          }
        }
      }
    `,
    {
      variables: {
        input: {
          startBlockHeight: 1,
          endBlockHeight: 4000000000,
          orgType: "PARLIAMENT",
          skipCount: 0,
          maxResultCount: 1,
          proposalIds: proposalIds,
        },
      },
      pollInterval,
      skip: proposalIds.length === 0,
    }
  );
};

interface GetContractListResponse {
  contractList: {
    items: Array<{
      address: string;
      metadata: {
        block: {
          blockTime: string;
        };
      };
    }>;
  };
}

export const useContractList = (author?: string) => {
  return useQuery<GetContractListResponse>(
    gql`
      query ContractList($input: GetContractInfoDto) {
        contractList(input: $input) {
          items {
            address
            metadata {
              block {
                blockTime
              }
            }
          }
        }
      }
    `,
    {
      variables: {
        input: {
          author: author,
          maxResultCount: 1000,
          skipCount: 0,
        },
      },
      skip: !author,
      context: {clientName: AELFSCAN_CLIENT_NAME}
    }
  );
};
