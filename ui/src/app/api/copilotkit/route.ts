// import {
//   CopilotRuntime,
//   GroqAdapter,
//   copilotKitEndpoint,
//   copilotRuntimeNextJSAppRouterEndpoint,
//   langGraphPlatformEndpoint,
// } from '@copilotkit/runtime';
// import { NextRequest, NextResponse } from 'next/server';

// const serviceAdapter = new GroqAdapter({ model: "google_genai" });

// // const runtime = new CopilotRuntime({
// //   remoteEndpoints: [
// //     {
// //       url: process.env.REMOTE_ACTION_URL || "http://localhost:3001/copilotkit",
// //     },
// //   ],
// // });

// const deploymentUrl = "http://localhost:8001/copilotkit"
// const langsmithApiKey = "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";

// const remoteEndpoint = langGraphPlatformEndpoint({
//   deploymentUrl,
//   langsmithApiKey,
//   agents: [
//     {
//       name: "aelf_code_generator",
//       description: "Aelf code generator",
//     },
//   ],
// })

// export const POST = async (req: NextRequest) => {
//   try {

//     // const remoteEndpoint = copilotKitEndpoint({
//     //   url: "http://localhost:3001/copilotkit",
//     // })
//     const runtime = new CopilotRuntime({
//       remoteEndpoints: [remoteEndpoint],
//     });

//     const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
//       runtime,
//       serviceAdapter,
//       endpoint: '/api/copilotkit',
//     });

//     return handleRequest(req);
//   } catch (error: any) {
//     console.error('Copilot API Error:', error);
    
//     // Handle rate limiting and quota errors specifically
//     if (error.status === 429) {
//       return NextResponse.json(
//         { error: 'Rate limit exceeded. Please try again in a few moments.' },
//         { status: 429 }
//       );
//     }
    
//     return NextResponse.json(
//       { error: error.message || 'Internal Server Error' },
//       { status: error.status || 500 }
//     );
//   }
// }; 

// import {
//   CopilotRuntime,
//   copilotRuntimeNextJSAppRouterEndpoint,
//   GroqAdapter,
//   langGraphPlatformEndpoint,
// } from '@copilotkit/runtime';
// import { NextRequest, NextResponse } from 'next/server';

// // Update model to use Google's Gemini model to match agent configuration
// const serviceAdapter = new GroqAdapter({ model: "google_genai" });

// // Configure the deployment URL to point to the agent's endpoint
// const deploymentUrl = "http://localhost:3001/copilotkit"
// const langsmithApiKey = "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";

// // Configure the remote endpoint to use the AELF code generator agent
// const remoteEndpoint = langGraphPlatformEndpoint({
//   deploymentUrl,
//   langsmithApiKey,
//   agents: [
//     {
//       name: "aelf_code_generator",
//       description: "Generates AELF smart contract code based on natural language descriptions",
//     },
//   ],
// })

// export const POST = async (req: NextRequest) => {
//   try {
//     const runtime = new CopilotRuntime({
//       remoteEndpoints: [remoteEndpoint],
//     });

//     const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
//       runtime,
//       serviceAdapter,
//       endpoint: '/api/copilotkit',
//     });

//     return handleRequest(req);
//   } catch (error: any) {
//     console.error('Copilot API Error:', error);
    
//     if (error.status === 429) {
//       return NextResponse.json(
//         { error: 'Rate limit exceeded. Please try again in a few moments.' },
//         { status: 429 }
//       );
//     }
    
//     return NextResponse.json(
//       { error: error.message || 'Internal Server Error' },
//       { status: error.status || 500 }
//     );
//   }
// };




import {
  CopilotRuntime,
  GroqAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  langGraphPlatformEndpoint, copilotKitEndpoint,
} from "@copilotkit/runtime";
import Groq from "groq-sdk";
import { NextRequest } from "next/server";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const llmAdapter = new GroqAdapter({ groq, model: "google_genai"  } as any);
const langsmithApiKey = process.env.LANGSMITH_API_KEY as string || "";

export const POST = async (req: NextRequest) => {
  const searchParams = req.nextUrl.searchParams
  const deploymentUrl = searchParams.get('lgcDeploymentUrl') || process.env.LGC_DEPLOYMENT_URL;

  const remoteEndpoint = deploymentUrl ? langGraphPlatformEndpoint({
    deploymentUrl,
    langsmithApiKey,
    agents: [
      {
        name: "aelf_code_generator",
        description: "Aelf code generator",
      },
    ],
  }) : copilotKitEndpoint({
    url: process.env.REMOTE_ACTION_URL || "http://localhost:3001/copilotkit",
  })

  const runtime = new CopilotRuntime({
    remoteEndpoints: [remoteEndpoint],
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: llmAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
