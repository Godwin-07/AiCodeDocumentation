/**
 * Type definitions for the AI Code Documentation Generator extension
 */

/**
 * Result of workspace file discovery
 */
export interface FileDiscoveryResult {
  /** Absolute paths to source files */
  files: string[];
  /** Number of files excluded by ignore patterns */
  ignoredCount: number;
  /** Any discovery errors encountered */
  errors: string[];
}

/**
 * Ignore pattern from .docignore.txt
 */
export interface IgnorePattern {
  /** Glob pattern from .docignore.txt */
  pattern: string;
  /** Whether pattern targets directories */
  isDirectory: boolean;
}

/**
 * Input data for Python analysis engine
 */
export interface PythonEngineInput {
  /** Absolute path to workspace root */
  workspacePath: string;
  /** List of files to analyze */
  files: string[];
  /** LLM API endpoint URL */
  llmEndpoint: string;
  /** LLM request timeout in seconds */
  llmTimeout: number;
  /** LLM model name */
  llmModel: string;
  /** Documentation template style (optional) */
  template?: string;
  /** Mode of operation (optional) */
  mode?: string;
  /** Output file name (optional) */
  outputFileName?: string;
  /** Backup path (optional) */
  backupPath?: string;
}

/**
 * Output from Python analysis engine
 */
export interface PythonEngineOutput {
  /** Whether documentation generation succeeded */
  success: boolean;
  /** Path to generated DOCUMENTATION.md */
  documentationPath?: string;
  /** Number of files successfully processed */
  filesProcessed: number;
  /** Number of files skipped due to errors */
  filesSkipped: number;
  /** List of errors encountered */
  errors: string[];
}

/**
 * Progress update from Python engine
 * Format: {"type": "progress", "processed": N, "total": M}
 */
export interface ProgressUpdate {
  /** Type of message */
  type: 'progress';
  /** Number of files processed so far */
  processed: number;
  /** Total number of files to process */
  total: number;
}

/**
 * Result message from Python engine
 * Format: {"type": "result", "success": true, ...}
 */
export interface ResultMessage extends PythonEngineOutput {
  /** Type of message */
  type: 'result';
}

/**
 * Callback function for progress updates
 */
export type ProgressCallback = (processed: number, total: number) => void;
