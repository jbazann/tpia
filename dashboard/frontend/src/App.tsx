import { useState, useEffect, useRef } from 'react';
import './App.css';
import { SaveTemporaryFile, ExecuteAgent, CleanupTemporaryFiles, GetRules, AddRule, DeleteRule, ToggleRule, GetAgentLogs, CheckAgentStatus } from "../wailsjs/go/main/App.js";
import utnLogo from './assets/images/logo-utn.png';
import loteriaLogo from './assets/images/logo-loteria.webp';

interface UploadedFile {
    id: string;
    fileName: string;
    filePath: string;
    status: 'pendiente' | 'en proceso' | 'procesado' | 'error';
    output?: string;
    error?: string;
}

interface RuleItem {
    id: number;
    rule_name: string;
    priority: number;
    target_agent: string;
    action_type: string;
    payload: string;
    is_active: boolean;
}

function App() {
    const [activeMenu, setActiveMenu] = useState('reglas');
    const [dragActive, setDragActive] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [isProcessing, setIsProcessing] = useState<string | null>(null);
    const [expandedFileId, setExpandedFileId] = useState<string | null>(null);

    const [rules, setRules] = useState<RuleItem[]>([]);
    const [rulesLoading, setRulesLoading] = useState(false);
    const [rulesError, setRulesError] = useState<string | null>(null);

    const [newRuleName, setNewRuleName] = useState('');
    const [newTargetAgent, setNewTargetAgent] = useState('');
    const [newPayload, setNewPayload] = useState('');
    const [newPriority, setNewPriority] = useState(10);

    const [agentLogs, setAgentLogs] = useState<string>("Cargando logs...");
    const logConsoleRef = useRef<HTMLDivElement>(null);

    const refreshLogs = async () => {
        try {
            const logs = await GetAgentLogs();
            setAgentLogs(logs);
            if (logConsoleRef.current) {
                logConsoleRef.current.scrollTop = logConsoleRef.current.scrollHeight;
            }
        } catch (err) {
            console.error("Error al cargar logs:", err);
            setAgentLogs("Error de conexión al leer los logs del agente.");
        }
    };

    const [serviceStatus, setServiceStatus] = useState<string>("Verificando...");
    const [statusColor, setStatusColor] = useState<string>("var(--gray-400)");

    const updateServiceStatus = async () => {
        try {
            const status = await CheckAgentStatus();
            if (status === 'OK') {
                setServiceStatus('Disponible');
                setStatusColor('#4caf50');
            } else if (status === 'SIN_API_KEY') {
                setServiceStatus('Sin API Key (.env)');
                setStatusColor('#ff9800');
            } else {
                setServiceStatus('Agente No Encontrado');
                setStatusColor('#f44336');
            }
        } catch (e) {
            setServiceStatus('Error');
            setStatusColor('#f44336');
        }
    };

    // Cargar reglas desde la BD al montar la sección de reglas
    const loadRules = async () => {
        setRulesLoading(true);
        setRulesError(null);
        try {
            const data = await GetRules();
            setRules(data || []);
        } catch (err: any) {
            setRulesError(err?.message || 'No se pudieron recuperar las reglas de auditoría. Verifique la conexión con el motor de reglas.');
        } finally {
            setRulesLoading(false);
        }
    };

    useEffect(() => {
        if (activeMenu === 'reglas') loadRules();
        if (activeMenu === 'observabilidad') refreshLogs();
        if (activeMenu === 'agente') updateServiceStatus();
    }, [activeMenu]);

    useEffect(() => {
        updateServiceStatus();
    }, []);

    // Handle drag events for file upload
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    // Process dropped files
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        const files = e.dataTransfer.files;
        processFiles(files);
    };

    // Process selected files
    const handleFileSelect = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = false;
        input.onchange = (e: any) => {
            const files = e.target.files;
            processFiles(files);
        };
        input.click();
    };

    // Process files and save them
    const processFiles = async (files: FileList) => {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileData = await file.arrayBuffer();
            const uint8Array = Array.from(new Uint8Array(fileData));

            try {
                const result = await SaveTemporaryFile(file.name, uint8Array);
                const newFile: UploadedFile = {
                    id: `${Date.now()}-${i}`,
                    fileName: result.fileName,
                    filePath: result.filePath,
                    status: result.status as 'pendiente' | 'en proceso' | 'procesado' | 'error'
                };
                setUploadedFiles(prev => [...prev, newFile]);
            } catch (error) {
                console.error('Error saving file:', error);
                const newFile: UploadedFile = {
                    id: `${Date.now()}-${i}`,
                    fileName: file.name,
                    filePath: '',
                    status: 'error',
                    error: 'Error al guardar el archivo'
                };
                setUploadedFiles(prev => [...prev, newFile]);
            }
        }
    };

    // Execute the agent for a specific file
    const executeAgent = async (fileId: string) => {
        const file = uploadedFiles.find(f => f.id === fileId);
        if (!file) return;

        setIsProcessing(fileId);
        setUploadedFiles(prev =>
            prev.map(f =>
                f.id === fileId
                    ? { ...f, status: 'en proceso' }
                    : f
            )
        );

        try {
            const result = await ExecuteAgent(file.filePath, '');
            setUploadedFiles(prev =>
                prev.map(f =>
                    f.id === fileId
                        ? {
                            ...f,
                            status: result.success ? 'procesado' : 'error',
                            output: result.output,
                            error: result.error
                        }
                        : f
                )
            );
            
            if (result.success) {
                // Auto-expand output on success
                setExpandedFileId(fileId);
            }
        } catch (error) {
            console.error('Error executing agent:', error);
            setUploadedFiles(prev =>
                prev.map(f =>
                    f.id === fileId
                        ? {
                            ...f,
                            status: 'error',
                            error: 'Error al ejecutar el agente'
                        }
                        : f
                )
            );
        } finally {
            setIsProcessing(null);
        }
    };

    // Delete a file from the list
    const deleteFile = (fileId: string) => {
        if (expandedFileId === fileId) {
            setExpandedFileId(null);
        }
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    // Add a new rule to the DB
    const handleAddRule = async () => {
        if (!newRuleName.trim()) return;
        try {
            // Se inyectan de forma transparente los campos técnicos requeridos por el backend SQLite
            const targetAgent = "legal_evaluation_flow";
            const priority = 10;
            const actionType = "invoke_subagent";
            await AddRule(newRuleName.trim(), targetAgent, actionType, newPayload.trim(), priority);
            setNewRuleName('');
            setNewPayload('');
            await loadRules();
        } catch (err: any) {
            alert('Error al agregar regla: ' + (err?.message || err));
        }
    };

    // Delete a rule from the DB
    const handleDeleteRule = async (ruleId: number) => {
        try {
            await DeleteRule(ruleId);
            await loadRules();
        } catch (err: any) {
            alert('Error al eliminar regla: ' + (err?.message || err));
        }
    };

    // Toggle active state
    const handleToggleRule = async (ruleId: number, currentActive: boolean) => {
        try {
            await ToggleRule(ruleId, !currentActive);
            await loadRules();
        } catch (err: any) {
            alert('Error al actualizar regla: ' + (err?.message || err));
        }
    };

    // Parse verdict from output log
    const parseVerdict = (output?: string) => {
        if (!output) return null;
        if (output.includes('Veredicto: APROBAR')) return 'APROBAR';
        if (output.includes('Veredicto: RECHAZAR')) return 'RECHAZAR';
        if (output.includes('Veredicto: REVISAR')) return 'REVISAR';
        if (output.toLowerCase().includes('veredicto: aprobar')) return 'APROBAR';
        if (output.toLowerCase().includes('veredicto: rechazar')) return 'RECHAZAR';
        if (output.toLowerCase().includes('veredicto: revisar')) return 'REVISAR';
        return null;
    };

    // Parse justification from output log
    const parseJustification = (output?: string) => {
        if (!output) return null;
        const match = output.match(/Justificación:\s*([\s\S]*?)(?====+|$)/i);
        if (match && match[1]) {
            return match[1].trim();
        }
        return null;
    };

    return (
        <div className="app-container">
            {/* Topbar */}
            <nav className="topbar">
                <div className="topbar-brand">
                    <span>Auditor Normativo de Pautas</span>
                </div>
                <div className="topbar-menu">
                    <button
                        className={`menu-item ${activeMenu === 'reglas' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('reglas')}
                    >
                        Reglas de Auditoría
                    </button>
                    <button
                        className={`menu-item ${activeMenu === 'agente' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('agente')}
                    >
                        Procesamiento
                    </button>
                    <button
                        className={`menu-item ${activeMenu === 'observabilidad' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('observabilidad')}
                    >
                        Observabilidad
                    </button>
                </div>
            </nav>

            {/* Main Content */}
            <main className="main-content">
                {/* Reglas Section */}
                {activeMenu === 'reglas' && (
                    <section className="section">
                        <h2>Reglas de Control de Lotería de Santa Fe</h2>

                        {/* Form */}
                        <div className="rules-form-container">
                            <div className="form-group" style={{ flex: 1.2 }}>
                                <label className="form-label">Canal / Medio</label>
                                <input
                                    type="text"
                                    placeholder="ej: Publicidad Radial"
                                    className="form-input"
                                    value={newRuleName}
                                    onChange={e => setNewRuleName(e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 2.8 }}>
                                <label className="form-label">Requisitos / Especificaciones de la Resolución</label>
                                <input
                                    type="text"
                                    placeholder="ej: Zócalo con advertencia y altura de al menos 10%"
                                    className="form-input"
                                    value={newPayload}
                                    onChange={e => setNewPayload(e.target.value)}
                                />
                            </div>
                            <button className="btn-add" onClick={handleAddRule}>Agregar Regla</button>
                        </div>

                        {/* Status messages */}
                        {rulesError && (
                            <div style={{ color: 'var(--red-700)', fontSize: '0.82rem', marginBottom: '1rem', padding: '0.75rem', background: 'var(--red-100)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--red-200)' }}>
                                {rulesError}
                            </div>
                        )}

                        {/* Table */}
                        <div className="rules-table-container">
                            <table className="rules-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: '8%' }}>ID</th>
                                        <th style={{ width: '32%' }}>Canal / Medio</th>
                                        <th style={{ width: '45%' }}>Requisitos y Parámetros de Control</th>
                                        <th style={{ width: '15%', textAlign: 'center' }}>Estado / Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rulesLoading && (
                                        <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--gray-400)', padding: '2rem' }}>Cargando reglas...</td></tr>
                                    )}
                                    {!rulesLoading && rules.map(rule => (
                                        <tr key={rule.id}>
                                            <td style={{ color: 'var(--gray-400)', fontSize: '0.78rem' }}>#{rule.id}</td>
                                            <td style={{ fontWeight: 600 }}>{rule.rule_name}</td>
                                            <td style={{ color: 'var(--gray-600)', fontSize: '0.82rem' }}>{rule.payload || <span className="placeholder">—</span>}</td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button
                                                    className="btn-small"
                                                    style={{ marginRight: '0.3rem', background: rule.is_active ? 'var(--green-100)' : 'var(--gray-100)', color: rule.is_active ? 'var(--green-700)' : 'var(--gray-500)' }}
                                                    onClick={() => handleToggleRule(rule.id, rule.is_active)}
                                                    title={rule.is_active ? 'Desactivar' : 'Activar'}
                                                >
                                                    {rule.is_active ? 'Activa' : 'Inactiva'}
                                                </button>
                                                <button
                                                    className="btn-small btn-danger"
                                                    onClick={() => handleDeleteRule(rule.id)}
                                                >
                                                    Eliminar
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {!rulesLoading && rules.length === 0 && (
                                        <tr>
                                            <td colSpan={4} style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--gray-400)', fontSize: '0.9rem' }}>
                                                No hay reglas de auditoría cargadas en la sesión. Use el formulario superior para agregar una regla.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {/* Agente Section */}
                {activeMenu === 'agente' && (
                    <section className="section">
                        <h2>Procesamiento Inteligente Multi-Agente</h2>

                        {/* Status Labels */}
                        <div className="status-container">
                            <div className="status-item">
                                <label className="status-label">Estado del Servicio:</label>
                                <div className="status-value" style={{ color: statusColor, fontWeight: 'bold' }}>{serviceStatus}</div>
                            </div>
                            <div className="status-item">
                                <label className="status-label">Archivos Pendientes:</label>
                                <div className="status-value">{uploadedFiles.filter(f => f.status === 'pendiente').length}</div>
                            </div>
                        </div>

                        {/* Drag and Drop Area */}
                        <div
                            className={`drag-drop-area ${dragActive ? 'active' : ''}`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <div className="drag-drop-content">
                                <div className="drag-drop-icon">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                        <line x1="12" y1="18" x2="12" y2="12"/>
                                        <line x1="9" y1="15" x2="15" y2="15"/>
                                    </svg>
                                </div>
                                <p>Arrastre el documento PDF aquí para iniciar el análisis</p>
                                <p className="drag-drop-hint">Compatible con documentos PDF de material publicitario</p>
                            </div>
                        </div>

                        {/* File Selection Button */}
                        <button className="btn-file-select" onClick={handleFileSelect} style={{ marginBottom: '2rem' }}>
                            Seleccionar archivo PDF
                        </button>

                        {/* Files Table */}
                        {uploadedFiles.length > 0 && (
                            <div className="files-table-container">
                                <h3>Cola de Procesamiento de Auditoría</h3>
                                <table className="files-table">
                                    <thead>
                                        <tr>
                                            <th>Nombre del Archivo</th>
                                            <th style={{ width: '150px' }}>Estado</th>
                                            <th style={{ width: '250px', textAlign: 'right' }}>Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {uploadedFiles.map(file => {
                                            const isExpanded = expandedFileId === file.id;
                                            const verdict = parseVerdict(file.output);
                                            const justification = parseJustification(file.output);
                                            
                                            return (
                                                <>
                                                    <tr key={file.id} className="row-hover">
                                                        <td style={{ fontWeight: 500 }}>{file.fileName}</td>
                                                        <td>
                                                            <span className={`status-badge ${file.status.replace(' ', '')}`}>
                                                                {file.status}
                                                            </span>
                                                        </td>
                                                        <td style={{ textAlign: 'right' }}>
                                                            {file.status === 'pendiente' && (
                                                                <button
                                                                    className="btn-small"
                                                                    onClick={() => executeAgent(file.id)}
                                                                    disabled={isProcessing !== null}
                                                                >
                                                                    {isProcessing === file.id ? 'Analizando...' : 'Auditar con IA'}
                                                                </button>
                                                            )}
                                                            {file.status === 'procesado' && (
                                                                <button
                                                                    className="btn-small"
                                                                    style={{ backgroundColor: isExpanded ? '#f1f3f5' : '#e7f5ff', color: '#004b87' }}
                                                                    onClick={() => setExpandedFileId(isExpanded ? null : file.id)}
                                                                >
                                                                    {isExpanded ? 'Ocultar Resumen' : 'Ver Resultados'}
                                                                </button>
                                                            )}
                                                            <button
                                                                className="btn-small btn-danger"
                                                                onClick={() => deleteFile(file.id)}
                                                                disabled={isProcessing === file.id}
                                                            >
                                                                Eliminar
                                                            </button>
                                                            {file.error && (
                                                                <div className="error-message">{file.error}</div>
                                                            )}
                                                        </td>
                                                    </tr>
                                                    
                                                    {/* Expanded details row */}
                                                    {file.status === 'procesado' && isExpanded && (
                                                        <tr key={`${file.id}-expanded`}>
                                                            <td colSpan={3} className="output-row-td">
                                                                <div className="output-expand-container">
                                                                    <div className="output-header">
                                                                        <span className="output-title">Dictamen del Agente Multi-Agente RAG</span>
                                                                    </div>
                                                                    
                                                                    {/* Summary Cards */}
                                                                    <div className="output-results-summary">
                                                                        <div className="summary-card" style={{ borderLeft: '4px solid ' + (verdict === 'APROBAR' ? '#2f9e44' : verdict === 'RECHAZAR' ? '#e03131' : '#f59f00') }}>
                                                                            <div className="summary-card-title">Veredicto Legal</div>
                                                                            <div className="summary-card-value">
                                                                                <span className={`verdict-badge ${verdict?.toLowerCase() || 'revisar'}`}>
                                                                                    {verdict || 'REVISAR'}
                                                                                </span>
                                                                            </div>
                                                                        </div>
                                                                        
                                                                        <div className="summary-card" style={{ flex: 3 }}>
                                                                            <div className="summary-card-title">Justificación de la Resolución</div>
                                                                            <div className="summary-card-value" style={{ fontSize: '0.95rem', fontWeight: 500, color: '#343a40' }}>
                                                                                {justification || 'Ver detalles en la traza completa de ejecución abajo.'}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                    
                                                                    <div className="output-header" style={{ marginTop: '1.25rem' }}>
                                                                        <span className="output-title" style={{ fontSize: '0.85rem', color: '#6c757d' }}>Log Técnico de Auditoría (Traza del Grafo)</span>
                                                                    </div>
                                                                    <pre className="output-pre">
                                                                        {file.output}
                                                                    </pre>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )}
                                                </>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                )}

                {/* Observabilidad Section */}
                {activeMenu === 'observabilidad' && (
                    <section className="section">
                        <h2>Observabilidad y Trazabilidad del Sistema</h2>
                        <div className="observability-container">
                            <div className="pipeline-visual">
                                <div className="pipeline-node active">
                                    <div className="node-icon node-icon--pdf">PDF</div>
                                    <div className="node-title">Entrada</div>
                                    <div className="node-desc">Carga del documento de campaña</div>
                                </div>
                                <div className="pipeline-arrow">›</div>
                                <div className="pipeline-node active">
                                    <div className="node-icon node-icon--rag">RAG</div>
                                    <div className="node-title">Orquestador RAG</div>
                                    <div className="node-desc">Extracción semántica y contexto vectorial</div>
                                </div>
                                <div className="pipeline-arrow">›</div>
                                <div className="pipeline-node active">
                                    <div className="node-icon node-icon--legal">JUR</div>
                                    <div className="node-title">Especialista Legal</div>
                                    <div className="node-desc">Validación normativa Lotería SF</div>
                                </div>
                                <div className="pipeline-arrow">›</div>
                                <div className="pipeline-node active">
                                    <div className="node-icon node-icon--verdict">VRD</div>
                                    <div className="node-title">Emisor de Veredicto</div>
                                    <div className="node-desc">Dictamen final consolidado</div>
                                </div>
                            </div>
                            
                            <div className="logs-summary-card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <h3 style={{ marginBottom: 0 }}>Registros del Motor de Inferencia (LangGraph)</h3>
                                    <button className="btn-small" onClick={refreshLogs} style={{ background: 'var(--blue-100)', color: 'var(--blue-700)' }}>
                                        Actualizar Logs
                                    </button>
                                </div>
                                <div className="log-console" ref={logConsoleRef} style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', padding: '1rem', background: '#1e1e1e', color: '#d4d4d4', borderRadius: '4px', height: '400px', overflowY: 'auto' }}>
                                    {agentLogs}
                                </div>
                            </div>
                        </div>
                    </section>
                )}
            </main>

            {/* Institutional Footer */}
            <footer className="app-footer">
                <img src={loteriaLogo} alt="Lotería de Santa Fe" className="footer-logo" />
                <img src={utnLogo} alt="UTN Facultad Regional Santa Fe" className="footer-logo" />
            </footer>
        </div>
    );
}

export default App;
