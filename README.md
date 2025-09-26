# Guía de Análisis de Proyectos - SMA

## Descripción General

El Sistema de Monitoreo de Avances (SMA) incluye funcionalidades avanzadas para analizar proyectos utilizando archivos Excel como base de datos de proyectos y actividades.

## Características Principales

### 🎯 **Análisis Inteligente de Proyectos**
- Extracción automática de información de proyectos desde Excel
- Identificación de personas asignadas, proyectos, actividades y timeline
- Análisis de porcentajes de avance y estados de tareas
- Procesamiento inteligente de notas para encontrar razones de atrasos

### 📊 **Métricas Avanzadas**
- Clasificación automática de proyectos: en curso, atrasados, en riesgo
- Análisis de carga de trabajo por persona
- Identificación de patrones de atrasos recurrentes
- Cálculo de eficiencia y productividad del equipo

### 🤖 **IA Especializada**
- LLM configurado como Project Manager Senior
- Análisis de causas raíz basado en notas de reuniones
- Recomendaciones accionables para mejorar rendimiento
- Identificación de dependencias y cuellos de botella

## Estructura del Excel

El sistema reconoce automáticamente las siguientes columnas:

### Campos Principales:
- **Asignado/Responsable**: `asignado`, `assignee`, `responsable`, `encargado`
- **Proyecto**: `proyecto`, `project`, `nombre_proyecto`
- **Actividad**: `actividad`, `activity`, `tarea`, `task`
- **Progreso**: `progreso`, `progress`, `avance`, `porcentaje`
- **Notas**: `notas`, `notes`, `comentarios`, `observaciones`
- **Fechas**: `fecha_inicio`, `fecha_fin`, `start_date`, `end_date`

### Ejemplo de Estructura:
```
| Proyecto | Asignado | Actividad | Progreso | Notas | Fecha Inicio |
|----------|----------|-----------|----------|-------|--------------|
| Web CCB  | Juan     | Frontend  | 75%      | Reunión completada, falta revisar diseño | 01/09/2024 |
```

## Endpoints Disponibles

### 1. `/upload_excel`
**Método**: POST  
**Descripción**: Sube y procesa archivos Excel

```json
{
  "success": true,
  "message": "Archivo Excel procesado exitosamente",
  "data": {
    "filename": "SMA_Lector.xlsx",
    "rows_processed": 50,
    "vectors_created": 50
  }
}
```

### 2. `/analyze_delays`
**Método**: POST  
**Descripción**: Analiza proyectos con atrasos

```json
// Request
{
  "project_name": "Web CCB",  // opcional
  "assignee": "Juan",         // opcional
  "top_k": 20                 // opcional
}

// Response
{
  "success": true,
  "delayed_projects_found": 5,
  "delayed_projects": [...],
  "llm_analysis": "Análisis detallado de atrasos..."
}
```

### 3. `/pending_tasks`
**Método**: POST  
**Descripción**: Identifica tareas pendientes

```json
// Request
{
  "project_name": "Web CCB",  // opcional
  "assignee": "Juan"          // opcional
}

// Response
{
  "success": true,
  "projects_with_pending_tasks": 3,
  "projects": [...],
  "llm_analysis": "Análisis de tareas pendientes..."
}
```

### 4. `/project_summary`
**Método**: POST  
**Descripción**: Resumen completo de un proyecto

```json
// Request
{
  "project_name": "Web CCB"  // requerido
}

// Response
{
  "success": true,
  "project_name": "Web CCB",
  "metrics": {
    "total_activities": 15,
    "completed_activities": 8,
    "delayed_activities": 3,
    "average_progress": 67.5,
    "assignees": ["Juan", "María", "Carlos"]
  },
  "llm_analysis": "Análisis ejecutivo completo..."
}
```

### 5. `/search`
**Método**: POST  
**Descripción**: Búsqueda semántica

```json
// Request
{
  "query": "¿Por qué se atrasó el proyecto?",
  "top_k": 10  // opcional
}

// Response
{
  "success": true,
  "query": "¿Por qué se atrasó el proyecto?",
  "total_found": 5,
  "results": [...]
}
```

### 6. `/dashboard`
**Método**: GET  
**Descripción**: Métricas generales del sistema

## Análisis Automático de Notas

El sistema analiza automáticamente las notas para identificar:

### Indicadores de Atrasos:
- `atraso`, `retraso`, `problema`, `bloqueado`
- `esperando`, `falta`, `cancelado`, `pospuesto`

### Tareas Pendientes:
- `pendiente`, `por hacer`, `revisar`
- `completar`, `terminar`, `finish`

### Ejemplo:
```
Nota: "Reunión completada. Falta revisar diseño. Proyecto esperando aprobación."

Análisis Automático:
- Razón de atraso: "Proyecto esperando aprobación"
- Tarea pendiente: "Falta revisar diseño"
- Estado: "at_risk"
```

## Clasificación de Estados

### Estados de Proyecto:
- **En Curso** (`on_track`): Progreso ≥ 80%
- **En Riesgo** (`at_risk`): Progreso 50-79%
- **Atrasado** (`delayed`): Progreso < 50%

## Casos de Uso

### 1. **Análisis de Atrasos**
```bash
# Todos los proyectos atrasados
POST /analyze_delays
{}

# Atrasos de un proyecto específico
POST /analyze_delays
{"project_name": "Sistema CRM"}
```

### 2. **Gestión de Tareas Pendientes**
```bash
# Tareas pendientes de Juan
POST /pending_tasks
{"assignee": "Juan"}

# Tareas del proyecto Web
POST /pending_tasks
{"project_name": "Web CCB"}
```

### 3. **Resumen Ejecutivo**
```bash
POST /project_summary
{"project_name": "Sistema CRM"}
```

### 4. **Búsqueda Específica**
```bash
POST /search
{"query": "¿Qué tareas están pendientes en el proyecto de facturación?"}
```

## Beneficios

### Para Project Managers:
- **Visibilidad completa** del estado de proyectos
- **Identificación automática** de atrasos y causas
- **Recomendaciones accionables** basadas en IA
- **Análisis de patrones** para mejorar procesos

### Para Equipos:
- **Distribución equilibrada** de trabajo
- **Identificación temprana** de bloqueos
- **Seguimiento detallado** de tareas
- **Comunicación mejorada** sobre estados

### Para Gerencia:
- **Reportes automáticos**
- **Métricas de rendimiento**
- **Evaluación de riesgos**
- **Optimización de recursos**

## Flujo de Trabajo

1. **Subir Excel** → `/upload_excel`
2. **Analizar atrasos** → `/analyze_delays`
3. **Revisar pendientes** → `/pending_tasks`
4. **Generar resúmenes** → `/project_summary`
5. **Consultas específicas** → `/search`

El sistema está optimizado para procesar el archivo `SMA_Lector.xlsx` y proporcionar análisis inteligentes sobre el estado de tus proyectos.
