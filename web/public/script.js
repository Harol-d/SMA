// Variables globales
let currentView = 'chat';
let currentExcelFile = null;
let loadingOverlay = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeChatInput();
    initializeExcelUpload();
    initializeEventListeners();
});

// Navegación entre vistas
function initializeNavigation() {
    const navButtons = document.querySelectorAll('.sidebar-btn');
    
    navButtons.forEach((button) => {
        // Remover listeners previos si existen
        button.replaceWith(button.cloneNode(true));
    });
    
    // Volver a obtener los botones después de clonarlos
    const freshButtons = document.querySelectorAll('.sidebar-btn');
    
    freshButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewName = this.getAttribute('data-view');
            switchView(viewName);
            
            // Actualizar botón activo
            freshButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function switchView(viewName) {
    // Ocultar todas las vistas
    const views = document.querySelectorAll('.view');
    views.forEach(view => view.classList.remove('active'));
    
    // Mostrar vista seleccionada
    const targetView = document.getElementById(viewName + '-view');
    
    if (targetView) {
        targetView.classList.add('active');
        currentView = viewName;
        
        // Acciones especiales según la vista
        if (viewName === 'dashboard' && hasExcelFile()) {
            setTimeout(() => loadDashboard(), 500);
        } else if (viewName === 'analysis' && !hasExcelFile()) {
            displayAnalysisResults('Información', 'Carga un archivo Excel en el Dashboard para comenzar con los análisis.');
        }
    }
}

// Chat functionality
function initializeChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', handleChatKeyPress);
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Limpiar input
    input.value = '';
    
    // Agregar mensaje del usuario
    addMessage(message, 'user');
    
    // Deshabilitar botón de envío
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<div class="loading-spinner"></div>';
    }
    
    try {
        // Enviar mensaje a la API
        const response = await fetch('/api/ask/SMA-Agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: message,
                conversationId: 'conv_' + Date.now(),
                parentMessageId: null
            })
        });
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const data = await response.json();
        
        // Agregar respuesta del asistente
        addMessage(data.content || 'Error al procesar la respuesta', 'assistant');
        
    } catch (error) {
        console.error('Error enviando mensaje:', error);
        const errorMessage = error.message || 'Error al conectar con el servidor. Verifica que el backend esté ejecutándose.';
        addMessage(errorMessage, 'assistant');
    } finally {
        // Rehabilitar botón de envío
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }
}

