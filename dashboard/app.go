package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

// App struct
type App struct {
	ctx context.Context
}

// FileInfo holds information about a file in the temporary directory
type FileInfo struct {
	FileName string `json:"fileName"`
	FilePath string `json:"filePath"`
	Status   string `json:"status"`
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts. The context is saved
// so we can call the runtime methods
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// Greet returns a greeting for the given name
func (a *App) Greet(name string) string {
	return fmt.Sprintf("Hello %s, It's show time!", name)
}

// SaveTemporaryFile saves a file to the temporary directory and returns its path
func (a *App) SaveTemporaryFile(fileName string, fileData []byte) (map[string]interface{}, error) {
	// Create temp directory if it doesn't exist
	tempDir := filepath.Join(os.TempDir(), "tpia-dashboard")
	if err := os.MkdirAll(tempDir, os.ModePerm); err != nil {
		return nil, fmt.Errorf("failed to create temp directory: %w", err)
	}

	// Create full file path
	filePath := filepath.Join(tempDir, fileName)

	// Write file
	if err := os.WriteFile(filePath, fileData, 0644); err != nil {
		return nil, fmt.Errorf("failed to write file: %w", err)
	}

	return map[string]interface{}{
		"fileName": fileName,
		"filePath": filePath,
		"status":   "pendiente",
	}, nil
}

// ExecuteAgent executes the Python agent with the given file path
func (a *App) ExecuteAgent(filePath string, prompt string) (map[string]interface{}, error) {

	// Find the agent directory
	agentDir := findAgentDirectory()
	if agentDir == "" {
		return map[string]interface{}{
			"success": false,
			"status":  "error",
			"error":   "No se pudo encontrar el directorio del agente",
			"output":  "",
		}, nil
	}

	// Build the command - check if it's an executable or a Python script
	var cmd *exec.Cmd

	// Check if agentDir is a Python script directory or an executable path
	if isExecutable(agentDir) {
		// agentDir is the path to the compiled executable (agente.exe or agente)
		if prompt != "" {
			cmd = exec.Command(agentDir, "-f", filePath, "-p", prompt)
		} else {
			cmd = exec.Command(agentDir, "-f", filePath)
		}
	} else {
		// agentDir is a directory with main.py - use Python interpreter
		var pythonCmd string
		if runtime.GOOS == "windows" {
			pythonCmd = "python"
		} else {
			pythonCmd = "python3"
		}

		if prompt != "" {
			cmd = exec.Command(pythonCmd, filepath.Join(agentDir, "main.py"), "-f", filePath, "-p", prompt)
		} else {
			cmd = exec.Command(pythonCmd, filepath.Join(agentDir, "main.py"), "-f", filePath)
		}
		// Set the working directory to the agent directory to ensure config.yaml is found
		cmd.Dir = agentDir
	}

	// Capture output
	output, err := cmd.CombinedOutput()
	if err != nil {
		// Command failed, but we return the output anyway so the user can see what went wrong
		return map[string]interface{}{
			"success": false,
			"status":  "error",
			"error":   err.Error(),
			"output":  string(output),
		}, nil
	}

	return map[string]interface{}{
		"success": true,
		"status":  "procesado",
		"output":  string(output),
	}, nil
}

// isExecutable checks if a path is an executable file
func isExecutable(path string) bool {
	fileInfo, err := os.Stat(path)
	if err != nil {
		return false
	}

	// Check if it's a file and has .exe extension (Windows) or is executable (Unix)
	if fileInfo.IsDir() {
		return false
	}

	if runtime.GOOS == "windows" {
		return filepath.Ext(path) == ".exe"
	} else {
		return (fileInfo.Mode() & 0111) != 0
	}
}

// findAgentDirectory attempts to locate the agent directory or executable
func findAgentDirectory() string {
	// Try multiple potential paths for compiled executable first

	// 1. Check for executable in the same directory as the dashboard
	execPath, err := os.Executable()
	if err == nil {
		dashboardDir := filepath.Dir(execPath)

		// Check for agente.exe (Windows) or agente (Unix)
		exeNames := []string{"agente.exe", "agente"}
		for _, exeName := range exeNames {
			potentialPath := filepath.Join(dashboardDir, exeName)
			if _, err := os.Stat(potentialPath); err == nil {
				return potentialPath
			}
		}

		// Check in parent directory
		parentDir := filepath.Dir(dashboardDir)
		for _, exeName := range exeNames {
			potentialPath := filepath.Join(parentDir, exeName)
			if _, err := os.Stat(potentialPath); err == nil {
				return potentialPath
			}
		}
	}

	// 2. Check for executable in current working directory
	cwd, err := os.Getwd()
	if err == nil {
		exeNames := []string{"agente.exe", "agente"}
		for _, exeName := range exeNames {
			potentialPath := filepath.Join(cwd, exeName)
			if _, err := os.Stat(potentialPath); err == nil {
				return potentialPath
			}
		}
	}

	// 3. Check if TPIA_AGENT_PATH environment variable is set (can be executable or directory)
	if agentPath := os.Getenv("TPIA_AGENT_PATH"); agentPath != "" {
		if _, err := os.Stat(agentPath); err == nil {
			return agentPath
		}
	}

	// 4. Fall back to source directory (development)
	sourceDir := findAgentSourceDirectory()
	if sourceDir != "" {
		return sourceDir
	}

	return ""
}

// findAgentSourceDirectory attempts to locate the agent Python source directory
func findAgentSourceDirectory() string {
	// Try relative paths from development perspective
	potentialPaths := []string{
		"../../agente",
		"../agente",
		"./agente",
		"/opt/tpia/agente", // Unix-like
		"C:\\tpia\\agente", // Windows
	}

	for _, path := range potentialPaths {
		mainPy := filepath.Join(path, "main.py")
		if _, err := os.Stat(mainPy); err == nil {
			return path
		}
	}

	return ""
}

// CleanupTemporaryFiles removes all files from the temporary directory
func (a *App) CleanupTemporaryFiles() error {
	tempDir := filepath.Join(os.TempDir(), "tpia-dashboard")
	return os.RemoveAll(tempDir)
}
