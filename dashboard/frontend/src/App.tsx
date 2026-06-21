import { useState } from 'react';
import './App.css';
import { SaveTemporaryFile, ExecuteAgent, CleanupTemporaryFiles } from "../wailsjs/go/main/App.js";

interface UploadedFile {
    id: string;
    fileName: string;
    filePath: string;
    status: 'pendiente' | 'en proceso' | 'procesado' | 'error';
    output?: string;
    error?: string;
}

function App() {
    const [activeMenu, setActiveMenu] = useState('reglas');
    const [dragActive, setDragActive] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [isProcessing, setIsProcessing] = useState<string | null>(null);

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
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    // Get status badge color
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'pendiente':
                return '#FFB84D';
            case 'en proceso':
                return '#4CA6C6';
            case 'procesado':
                return '#66BB6A';
            case 'error':
                return '#EF5350';
            default:
                return '#999';
        }
    };

    return (
        <div className="app-container">
            {/* Topbar */}
            <nav className="topbar">
                <div className="topbar-brand">Dashboard TPIA</div>
                <div className="topbar-menu">
                    <button
                        className={`menu-item ${activeMenu === 'reglas' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('reglas')}
                    >
                        Reglas
                    </button>
                    <button
                        className={`menu-item ${activeMenu === 'agente' ? 'active' : ''}`}
                        onClick={() => setActiveMenu('agente')}
                    >
                        Agente
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
                        <h2>Reglas</h2>

                        {/* Form */}
                        <div className="rules-form-container">
                            <div className="form-group">
                                <input
                                    type="text"
                                    placeholder="Campo 1"
                                    className="form-input"
                                />
                            </div>
                            <div className="form-group">
                                <input
                                    type="text"
                                    placeholder="Campo 2"
                                    className="form-input"
                                />
                            </div>
                            <div className="form-group">
                                <input
                                    type="text"
                                    placeholder="Campo 3"
                                    className="form-input"
                                />
                            </div>
                            <button className="btn-add">+</button>
                        </div>

                        {/* Table */}
                        <div className="rules-table-container">
                            <table className="rules-table">
                                <thead>
                                    <tr>
                                        <th>Campo 1</th>
                                        <th>Campo 2</th>
                                        <th>Campo 3</th>
                                        <th>Acciones</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td>
                                            <button className="btn-small">Editar</button>
                                            <button className="btn-small btn-danger">Eliminar</button>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td>
                                            <button className="btn-small">Editar</button>
                                            <button className="btn-small btn-danger">Eliminar</button>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td className="placeholder">Placeholder</td>
                                        <td>
                                            <button className="btn-small">Editar</button>
                                            <button className="btn-small btn-danger">Eliminar</button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {/* Agente Section */}
                {activeMenu === 'agente' && (
                    <section className="section">
                        <h2>Agente</h2>

                        {/* Status Labels */}
                        <div className="status-container">
                            <div className="status-item">
                                <label className="status-label">Estado:</label>
                                <div className="status-value placeholder">Disponible</div>
                            </div>
                            <div className="status-item">
                                <label className="status-label">Trabajos en cola:</label>
                                <div className="status-value placeholder">{uploadedFiles.filter(f => f.status === 'pendiente').length}</div>
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
                                <div className="drag-drop-icon">📁</div>
                                <p>Arrastra archivos aquí</p>
                                <p className="drag-drop-hint">o usa el botón abajo</p>
                            </div>
                        </div>

                        {/* File Selection Button */}
                        <button className="btn-file-select" onClick={handleFileSelect}>
                            Seleccionar archivo
                        </button>

                        {/* Files Table */}
                        {uploadedFiles.length > 0 && (
                            <div className="files-table-container">
                                <h3>Archivos Cargados</h3>
                                <table className="files-table">
                                    <thead>
                                        <tr>
                                            <th>Nombre</th>
                                            <th>Estado</th>
                                            <th>Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {uploadedFiles.map(file => (
                                            <tr key={file.id}>
                                                <td>{file.fileName}</td>
                                                <td>
                                                    <span
                                                        className="status-badge"
                                                        style={{ backgroundColor: getStatusColor(file.status) }}
                                                    >
                                                        {file.status}
                                                    </span>
                                                </td>
                                                <td>
                                                    {file.status === 'pendiente' && (
                                                        <button
                                                            className="btn-small"
                                                            onClick={() => executeAgent(file.id)}
                                                            disabled={isProcessing === file.id}
                                                        >
                                                            {isProcessing === file.id ? 'Procesando...' : 'Iniciar'}
                                                        </button>
                                                    )}
                                                    <button
                                                        className="btn-small btn-danger"
                                                        onClick={() => deleteFile(file.id)}
                                                    >
                                                        Eliminar
                                                    </button>
                                                    {file.error && (
                                                        <div className="error-message">{file.error}</div>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                )}

                {/* Observabilidad Section */}
                {activeMenu === 'observabilidad' && (
                    <section className="section">
                        <h2>Observabilidad</h2>
                        <div className="empty-state">
                            <p>Esta sección está vacía por el momento.</p>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

export default App;
