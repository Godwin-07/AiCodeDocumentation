/**
 * Python bridge module for spawning and communicating with the Python analysis engine.
 * 
 * Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
 */

import { spawn } from 'child_process';
import { PythonEngineInput, PythonEngineOutput, ProgressUpdate, ProgressCallback } from './types';

/**
 * Spawns the Python analysis engine as a child process and communicates via stdin/stdout.
 * 
 * This function:
 * - Spawns a Python child process using child_process.spawn (Requirement 8.1)
 * - Passes PythonEngineInput as JSON via stdin (Requirement 8.2)
 * - Captures stdout and parses JSON output (Requirement 8.3)
 * - Parses progress messages and calls progress callback (Requirements 2.4, 7.3)
 * - Captures stderr for error logging (Requirement 8.4)
 * - Handles process exit codes (Requirement 8.5)
 * 
 * @param input - The input data for the Python engine
 * @param progressCallback - Optional callback for progress updates
 * @returns Promise resolving to PythonEngineOutput
 * @throws Error if Python process fails or returns invalid output
 */
export async function spawnPythonEngine(
  input: PythonEngineInput,
  progressCallback?: ProgressCallback
): Promise<PythonEngineOutput> {
  return new Promise((resolve, reject) => {
    // Spawn Python process (Requirement 8.1)
    // Run main.py directly from the analysis_engine directory
    const path = require('path');
    const fs = require('fs');
    
    // Find the analysis_engine directory
    // Strategy: Look in multiple locations
    let mainPyPath: string | null = null;
    
    // 1. Check if analysis_engine is in the workspace being analyzed (user has it in their project)
    let candidatePath = path.join(input.workspacePath, 'analysis_engine', 'main.py');
    if (fs.existsSync(candidatePath)) {
      mainPyPath = candidatePath;
    }
    
    // 2. Check parent directory of workspace (development mode - test_workspace case)
    if (!mainPyPath) {
      candidatePath = path.join(input.workspacePath, '..', 'analysis_engine', 'main.py');
      if (fs.existsSync(candidatePath)) {
        mainPyPath = candidatePath;
      }
    }
    
    // 3. Check relative to extension directory (packaged extension)
    if (!mainPyPath) {
      candidatePath = path.join(__dirname, '..', '..', 'analysis_engine', 'main.py');
      if (fs.existsSync(candidatePath)) {
        mainPyPath = candidatePath;
      }
    }
    
    // If still not found, error out
    if (!mainPyPath) {
      reject(new Error('Could not find analysis_engine/main.py. Please ensure the Python analysis engine is installed.'));
      return;
    }
    
    console.log(`[Python Bridge] Using analysis engine at: ${mainPyPath}`);
    
    // Try 'python' first (Windows), fallback to 'python3' (Unix)
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
    
    const pythonProcess = spawn(pythonCommand, [mainPyPath], {
      cwd: input.workspacePath, // Run from the workspace being analyzed
      stdio: ['pipe', 'pipe', 'pipe'], // stdin, stdout, stderr
    });

    // Buffers to collect output
    let stdoutData = '';
    let stderrData = '';
    let finalResult: PythonEngineOutput | null = null;

    // Capture stdout and parse line-by-line JSON (Requirements 8.3, 2.4, 7.3)
    pythonProcess.stdout.on('data', (data: Buffer) => {
      stdoutData += data.toString();
      
      // Process complete lines (messages are separated by newlines)
      const lines = stdoutData.split('\n');
      
      // Keep the last incomplete line in the buffer
      stdoutData = lines.pop() || '';
      
      // Parse each complete line as JSON
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue; // Skip empty lines
        
        try {
          const message = JSON.parse(trimmedLine);
          
          // Handle progress messages
          if (message.type === 'progress') {
            const progressMsg = message as ProgressUpdate;
            if (progressCallback) {
              progressCallback(progressMsg.processed, progressMsg.total);
            }
          }
          // Handle result messages
          else if (message.type === 'result') {
            finalResult = message as PythonEngineOutput;
          }
        } catch (error) {
          // Log parse errors but continue processing
          console.error('[Python Engine] Failed to parse JSON line:', trimmedLine);
        }
      }
    });

    // Capture stderr for error logging (Requirement 8.4)
    pythonProcess.stderr.on('data', (data: Buffer) => {
      stderrData += data.toString();
      // Log stderr in real-time for debugging
      console.error('[Python Engine]', data.toString());
    });

    // Handle process exit (Requirement 8.5)
    pythonProcess.on('close', (code: number | null) => {
      // If process exited with non-zero code, reject with error (Requirement 8.5)
      if (code !== 0) {
        const errorMessage = `Python process exited with code ${code}. stderr: ${stderrData}`;
        reject(new Error(errorMessage));
        return;
      }

      // Use the parsed final result if available
      if (finalResult) {
        resolve(finalResult);
        return;
      }

      // Fallback: try to parse any remaining stdout data (backward compatibility)
      // This handles cases where the Python engine doesn't emit "type" field
      const remainingData = stdoutData.trim();
      if (remainingData) {
        try {
          const output: PythonEngineOutput = JSON.parse(remainingData);
          resolve(output);
          return;
        } catch (error) {
          const parseError = error instanceof Error ? error.message : String(error);
          reject(new Error(`Failed to parse Python output as JSON: ${parseError}. stdout: ${remainingData}`));
          return;
        }
      }

      // No result found
      reject(new Error('Python process completed but no result message was received'));
    });

    // Handle process spawn errors
    pythonProcess.on('error', (error: Error) => {
      reject(new Error(`Failed to spawn Python process: ${error.message}`));
    });

    // Pass input as JSON via stdin (Requirement 8.2)
    try {
      const inputJson = JSON.stringify(input);
      pythonProcess.stdin.write(inputJson);
      pythonProcess.stdin.end(); // Close stdin to signal end of input
    } catch (error) {
      const writeError = error instanceof Error ? error.message : String(error);
      pythonProcess.kill(); // Kill the process if we can't write input
      reject(new Error(`Failed to write input to Python process: ${writeError}`));
    }
  });
}