function addMessage(content, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Formatear contenido
    if (typeof content === 'string') {
        contentDiv.innerHTML = content.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
    } else {
        contentDiv.textContent = String(content);
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    
    // Mejorar el scroll al final con un pequeño delay para asegurar que el DOM se actualice
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 50);
    
    // También forzar el scroll inmediatamente
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Funciones de análisis mejoradas
async function analyzeDelays() {
    if (!hasExcelFile()) {
        displayAnalysisResults('Advertencia', 'Primero debes cargar un archivo Excel en el Dashboard para realizar análisis.');
        showErrorMessage('Carga un archivo Excel primero');
        return;
    }
    
    showLoading('Analizando atrasos...');
    try {
        const response = await fetch('/api/analyze_delays', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Análisis de atrasos:', data);
        displayAnalysisResults('Análisis de Atrasos', data);
    } catch (error) {
        console.error('Error:', error);
        displayAnalysisResults('Error', `Error al analizar atrasos: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function analyzePendingTasks() {
    if (!hasExcelFile()) {
        displayAnalysisResults('Advertencia', 'Primero debes cargar un archivo Excel en el Dashboard para realizar análisis.');
        showErrorMessage('Carga un archivo Excel primero');
        return;
    }
    
    const assigneeFilter = document.getElementById('assigneeFilter')?.value?.trim();
    
    showLoading('Analizando tareas pendientes...');
    try {
        const requestBody = assigneeFilter ? { assignee: assigneeFilter } : {};
        
        const response = await fetch('/api/pending_tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Tareas pendientes:', data);
        
        const title = assigneeFilter ? `Tareas Pendientes - ${assigneeFilter}` : 'Tareas Pendientes';
        displayAnalysisResults(title, data);
    } catch (error) {
        console.error('Error:', error);
        displayAnalysisResults('Error', `Error al analizar tareas pendientes: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function getProjectSummary() {
    if (!hasExcelFile()) {
        displayAnalysisResults('Advertencia', 'Primero debes cargar un archivo Excel en el Dashboard para realizar análisis.');
        showErrorMessage('Carga un archivo Excel primero');
        return;
    }
    
    const projectName = document.getElementById('projectFilter')?.value?.trim();
    if (!projectName) {
        displayAnalysisResults('Error', 'Por favor ingresa el nombre del proyecto');
        showErrorMessage('Ingresa el nombre del proyecto');
        return;
    }
    
    showLoading(`Generando resumen de ${projectName}...`);
    try {
        const response = await fetch('/api/project_summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: projectName })
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Resumen del proyecto:', data);
        displayAnalysisResults(`Resumen del Proyecto: ${projectName}`, data);
        showSuccessMessage('Resumen generado exitosamente');
    } catch (error) {
        console.error('Error:', error);
        displayAnalysisResults('Error', `Error al obtener resumen del proyecto: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Utilidades mejoradas
function showLoading(message = 'Cargando...') {
    hideLoading(); // Asegurar que no haya overlays duplicados
    
    loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    if (loadingOverlay) {
        document.body.removeChild(loadingOverlay);
        loadingOverlay = null;
    }
}


// Función para cargar el dashboard
async function loadDashboard() {
    if (!hasExcelFile()) {
        showErrorMessage('Primero carga un archivo Excel para ver las métricas');
        return;
    }
    
    showLoading('Actualizando métricas...');
    try {
        const response = await fetch('/api/dashboard', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error('Error al cargar el dashboard');
        }
        
        const data = await response.json();
        console.log('Dashboard data:', data);
        
        // Actualizar métricas en la UI
        updateDashboardMetrics(data);
        
        showSuccessMessage('Métricas actualizadas correctamente');
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage(`Error al cargar el dashboard: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function updateDashboardMetrics(data) {
    // Actualizar elementos del dashboard si existen
    const totalProjects = document.getElementById('total-projects');
    const onTrackProjects = document.getElementById('on-track-projects');
    const atRiskProjects = document.getElementById('at-risk-projects');
    const delayedProjects = document.getElementById('delayed-projects');
    
    if (data && data.metrics) {
        if (totalProjects) {
            totalProjects.textContent = data.metrics.total_projects || 0;
            totalProjects.parentElement.classList.remove('success', 'warning', 'danger');
        }
        if (onTrackProjects) {
            onTrackProjects.textContent = data.metrics.on_track || 0;
            onTrackProjects.parentElement.classList.add('success');
        }
        if (atRiskProjects) {
            atRiskProjects.textContent = data.metrics.at_risk || 0;
            atRiskProjects.parentElement.classList.add('warning');
        }
        if (delayedProjects) {
            delayedProjects.textContent = data.metrics.delayed || 0;
            delayedProjects.parentElement.classList.add('danger');
        }
    } else {
        // Si no hay datos, mostrar ceros
        if (totalProjects) totalProjects.textContent = '0';
        if (onTrackProjects) onTrackProjects.textContent = '0';
        if (atRiskProjects) atRiskProjects.textContent = '0';
        if (delayedProjects) delayedProjects.textContent = '0';
    }
}

// Función para mostrar resultados de análisis en la UI
function displayAnalysisResults(title, data) {
    const resultsContainer = document.getElementById('analysisResults');
    if (!resultsContainer) return;
    
    let content = '';
    if (typeof data === 'string') {
        content = `<h3>${title}</h3><p>${data}</p>`;
    } else if (typeof data === 'object' && data !== null) {
        content = `<h3>${title}</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
    } else {
        content = `<h3>${title}</h3><p>No hay datos disponibles</p>`;
    }
    
    resultsContainer.innerHTML = content;
}

// Sistema de notificaciones Toast mejorado
function showToast(message, type = 'success') {
    // Remover toasts existentes
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="${icon}"></i>
        <span class="toast-message">${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Mostrar toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Ocultar toast después de 4 segundos
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

const showSuccessMessage = (message) => showToast(message, 'success');
const showErrorMessage = (message) => showToast(message, 'error');

// ========== FUNCIONALIDAD DE EXCEL ==========

// Variables para historial de archivos
let fileHistory = JSON.parse(localStorage.getItem('sma_file_history') || '[]');

// Inicializar funcionalidad de Excel
function initializeExcelUpload() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }
    
    // Drag & Drop functionality
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleFileDrop);
    }
    
    // Cargar historial al inicializar
    loadFileHistory();
    
    // Verificar si hay archivo actual
    updateFileStatus();
}

// Manejar selección de archivo
function handleFileSelection(event) {
    const file = event.target.files[0];
    if (file) {
        processExcelFile(file);
    }
}

// Manejar drag & drop
function handleDragOver(event) {
    event.preventDefault();
    const uploadArea = event.currentTarget;
    uploadArea.style.borderColor = '#10a37f';
    uploadArea.style.backgroundColor = '#f0fdf4';
    uploadArea.style.transform = 'scale(1.02)';
}

function handleDragLeave(event) {
    event.preventDefault();
    const uploadArea = event.currentTarget;
    uploadArea.style.borderColor = '';
    uploadArea.style.backgroundColor = '';
    uploadArea.style.transform = '';
}

function handleFileDrop(event) {
    event.preventDefault();
    const uploadArea = event.currentTarget;
    uploadArea.style.borderColor = '';
    uploadArea.style.backgroundColor = '';
    uploadArea.style.transform = '';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type.includes('sheet') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            processExcelFile(file);
        } else {
            showErrorMessage('Por favor selecciona un archivo Excel válido (.xlsx o .xls)');
        }
    }
}

// Procesar archivo Excel
async function processExcelFile(file) {
    // Validar archivo
    if (!file) {
        showErrorMessage('No se seleccionó ningún archivo');
        return;
    }
    
    // Validar tamaño (máximo 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showErrorMessage('El archivo es demasiado grande. Máximo 10MB permitido.');
        return;
    }
    
    // Mostrar progreso
    showUploadProgress();
    
    try {
        // Simular progreso de carga
        for (let i = 0; i <= 90; i += 10) {
            updateUploadProgress(i);
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        // Preparar datos para enviar
        const formData = new FormData();
        formData.append('file', file);
        
        // Enviar archivo al backend
        const response = await fetch('/api/upload_excel', {
            method: 'POST',
            body: formData
        });
        
        updateUploadProgress(100);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: response.statusText }));
            throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Éxito - Guardar archivo actual
        currentExcelFile = {
            name: file.name,
            size: file.size,
            uploadDate: new Date(),
            data: result,
            originalBlob: file  // Guardar referencia al archivo original para descarga
        };
        
        // Agregar al historial
        addToFileHistory(currentExcelFile);
        
        // Actualizar UI
        hideUploadProgress();
        updateFileStatus();
        showSuccessMessage('Archivo Excel cargado exitosamente');
        
        // Limpiar input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
        
    } catch (error) {
        console.error('Error al procesar archivo:', error);
        hideUploadProgress();
        showErrorMessage(`Error al procesar el archivo: ${error.message}`);
        currentExcelFile = null;
        updateFileStatus();
    }
}

// Actualizar estado de carga
function updateUploadStatus(text, status = 'default') {
    const statusElement = document.getElementById('uploadStatus');
    const textElement = document.getElementById('uploadText');
    const iconElement = document.getElementById('uploadIcon');
    const clearBtn = document.getElementById('clearBtn');
    
    if (textElement) textElement.textContent = text;
    
    if (statusElement) {
        statusElement.className = 'upload-status';
        if (status === 'success') {
            statusElement.classList.add('has-file');
            if (clearBtn) clearBtn.style.display = 'inline-flex';
        } else if (status === 'error') {
            statusElement.classList.add('error');
            if (clearBtn) clearBtn.style.display = 'none';
        } else {
            if (clearBtn) clearBtn.style.display = 'none';
        }
    }
    
    if (iconElement) {
        iconElement.className = status === 'success' ? 'fas fa-check-circle' : 
                               status === 'error' ? 'fas fa-exclamation-circle' :
                               status === 'loading' ? 'fas fa-spinner fa-spin' : 'fas fa-upload';
    }
}

// Mostrar progreso de carga
function showUploadProgress() {
    const progressContainer = document.getElementById('uploadProgress');
    const uploadArea = document.getElementById('uploadArea');
    
    if (progressContainer) {
        progressContainer.style.display = 'block';
        updateUploadProgress(0);
    }
    
    if (uploadArea) {
        uploadArea.style.opacity = '0.5';
        uploadArea.style.pointerEvents = 'none';
    }
}

// Actualizar progreso
function updateUploadProgress(progress) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill) progressFill.style.width = `${progress}%`;
    if (progressText) progressText.textContent = `${progress}%`;
}

// Ocultar progreso
function hideUploadProgress() {
    const progressContainer = document.getElementById('uploadProgress');
    const uploadArea = document.getElementById('uploadArea');
    
    if (progressContainer) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            updateUploadProgress(0);
        }, 1000);
    }
    
    if (uploadArea) {
        uploadArea.style.opacity = '';
        uploadArea.style.pointerEvents = '';
    }
}

// ========== FUNCIONES DE GESTIÓN DE ARCHIVOS ==========

// Actualizar estado del archivo
function updateFileStatus() {
    const fileInfo = document.getElementById('fileInfo');
    const uploadArea = document.getElementById('uploadArea');
    
    if (currentExcelFile) {
        // Mostrar información del archivo
        const fileName = document.getElementById('fileName');
        const fileDetails = document.getElementById('fileDetails');
        
        if (fileName) fileName.textContent = currentExcelFile.name;
        if (fileDetails) {
            const sizeInMB = (currentExcelFile.size / (1024 * 1024)).toFixed(2);
            const uploadTime = formatTimeAgo(currentExcelFile.uploadDate);
            fileDetails.textContent = `Tamaño: ${sizeInMB} MB | Cargado: ${uploadTime}`;
        }
        
        if (fileInfo) fileInfo.style.display = 'block';
        if (uploadArea) uploadArea.style.display = 'none';
    } else {
        // Mostrar área de carga
        if (fileInfo) fileInfo.style.display = 'none';
        if (uploadArea) uploadArea.style.display = 'block';
    }
}

// Eliminar archivo Excel
function deleteExcelFile() {
    if (!currentExcelFile) return;
    
    const confirmDelete = confirm(`¿Estás seguro de que quieres eliminar "${currentExcelFile.name}"?`);
    
    if (confirmDelete) {
        currentExcelFile = null;
        updateFileStatus();
        showSuccessMessage('Archivo eliminado correctamente');
        
        // Limpiar métricas del dashboard
        updateDashboardMetrics({ metrics: { total_projects: 0, on_track: 0, at_risk: 0, delayed: 0 } });
    }
}

// Descargar archivo Excel (placeholder)
function downloadExcelFile() {
    if (!currentExcelFile) {
        showErrorMessage('No hay archivo Excel para descargar');
        return;
    }
    
    try {
        // Crear un blob con los datos del archivo original si están disponibles
        if (currentExcelFile.originalBlob) {
            // Si tenemos el blob original, usarlo directamente
            const url = URL.createObjectURL(currentExcelFile.originalBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = currentExcelFile.name;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            showSuccessMessage(`Archivo "${currentExcelFile.name}" descargado exitosamente`);
        } else {
            // Si no tenemos el blob original, mostrar información y sugerir alternativas
            showToast(`Archivo "${currentExcelFile.name}" procesado - descarga no disponible`, 'error');
            console.warn('Archivo Excel no disponible para descarga - solo metadata almacenado');
        }
    } catch (error) {
        console.error('Error al descargar archivo:', error);
        showErrorMessage('Error al descargar el archivo Excel');
    }
}

// Agregar al historial
function addToFileHistory(fileInfo) {
    const historyItem = {
        id: Date.now(),
        name: fileInfo.name,
        size: fileInfo.size,
        uploadDate: fileInfo.uploadDate,
        status: 'completed'
    };
    
    // Agregar al inicio del array
    fileHistory.unshift(historyItem);
    
    // Mantener solo los últimos 10
    fileHistory = fileHistory.slice(0, 10);
    
    // Guardar en localStorage
    localStorage.setItem('sma_file_history', JSON.stringify(fileHistory));
    
    // Actualizar UI
    loadFileHistory();
}

// Cargar historial de archivos
function loadFileHistory() {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    if (fileHistory.length === 0) {
        historyList.innerHTML = '<p class="no-history">No hay archivos cargados previamente</p>';
        return;
    }
    
    const historyHTML = fileHistory.map(item => `
        <div class="history-item">
            <div class="history-details">
                <i class="fas fa-file-excel"></i>
                <div>
                    <div class="history-text">${item.name}</div>
                    <div class="history-date">${formatTimeAgo(new Date(item.uploadDate))}</div>
                </div>
            </div>
            <div class="history-actions">
                <button class="btn btn-sm btn-secondary" onclick="reloadFromHistory('${item.id}')">
                    <i class="fas fa-redo"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    historyList.innerHTML = historyHTML;
}

// Recargar desde historial
function reloadFromHistory(itemId) {
    try {
        const historyItem = fileHistory.find(item => item.id.toString() === itemId.toString());
        
        if (!historyItem) {
            showErrorMessage('Archivo no encontrado en el historial');
            return;
        }
        
        // Verificar si el archivo original aún existe
        const originalPath = historyItem.originalPath;
        if (!originalPath) {
            showErrorMessage('Ruta del archivo original no disponible');
            return;
        }
        
        // Mostrar confirmación al usuario
        const confirmReload = confirm(`¿Deseas recargar "${historyItem.name}"?\n\nEsto reemplazará el archivo actual y procesará nuevamente los datos.`);
        
        if (!confirmReload) {
            return;
        }
        
        showLoading('Recargando archivo desde historial...');
        
        // Simular recarga del archivo (en un caso real, necesitarías acceso al archivo original)
        setTimeout(() => {
            try {
                // Actualizar archivo actual con datos del historial
                currentExcelFile = {
                    name: historyItem.name,
                    size: historyItem.size,
                    uploadDate: new Date(), // Nueva fecha de carga
                    data: historyItem.data || null,
                    reloadedFrom: itemId
                };
                
                // Actualizar UI
                updateFileStatus();
                hideLoading();
                showSuccessMessage(`Archivo "${historyItem.name}" recargado desde historial`);
                
                // Cambiar a vista de upload para mostrar el archivo cargado
                switchView('upload');
                
            } catch (error) {
                console.error('Error al recargar desde historial:', error);
                hideLoading();
                showErrorMessage('Error al recargar el archivo desde historial');
            }
        }, 1500);
        
    } catch (error) {
        console.error('Error en reloadFromHistory:', error);
        showErrorMessage('Error al acceder al historial de archivos');
    }
}

// Formatear tiempo transcurrido
function formatTimeAgo(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `hace ${days} día${days > 1 ? 's' : ''}`;
    if (hours > 0) return `hace ${hours} hora${hours > 1 ? 's' : ''}`;
    if (minutes > 0) return `hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
    return 'hace un momento';
}

// Utilidades de archivo
const hasExcelFile = () => currentExcelFile !== null;
const getExcelFileInfo = () => currentExcelFile;


// ========== FUNCIONES ESPECIALES DASHBOARD Y ANÁLISIS ==========


// Exportar funciones para uso global
window.sendMessage = sendMessage;
window.handleChatKeyPress = handleChatKeyPress;
window.analyzeDelays = analyzeDelays;
window.analyzePendingTasks = analyzePendingTasks;
window.getProjectSummary = getProjectSummary;
window.loadDashboard = loadDashboard;
window.displayAnalysisResults = displayAnalysisResults;
window.deleteExcelFile = deleteExcelFile;
window.downloadExcelFile = downloadExcelFile;
window.hasExcelFile = hasExcelFile;
window.getExcelFileInfo = getExcelFileInfo;
window.switchView = switchView;

