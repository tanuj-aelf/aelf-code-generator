import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

const execAsync = promisify(exec);

export async function POST(req: Request) {
  try {
    const { folderStructure } = await req.json();
    
    // Create a temporary directory with a unique name
    const tempDir = path.join(os.tmpdir(), 'aelf-contract-' + Date.now());
    await fs.mkdir(tempDir, { recursive: true });

    // Write files to temp directory
    const writeFiles = async (structure: any, currentPath: string) => {
      for (const [name, content] of Object.entries(structure)) {
        const filePath = path.join(currentPath, name);
        if (typeof content === 'string') {
          // Create directories if they don't exist
          await fs.mkdir(path.dirname(filePath), { recursive: true });
          await fs.writeFile(filePath, content);
        } else {
          await fs.mkdir(filePath, { recursive: true });
          await writeFiles(content, filePath);
        }
      }
    };

    await writeFiles(folderStructure, tempDir);

    // Find the .csproj file
    let csprojFile = '';
    const findCsprojFile = async (dir: string): Promise<string> => {
      const files = await fs.readdir(dir, { withFileTypes: true });
      
      for (const file of files) {
        const fullPath = path.join(dir, file.name);
        if (file.isDirectory()) {
          const found = await findCsprojFile(fullPath);
          if (found) return found;
        } else if (file.name.endsWith('.csproj')) {
          return fullPath;
        }
      }
      return '';
    };

    csprojFile = await findCsprojFile(tempDir);

    if (!csprojFile) {
      throw new Error('No .csproj file found in the project');
    }

    // Get the directory containing the .csproj file
    const projectDir = path.dirname(csprojFile);

    // Run dotnet restore first
    try {
      const { stdout: restoreOutput, stderr: restoreError } = await execAsync('dotnet restore', { 
        cwd: projectDir,
        env: { ...process.env, DOTNET_CLI_HOME: tempDir }
      });
      console.log('Restore output:', restoreOutput);
      if (restoreError) console.error('Restore error:', restoreError);
    } catch (error) {
      console.error('Restore failed:', error);
      throw new Error(`Restore failed: ${(error as Error).message}`);
    }

    // Then run dotnet build
    try {
      const { stdout, stderr } = await execAsync('dotnet build', { 
        cwd: projectDir,
        env: { ...process.env, DOTNET_CLI_HOME: tempDir }
      });

      // Clean up
      await fs.rm(tempDir, { recursive: true, force: true });

      if (stderr) {
        console.error('Build stderr:', stderr);
        return NextResponse.json({ 
          success: false, 
          error: stderr 
        }, { status: 400 });
      }

      return NextResponse.json({ 
        success: true, 
        output: stdout 
      });

    } catch (error) {
      console.error('Build error:', error);
      // Clean up even if build fails
      await fs.rm(tempDir, { recursive: true, force: true });
      
      throw error;
    }

  } catch (error) {
    console.error('Process error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Build failed: ' + (error as Error).message,
        details: (error as any).stderr || ''
      },
      { status: 500 }
    );
  }
} 