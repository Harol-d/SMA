
require('dotenv').config();
const express = require('express');
const path = require('path');
const cors = require('cors');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const compression = require('compression');
const multer = require('multer');
const axios = require('axios'); // Movido al inicio para evitar imports repetitivos

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware de seguridad
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  crossOriginEmbedderPolicy: false
}));
app.use(compression());

// Rate limiting
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutos
  max: 100, // máximo 100 requests por IP
  message: 'Demasiadas solicitudes desde esta IP, intenta nuevamente más tarde.'
});
app.use('/api/', limiter);

// Middleware básico
app.use(cors({
  origin: [
    process.env.FRONTEND_URL || `http://localhost:${PORT}`,
    'http://localhost:3000',
    'http://127.0.0.1:3000'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Validación de JSON
app.use(bodyParser.json({ 
  limit: '10mb',
  verify: (req, res, buf) => {
    try {
      if (buf.length > 0) {
        JSON.parse(buf);
      }
    } catch(e) {
      // Hay que dejar que Express maneje el error
      const error = new Error('Formato JSON inválido');
      error.status = 400;
      error.type = 'entity.parse.failed';
      throw error;
    }
  }
}));

// Middleware para manejar errores de parsing JSON
app.use((error, req, res, next) => {
  if (error.type === 'entity.parse.failed') {
    return res.status(400).json({ 
      error: 'Formato JSON inválido',
      message: 'El cuerpo de la solicitud contiene JSON malformado'
    });
  }
  next(error);
});
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// Configurar multer para archivos Excel
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB límite
  },
  fileFilter: (req, file, cb) => {
    // Aceptar solo archivos Excel
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel' // .xls
    ];
    
    if (allowedTypes.includes(file.mimetype) || 
        file.originalname.endsWith('.xlsx') || 
        file.originalname.endsWith('.xls')) {
      cb(null, true);
    } else {
      cb(new Error('Solo se permiten archivos Excel (.xlsx, .xls)'));
    }
  }
});

// Servir archivos estáticos
app.use(express.static(path.join(__dirname, 'public')));


// Configuración de endpoints disponibles
const endpoints = {
  'SMA-Agent': {
    name: 'SMA-Agent',
    type: 'custom',
    baseURL: process.env.BACKEND_URL || 'http://localhost:5000',
    iconURL: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCAxMkwxMy4wOSAxNS43NEwxMiAyMkwxMC45MSAxNS43NEw0IDEyTDEwLjkxIDguMjZMMTIgMloiIGZpbGw9IiNEQzI2MjYiLz4KPC9zdmc+'
  }
};


// Usuario por defecto
const defaultUser = {
  id: 'user-sma',
  name: 'Usuario SMA',
  email: 'usuario@sma.com'
};

// Configuración de la app
app.get('/api/config', (req, res) => {
  res.json({
    appTitle: 'Sistema de Monitoreo de Avances (SMA)',
    appVersion: '1.0.0',
    endpoints: endpoints,
    interface: {
      customWelcome: '¡Bienvenido a SMA! Ingresa tu archivo Excel para analizar los avances de los proyectos.',
      endpointsMenu: true,
      modelSelect: true
    },
    user: defaultUser
  });
});

// Función de validación de entrada
function validateInput(input, maxLength = 1000) {
  if (!input || typeof input !== 'string') {
    return { valid: false, error: 'Input debe ser una cadena no vacía' };
  }
  if (input.length > maxLength) {
    return { valid: false, error: `Input excede el límite de ${maxLength} caracteres` };
  }
  // Sanitizar caracteres peligrosos básicos
  const sanitized = input.replace(/[<>]/g, '');
  return { valid: true, sanitized };
}

// Función de validación para parámetros de conversación
function validateConversationParams(conversationId, parentMessageId) {
  const errors = [];
  
  if (conversationId && (typeof conversationId !== 'string' || conversationId.length > 100)) {
    errors.push('conversationId debe ser una cadena válida de máximo 100 caracteres');
  }
  
  if (parentMessageId && (typeof parentMessageId !== 'string' || parentMessageId.length > 100)) {
    errors.push('parentMessageId debe ser una cadena válida de máximo 100 caracteres');
  }
  
  return {
    valid: errors.length === 0,
    errors: errors
  };
}

