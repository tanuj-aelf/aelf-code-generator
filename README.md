# AElf Code Generator

An AI-powered code generator for the AElf ecosystem, built with Next.js, CopilotKit, and OpenAI.

## Features

- AI-powered code generation for smart contracts and dApps
- Real-time code suggestions and completions
- Built-in examples and templates for common use cases
- Modern, responsive UI with Tailwind CSS

## Prerequisites

- Node.js 18+ and npm
- OpenAI API key

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Copy `.env.local.example` to `.env.local` and add your API keys:
   ```bash
   # UI Environment Variables
   NEXT_PUBLIC_RUNTIME_URL=http://localhost:3000/api/copilotkit
   AGENT_URL=http://localhost:3001/copilotkit/generate 
   GROQ_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
   NEXT_PUBLIC_FAUCET_API_URL=https://faucet.aelf.dev
   NEXT_PUBLIC_GOOGLE_CAPTCHA_SITEKEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Agent Environment Variables
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   MODEL=azure_openai
   AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # LangSmith Tracing (optional)
   LANGSMITH_TRACING=true
   LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
   LANGSMITH_API_KEY="lsv2_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   LANGSMITH_PROJECT="ai-code-generator"
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Technology Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- CopilotKit
- OpenAI API
- Vercel Analytics

## License

MIT 