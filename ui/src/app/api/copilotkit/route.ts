import { NextRequest, NextResponse } from "next/server";
import * as http from 'http';
import { URL } from 'url';

export const dynamic = 'force-dynamic';
export const maxDuration = 40 * 60; // 40 minutes

interface CustomResponse {
  ok: boolean;
  status: number;
  json: () => Promise<any>;
  text: () => Promise<string>;
}

const makeRequest = async (urlString: string, options: RequestInit): Promise<CustomResponse> => {
  console.log(`Making request to: ${urlString}`);
  const url = new URL(urlString);
  
  return new Promise((resolve, reject) => {
    const requestOptions = {
      hostname: url.hostname,
      port: url.port || '3001',
      path: url.pathname,
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      },
      timeout: 40 * 60 * 1000, // 40 minutes
    };
    
    console.log("Request options:", requestOptions);
    
    const req = http.request(requestOptions, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        console.log(`Response status: ${res.statusCode}`);
        resolve({
          ok: res.statusCode ? res.statusCode >= 200 && res.statusCode < 300 : false,
          status: res.statusCode || 500,
          json: async () => JSON.parse(responseData),
          text: async () => responseData,
        });
      });
    });
    
    req.on('error', (error) => {
      console.error("Request error:", error);
      reject(error);
    });
    
    req.on('timeout', () => {
      console.log('Request timed out');
      req.destroy();
      reject(new Error('Request timed out'));
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
};

export const POST = async (req: NextRequest) => {
  console.log("Received request to /copilotkit endpoint");
  
  try {
    const body = await req.json();
    console.log("Request body:", body);
    
    // Try different endpoint variations to see which works
    const apiUrl = process.env.AGENT_URL || "http://localhost:3001/copilotkit";
    console.log(`Using agent URL: ${apiUrl}`);

    const response = await makeRequest(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      throw new Error(`Agent responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Agent response:", data);

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Error in /copilotkit endpoint:", error);
    
    if (error.message === 'Request timed out') {
      return new Response(JSON.stringify({
        error: "The request timed out after 40 minutes. The model is taking too long to generate a response."
      }), { 
        status: 504,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return NextResponse.json(
      { error: error.message || "Internal Server Error" },
      { status: error.status || 500 }
    );
  }
};