// Endpoint para enviar mensajes
app.post('/api/ask/:endpoint', async (req, res) => {
  const { endpoint } = req.params;
  const { text, conversationId, parentMessageId } = req.body;
  
  // Validar entrada de texto
  const textValidation = validateInput(text, 2000);
  if (!textValidation.valid) {
    return res.status(400).json({ error: textValidation.error });
  }
  
  // Validar parámetros de conversación
  const paramsValidation = validateConversationParams(conversationId, parentMessageId);
  if (!paramsValidation.valid) {
    return res.status(400).json({ 
      error: 'Parámetros de conversación inválidos',
      details: paramsValidation.errors
    });
  }
  
  console.log(`📤 Enviando mensaje a ${endpoint}:`, textValidation.sanitized);
  
  try {
    const endpointConfig = endpoints[endpoint];
    
    if (!endpointConfig) {
      return res.status(404).json({ error: 'Endpoint no encontrado' });
    }
    
    // Enviar al agente SMA
    const response = await axios.post(`${endpointConfig.baseURL}/api/response`, {
      prompt: textValidation.sanitized
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 40000
    });
    
    const { data } = response;
    
    // Formatear respuesta compatible con LibreChat
    // Extraer el contenido de la respuesta del backend Flask
    let content = '';
    if (typeof data === 'string') {
      content = data;
    } else if (typeof data === 'object' && data !== null) {
      // El backend Flask devuelve {"LLM": "respuesta"} para el endpoint /response
      content = data.LLM || data.response || data.message || data.content || data.text || data.answer || data.result;
      
      // Si no se encuentra contenido en propiedades conocidas, usar el JSON completo
      if (!content) {
        // Verificar si hay algún valor de string en el objeto
        const stringValues = Object.values(data).filter(val => typeof val === 'string' && val.trim());
        if (stringValues.length > 0) {
          content = stringValues[0];
        } else {
          content = JSON.stringify(data, null, 2);
        }
      }
    } else {
      content = 'La respuesta de la API no pudo ser procesada correctamente.';
    }
    
    const chatResponse = {
      id: data.message_id || 'msg_' + Date.now(),
      conversationId: conversationId || 'conv_' + Date.now(),
      parentMessageId: parentMessageId,
      role: 'assistant',
      content: content,
      model: 'sma-assistant-v1',
      finish_reason: 'stop',
      metadata: {
        sql_query: data?.sql_query,
        execution_time: data?.execution_time,
        affected_rows: data?.affected_rows,
        raw_response: data
      }
    };
    
    res.json(chatResponse);
    
  } catch (error) {
    console.error('❌ Error en el chat:', error.message);
    
    res.status(500).json({
      id: 'error_' + Date.now(),
      conversationId: req.body.conversationId,
      parentMessageId: req.body.parentMessageId,
      role: 'assistant',
      content: `❌ Error al procesar la consulta: ${error.message}\n\n🔧 **Posibles soluciones:**\n- Verificar que el servicio backend esté ejecutándose en http://localhost:5000\n- Revisar la conexión de red\n- Comprobar los logs del servidor`,
      error: true
    });
  }
});

// Endpoints específicos del SMA
app.post('/api/upload_excel', upload.single('file'), async (req, res) => {
  try {
    console.log('📤 Solicitud de carga recibida');
    console.log('📤 Headers:', req.headers);
    console.log('📤 Content-Type:', req.get('Content-Type'));
    
    if (!req.file) {
      console.log('❌ No se recibió archivo en el campo "file"');
      console.log('📤 Campos disponibles:', Object.keys(req.body));
      return res.status(400).json({ 
        error: 'No se recibió ningún archivo',
        debug: 'Asegúrate de usar el campo "file" en el FormData'
      });
    }

    console.log('📤 Archivo recibido:', req.file.originalname, 'Tamaño:', req.file.size);
    console.log('📤 MIME Type:', req.file.mimetype);
    
    const backendURL = process.env.BACKEND_URL || 'http://localhost:5000';
    
    // Crear FormData para enviar el archivo al backend Python
    const FormData = require('form-data');
    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype
    });
    
    const response = await axios.post(`${backendURL}/api/upload_excel`, formData, {
      headers: {
        ...formData.getHeaders(),
        'Content-Length': formData.getLengthSync()
      },
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });
    
    console.log('✅ Archivo procesado exitosamente por el backend');
    res.json(response.data);
  } catch (error) {
    console.error('❌ Error en upload_excel:', error.message);
    
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'El archivo es demasiado grande. Máximo 10MB permitido.' });
    }
    
    if (error.message.includes('Solo se permiten archivos Excel')) {
      return res.status(400).json({ error: error.message });
    }
    
    res.status(500).json({ 
      error: 'Error al procesar el archivo Excel',
      details: error.response?.data || error.message
    });
  }
});

app.post('/api/analyze_delays', async (req, res) => {
  try {
    const backendURL = process.env.BACKEND_URL || 'http://localhost:5000';
    
    const response = await axios.post(`${backendURL}/api/analyze_delays`, req.body, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('❌ Error en analyze_delays:', error.message);
    res.status(500).json({ error: 'Error al analizar atrasos' });
  }
});

app.post('/api/pending_tasks', async (req, res) => {
  try {
    const backendURL = process.env.BACKEND_URL || 'http://localhost:5000';
    
    const response = await axios.post(`${backendURL}/api/pending_tasks`, req.body, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('❌ Error en pending_tasks:', error.message);
    res.status(500).json({ error: 'Error al obtener tareas pendientes' });
  }
});

app.post('/api/project_summary', async (req, res) => {
  try {
    const backendURL = process.env.BACKEND_URL || 'http://localhost:5000';
    
    const response = await axios.post(`${backendURL}/api/project_summary`, req.body, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    res.json(response.data);
  } catch (error) {
    console.error('❌ Error en project_summary:', error.message);
    res.status(500).json({ error: 'Error al obtener resumen del proyecto' });
  }
});

app.get('/api/dashboard', async (req, res) => {
  try {
    const backendURL = process.env.BACKEND_URL || 'http://localhost:5000';
    
    const response = await axios.get(`${backendURL}/api/dashboard`);
    res.json(response.data);
  } catch (error) {
    console.error('❌ Error en dashboard:', error.message);
    res.status(500).json({ error: 'Error al obtener métricas del dashboard' });
  }
});

// Middleware para manejar errores de multer
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'El archivo es demasiado grande. Máximo 10MB permitido.' });
    }
    if (error.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({ error: 'Campo de archivo inesperado. Usa el campo "file".' });
    }
    return res.status(400).json({ error: `Error de carga: ${error.message}` });
  }
  
  if (error.message && error.message.includes('Solo se permiten archivos Excel')) {
    return res.status(400).json({ error: error.message });
  }
  
  next(error);
});

// Ruta principal
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 SMA Frontend: http://localhost:${PORT}`);
  console.log(`🔗 Backend: ${process.env.BACKEND_URL || 'http://localhost:5000'}`);
});

module.exports = app;
