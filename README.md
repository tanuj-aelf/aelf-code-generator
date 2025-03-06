# AElf Code Generator

An AI-powered code generator for the AElf ecosystem, built with Next.js, CopilotKit, and Langgraph.

<img width="1728" alt="Screenshot 2025-03-06 at 12 48 05 PM" src="https://github.com/user-attachments/assets/ecd0aa71-9925-4b46-ae02-99ca866f5932" />
<img width="1725" alt="Screenshot 2025-03-06 at 12 47 52 PM" src="https://github.com/user-attachments/assets/df9a5c2d-fed6-401c-8ede-6c76394c2234" />

## Features

- AI-powered code generation for smart contracts and dApps
- Real-time code suggestions and completions
- Built-in examples and templates for common use cases
- Modern, responsive UI with Tailwind CSS

## Prerequisites

- Node.js 18+ and npm
- OpenAI API key
- Gemini API key

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
4. Set up and run the agent:
   ```bash
   # Navigate to the agent directory
   cd agent
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -e .
   
   # Run the agent
   python3 -m aelf_code_generator
   ```

5. Run the UI development server:
   ```bash
   # Return to the root directory
   cd ../ui
   
   # Start the Next.js server
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser

## Technology Stack

- Next.js 14
- TypeScript
- Tailwind CSS
- CopilotKit
- Gemini embedding withOpenAI API

## License

MIT 
