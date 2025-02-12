import { NextRequest, NextResponse } from "next/server";

export const POST = async (req: NextRequest) => {
  console.log("Received request to /copilotkit endpoint");
  
  try {
    const body = await req.json();
    console.log("Request body:", body);
    
    const response = await fetch(process.env.AGENT_URL || "http://localhost:3001/generate", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Agent responded with status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Agent response:", data);

    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Error in /copilotkit endpoint:", error);
    return NextResponse.json(
      { error: error.message || "Internal Server Error" },
      { status: error.status || 500 }
    );
  }
};
