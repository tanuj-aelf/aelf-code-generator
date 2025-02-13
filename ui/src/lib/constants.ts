export const benifits = [
  {
    title: "Natural Language",
    description: "Describe your contract in plain English",
    icon: "💬",
  },
  {
    title: "Best Practices",
    description: "Generated code follows security standards",
    icon: "🛡️",
  },
  {
    title: "Ready to Deploy",
    description: "Get production-ready smart contracts",
    icon: "🚀",
  },
];

interface Suggestion {
  title: string;
  description: string;
  prompt: string;
}

export const INITIAL_SUGGESTIONS: Suggestion[] = [
  {
    title: "Voting System",
    description: "Secure and transparent voting",
    prompt:
      "Create a voting smart contract with voter registration, vote casting, and result tabulation functionality",
  },
  {
    title: "Lottery Game",
    description: "Create a decentralized lottery system",
    prompt:
      "Generate a lottery game smart contract with ticket purchasing, random winner selection, and prize distribution",
  },
  {
    title: "Todo List",
    description: "Decentralized todo list management",
    prompt:
      "Generate a todo list smart contract with features for adding, updating, and completing tasks",
  },
  {
    title: "Dice Game Contract",
    description: "Create a decentralized dice gambling game",
    prompt:
      "Generate a dice game smart contract with betting functionality, random number generation, and reward distribution",
  },
  {
    title: "Donation Contract",
    description: "Build a transparent donation management system",
    prompt:
      "Create a donation smart contract with features for accepting donations, tracking donors, and managing fund distribution",
  },
  {
    title: "Expense Tracker",
    description: "Track and manage expenses on-chain",
    prompt:
      "Generate an expense tracking smart contract with features for recording expenses, categorization, and expense history",
  },

  {
    title: "NFT Contract",
    description: "Create NFT tokens with custom features",
    prompt:
      "Create an NFT smart contract with minting, transferring, and metadata management functionality",
  },
  {
    title: "Simple DAO",
    description: "Basic DAO with governance features",
    prompt:
      "Create a simple DAO smart contract with proposal creation, voting mechanism, and execution of approved proposals",
  },
  {
    title: "Staking Contract",
    description: "Token staking with rewards",
    prompt:
      "Generate a staking smart contract with features for token staking, reward distribution, and withdrawal functionality",
  },
  {
    title: "Tic-Tac-Toe Game",
    description: "On-chain Tic-Tac-Toe game",
    prompt:
      "Create a Tic-Tac-Toe game smart contract with player moves, game state management, and winner verification",
  },
];
