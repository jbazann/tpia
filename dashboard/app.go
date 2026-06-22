package main

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"

	_ "modernc.org/sqlite"
)

// App struct
type App struct {
	ctx    context.Context
	dbPath string
}

// FileInfo holds information about a file in the temporary directory
type FileInfo struct {
	FileName string `json:"fileName"`
	FilePath string `json:"filePath"`
	Status   string `json:"status"`
}

// Rule representa una regla de auditoría en la base de datos
type Rule struct {
	ID          int    `json:"id"`
	RuleName    string `json:"rule_name"`
	Priority    int    `json:"priority"`
	TargetAgent string `json:"target_agent"`
	ActionType  string `json:"action_type"`
	Payload     string `json:"payload"`
	IsActive    bool   `json:"is_active"`
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.dbPath = a.findRulesDB()
}

// findRulesDB intenta localizar la base de datos rules.db del agente
func (a *App) findRulesDB() string {
	execPath, err := os.Executable()
	if err != nil {
		return ""
	}
	dashboardDir := filepath.Dir(execPath)

	candidates := []string{
		filepath.Join(dashboardDir, "data", "rules.db"),
		filepath.Join(dashboardDir, "agente", "data", "rules.db"),
		filepath.Join(dashboardDir, "..", "agente", "data", "rules.db"),
		filepath.Join(dashboardDir, "..", "..", "agente", "data", "rules.db"),
		// Modo desarrollo: desde dashboard/
		filepath.Join("..", "agente", "data", "rules.db"),
		filepath.Join("..", "..", "agente", "data", "rules.db"),
	}

	for _, p := range candidates {
		abs, err := filepath.Abs(p)
		if err != nil {
			continue
		}
		if _, err := os.Stat(abs); err == nil {
			return abs
		}
	}
	return ""
}

