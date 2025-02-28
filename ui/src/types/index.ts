export interface FolderStructure {
  [key: string]: string | FolderStructure;
}

export interface GeneratedFile {
  path: string;
  content: string;
  file_type: string;
}

export interface AgentResponse {
  test_contract: {
    generate: {
      _internal: {
        output: {
          reference: any;
          contract: GeneratedFile;
          state: GeneratedFile;
          proto: GeneratedFile;
          project: GeneratedFile;
          metadata: GeneratedFile[];
        };
      };
    };
  }
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
} 