import {
  CopilotRuntime,
  GroqAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from '@copilotkit/runtime';
import { NextRequest, NextResponse } from 'next/server';

const serviceAdapter = new GroqAdapter({ model: "llama-3.3-70b-versatile" });
const runtime = new CopilotRuntime();

export const POST = async (req: NextRequest) => {
  try {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter,
      endpoint: '/api/copilot',
    });

    return handleRequest(req);
  } catch (error: any) {
    console.error('Copilot API Error:', error);
    
    // Handle rate limiting and quota errors specifically
    if (error.status === 429) {
      return NextResponse.json(
        { error: 'Rate limit exceeded. Please try again in a few moments.' },
        { status: 429 }
      );
    }
    
    return NextResponse.json(
      { error: error.message || 'Internal Server Error' },
      { status: error.status || 500 }
    );
  }
}; 