// openDB abre la conexión SQLite y la inicializa si no existe
func (a *App) openDB() (*sql.DB, error) {
	if a.dbPath == "" {
		// Si no se encontró, creamos una por defecto
		execPath, err := os.Executable()
		if err != nil {
			return nil, err
		}
		dashboardDir := filepath.Dir(execPath)
		
		// Intentar buscar directorio relativo de agente en desarrollo o crear localmente
		var targetPath string
		if _, err := os.Stat(filepath.Join("..", "agente", "data")); err == nil {
			targetPath = filepath.Join("..", "agente", "data", "rules.db")
		} else {
			targetPath = filepath.Join(dashboardDir, "data", "rules.db")
		}
		
		absPath, err := filepath.Abs(targetPath)
		if err != nil {
			return nil, err
		}
		
		// Crear los directorios correspondientes si no existen
		err = os.MkdirAll(filepath.Dir(absPath), 0755)
		if err != nil {
			return nil, fmt.Errorf("no se pudieron crear directorios para la base de datos: %w", err)
		}
		a.dbPath = absPath
	}

	db, err := sql.Open("sqlite", a.dbPath)
	if err != nil {
		return nil, err
	}

	// Crear la tabla si no existe de forma preventiva
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS rules (
			id          INTEGER PRIMARY KEY AUTOINCREMENT,
			rule_name   TEXT    NOT NULL UNIQUE,
			priority    INTEGER DEFAULT 0,
			target_agent TEXT   NOT NULL,
			action_type TEXT    DEFAULT 'invoke_subagent',
			payload     TEXT,
			is_active   INTEGER DEFAULT 1
		)
	`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("error al inicializar tabla de reglas: %w", err)
	}

	return db, nil
}

// ─────────────────────────────────────────────────────────
// CRUD de Reglas — expuestos como bindings a React
// ─────────────────────────────────────────────────────────

// GetRules devuelve todas las reglas de la base de datos
func (a *App) GetRules() ([]Rule, error) {
	db, err := a.openDB()
	if err != nil {
		return nil, err
	}
	defer db.Close()

	rows, err := db.Query(`
		SELECT id, rule_name, priority, target_agent, action_type,
		       COALESCE(payload, ''), is_active
		FROM rules
		ORDER BY priority ASC
	`)
	if err != nil {
		return nil, fmt.Errorf("error al consultar reglas: %w", err)
	}
	defer rows.Close()

	var rules []Rule
	for rows.Next() {
		var r Rule
		var isActive int
		if err := rows.Scan(&r.ID, &r.RuleName, &r.Priority, &r.TargetAgent,
			&r.ActionType, &r.Payload, &isActive); err != nil {
			return nil, err
		}
		r.IsActive = isActive == 1
		rules = append(rules, r)
	}
	return rules, nil
}

// AddRule agrega una nueva regla a la base de datos
func (a *App) AddRule(ruleName, targetAgent, actionType, payload string, priority int) (int64, error) {
	if ruleName == "" || targetAgent == "" {
		return 0, fmt.Errorf("rule_name y target_agent son obligatorios")
	}
	db, err := a.openDB()
	if err != nil {
		return 0, err
	}
	defer db.Close()

	result, err := db.Exec(`
		INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
		VALUES (?, ?, ?, ?, ?, 1)
	`, ruleName, priority, targetAgent, actionType, payload)
	if err != nil {
		return 0, fmt.Errorf("error al insertar regla: %w", err)
	}
	return result.LastInsertId()
}

// UpdateRule actualiza una regla existente por ID
func (a *App) UpdateRule(id int, ruleName, targetAgent, actionType, payload string, priority int, isActive bool) error {
	db, err := a.openDB()
	if err != nil {
		return err
	}
	defer db.Close()

	activeInt := 0
	if isActive {
		activeInt = 1
	}

	_, err = db.Exec(`
		UPDATE rules
		SET rule_name=?, priority=?, target_agent=?, action_type=?, payload=?, is_active=?
		WHERE id=?
	`, ruleName, priority, targetAgent, actionType, payload, activeInt, id)
	if err != nil {
		return fmt.Errorf("error al actualizar regla %d: %w", id, err)
	}
	return nil
}

// DeleteRule elimina una regla por ID
func (a *App) DeleteRule(id int) error {
	db, err := a.openDB()
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec(`DELETE FROM rules WHERE id = ?`, id)
	if err != nil {
		return fmt.Errorf("error al eliminar regla %d: %w", id, err)
	}
	return nil
}

// ToggleRule activa o desactiva una regla sin eliminarla
func (a *App) ToggleRule(id int, isActive bool) error {
	db, err := a.openDB()
	if err != nil {
		return err
	}
	defer db.Close()

	activeInt := 0
	if isActive {
		activeInt = 1
	}
	_, err = db.Exec(`UPDATE rules SET is_active=? WHERE id=?`, activeInt, id)
	return err
}

// GetAgentLogs reads the observability log file generated by the Python agent
func (a *App) GetAgentLogs() (string, error) {
	execPath, err := os.Executable()
	if err != nil {
		return "Error interno al buscar logs.", err
	}
	dashboardDir := filepath.Dir(execPath)
	
	candidates := []string{
		filepath.Join(dashboardDir, "data", "logs", "agent_observability.log"),
		filepath.Join(dashboardDir, "agente", "data", "logs", "agent_observability.log"),
		filepath.Join(dashboardDir, "..", "agente", "data", "logs", "agent_observability.log"),
		filepath.Join(dashboardDir, "..", "..", "agente", "data", "logs", "agent_observability.log"),
		filepath.Join("..", "agente", "data", "logs", "agent_observability.log"),
	}

	for _, p := range candidates {
		abs, err := filepath.Abs(p)
		if err != nil {
			continue
		}
		if _, err := os.Stat(abs); err == nil {
			content, err := os.ReadFile(abs)
			if err == nil {
				return string(content), nil
			}
		}
	}
	return "No hay logs disponibles aún. Ejecute el agente procesando un archivo al menos una vez para generarlos.", nil
}

// ─────────────────────────────────────────────────────────
// Funciones existentes de manejo de archivos y agente
// ─────────────────────────────────────────────────────────

// Greet returns a greeting for the given name
func (a *App) Greet(name string) string {
	return fmt.Sprintf("Hello %s, It's show time!", name)
}

// SaveTemporaryFile saves a file to the temporary directory and returns its path
func (a *App) SaveTemporaryFile(fileName string, fileData []byte) (map[string]interface{}, error) {
	tempDir := filepath.Join(os.TempDir(), "tpia-dashboard")
	if err := os.MkdirAll(tempDir, os.ModePerm); err != nil {
		return nil, fmt.Errorf("failed to create temp directory: %w", err)
	}

	filePath := filepath.Join(tempDir, fileName)
	if err := os.WriteFile(filePath, fileData, 0644); err != nil {
		return nil, fmt.Errorf("failed to write file: %w", err)
	}

	return map[string]interface{}{
		"fileName": fileName,
		"filePath": filePath,
		"status":   "pendiente",
	}, nil
}

// findVenvPython busca un intérprete de Python dentro de un entorno virtual (venv)
func findVenvPython(agentDir string) string {
	execPath, err := os.Executable()
	var dashboardDir string
	if err == nil {
		dashboardDir = filepath.Dir(execPath)
	}

	candidates := []string{
		// Relativo a agentDir (por ejemplo, si agentDir es ../agente, el venv suele estar en ../venv)
		filepath.Join(agentDir, "..", "venv", "bin", "python3"),
		filepath.Join(agentDir, "..", "venv", "bin", "python"),
		filepath.Join(agentDir, "..", "venv", "Scripts", "python.exe"),

		// Relativo al directorio actual de ejecución o al directorio padre del dashboard
		filepath.Join("..", "venv", "bin", "python3"),
		filepath.Join("..", "venv", "bin", "python"),
		filepath.Join("..", "venv", "Scripts", "python.exe"),
		filepath.Join("venv", "bin", "python3"),
		filepath.Join("venv", "bin", "python"),
		filepath.Join("venv", "Scripts", "python.exe"),
	}

	if dashboardDir != "" {
		candidates = append(candidates,
			filepath.Join(dashboardDir, "..", "venv", "bin", "python3"),
			filepath.Join(dashboardDir, "..", "venv", "bin", "python"),
			filepath.Join(dashboardDir, "..", "venv", "Scripts", "python.exe"),
		)
	}

	for _, p := range candidates {
		abs, err := filepath.Abs(p)
		if err != nil {
			continue
		}
		if _, err := os.Stat(abs); err == nil {
			return abs
		}
	}
	return ""
}

// ExecuteAgent executes the Python agent with the given file path
func (a *App) ExecuteAgent(filePath string, prompt string) (map[string]interface{}, error) {
	agentDir := findAgentDirectory()
	if agentDir == "" {
		return map[string]interface{}{
			"success": false,
			"status":  "error",
			"error":   "No se pudo encontrar el directorio del agente",
			"output":  "",
		}, nil
	}

	var cmd *exec.Cmd
	if isExecutable(agentDir) {
		if prompt != "" {
			cmd = exec.Command(agentDir, "-f", filePath, "-p", prompt)
		} else {
			cmd = exec.Command(agentDir, "-f", filePath)
		}
		cmd.Dir = filepath.Dir(agentDir)
	} else {
		pythonCmd := findVenvPython(agentDir)
		if pythonCmd == "" {
			if runtime.GOOS == "windows" {
				pythonCmd = "python"
			} else {
				pythonCmd = "python3"
			}
		}
		if prompt != "" {
			cmd = exec.Command(pythonCmd, filepath.Join(agentDir, "main.py"), "-f", filePath, "-p", prompt)
		} else {
			cmd = exec.Command(pythonCmd, filepath.Join(agentDir, "main.py"), "-f", filePath)
		}
		cmd.Dir = agentDir
	}

	output, err := cmd.CombinedOutput()
	if err != nil {
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

func isExecutable(path string) bool {
	fileInfo, err := os.Stat(path)
	if err != nil || fileInfo.IsDir() {
		return false
	}
	if runtime.GOOS == "windows" {
		return filepath.Ext(path) == ".exe"
	}
	return (fileInfo.Mode() & 0111) != 0
}

func findAgentDirectory() string {
	execPath, err := os.Executable()
	if err == nil {
		dashboardDir := filepath.Dir(execPath)
		exeNames := []string{"agente.exe", "agente"}
		for _, exeName := range exeNames {
			if p := filepath.Join(dashboardDir, exeName); fileExists(p) {
				return p
			}
			if p := filepath.Join(filepath.Dir(dashboardDir), exeName); fileExists(p) {
				return p
			}
		}
	}

	cwd, err := os.Getwd()
	if err == nil {
		for _, exeName := range []string{"agente.exe", "agente"} {
			if p := filepath.Join(cwd, exeName); fileExists(p) {
				return p
			}
		}
	}

	if agentPath := os.Getenv("TPIA_AGENT_PATH"); agentPath != "" && fileExists(agentPath) {
		return agentPath
	}

	return findAgentSourceDirectory()
}

func findAgentSourceDirectory() string {
	candidates := []string{
		"../../agente", "../agente", "./agente",
		"/opt/tpia/agente", `C:\tpia\agente`,
	}
	for _, path := range candidates {
		if fileExists(filepath.Join(path, "main.py")) {
			return path
		}
	}
	return ""
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// CleanupTemporaryFiles removes all files from the temporary directory
func (a *App) CleanupTemporaryFiles() error {
	tempDir := filepath.Join(os.TempDir(), "tpia-dashboard")
	return os.RemoveAll(tempDir)
}
