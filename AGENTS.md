# AGENTS.md — Guía para Agentes de IA

## Descripción del Proyecto

Sistema integral de **evaluaciones psicométricas y de desempeño** para RRHH, construido con **Streamlit + SQLite**. Permite gestionar candidatos y empleados, asignar evaluaciones, recopilar respuestas y generar reportes PDF.

## Comandos Esenciales

```bash
# Ejecutar localmente
streamlit run app.py

# Ejecutar en Docker
docker-compose up --build

# Importar empleados desde Excel
python import_empleados.py

# Ver módulos y cálculos de demo
python demo_modulos.py
```

## Arquitectura

```
app.py              → UI Streamlit + páginas principales + generación de PDFs
database.py         → Capa de datos: SQLite raw SQL, todas las operaciones CRUD + migraciones
constants.py        → Constantes de todas las evaluaciones (preguntas, escalas, descripciones)
calculations.py     → Funciones de cálculo psicométrico por tipo de test
analysis.py         → Análisis e interpretación de resultados (aptitud, fortalezas, alertas)
charts.py           → Gráficos matplotlib/plotly por tipo de test (barras, radar, comparación)
pdfs.py             → Generación de reportes PDF con ReportLab para todas las pruebas
auth.py             → Autenticación admin, tokens HMAC, sesiones con idle timeout (60 min)
theme.py            → Tema visual + selector claro/oscuro en sidebar
utils.py            → Carga de archivos JSON, navegación (nav())
```

## Base de Datos

**Motor:** SQLite 3 — archivo `evaluaciones_rh.db` (dev) / `/app/data/evaluaciones_rh.db` (Docker)

**Tablas principales:**

| Tabla | Descripción |
|-------|-------------|
| `admins` | Usuarios admin (`role`: admin/superadmin, password SHA256) |
| `empresas` | Multi-tenant: empresas del grupo |
| `candidates` | Empleados/candidatos con datos demográficos y de cargo |
| `test_sessions` | Sesiones de evaluación por candidato (`test_type`, `status`, `questions_data` JSON, `evaluador_cedula`, `evaluador_nombre`) |
| `test_answers` | Respuestas individuales por pregunta |
| `test_results` | Resultado completo serializado como JSON |

**`test_type` válidos:**
- `disc` — Evaluación DISC de personalidad
- `valanti` — Valores Universales (5 traits). En negocio suele llamarse "Valenti", pero en código/BD se usa `valanti`.
- `wpi` — Work Personality Index (6 dimensiones)
- `eri` — Evaluación de Riesgo e Integridad (6 dimensiones)
- `talent_map` — Mapeo de Competencias (8 competencias)
- `desempeno` — Desempeño Operativo (rendimiento 1-5 + potencial 0-3) — **lo completa el admin**
- `desempeno_lider` — Desempeño Líderes (competencias 1-6 + rendimiento + potencial) — **flujo dual: employee_eval → jefe_eval**
- `desempeno_medios` — Desempeño Mandos Medios (competencias 1-6 + rendimiento + potencial) — **flujo dual: employee_eval → jefe_eval**
- `periodo_prueba` — Evaluación Período de Prueba (actuaciones + calificaciones) — **flujo dual: employee_eval → jefe_eval**

## Foco: Calificación Valenti (clave `valanti`)

### Flujo real de calificación (no asumir Likert 1-5)
1. Captura en [pages/candidate.py](pages/candidate.py): `page_valanti_test()`.
2. Cada pregunta tiene dos frases A/B y se distribuyen **3 puntos** entre ambas (`A + B = 3`).
3. Se persiste `answer_value` (A, rango 0-3) y `answer_b_value` (B, derivado como `3 - A`).
4. El cálculo usa solo la serie A acumulada en `responses`.

### Cálculo técnico
1. Mapeo de rasgos en [constants.py](constants.py): `VALANTI_TRAITS` (índices 1-based).
2. Suma directa por rasgo en [calculations.py](calculations.py): `calculate_valanti_results(responses)`.
3. Estandarización a T-score:
    - `z = (direct[trait] - VALANTI_AVGS[trait]) / VALANTI_SDS[trait]`
    - `standard[trait] = round(z * 10 + 50)`
4. Interpretación en [analysis.py](analysis.py): `analyze_valanti_aptitude(standard)`.

### Umbrales de interpretación usados hoy
- Valor alto: `T >= 55`
- Valor bajo: `T < 40`
- Valor crítico: `T < 30`
- Puntaje de aptitud: `avg_score + 5*altos - 8*bajos - 15*criticos` (acotado a 0-100)

### Reglas para cambios seguros en Valenti/Valanti
- No renombrar la clave `valanti` en DB, sesiones ni rutas de página sin migración completa.
- Si cambias escalas de respuesta (actual 0-3 en A), recalibra `VALANTI_AVGS` y `VALANTI_SDS` en [constants.py](constants.py).
- Mantén alineados cálculo ([calculations.py](calculations.py)) y análisis ([analysis.py](analysis.py)); no ajustar umbrales en un solo lado.
- Validar siempre el flujo completo: captura candidato -> guardado -> vista admin -> PDF.

Documentación de apoyo (no duplicar aquí): [REFACTORIZACION.md](REFACTORIZACION.md), [README.md](README.md).

## Tipos de Evaluación

### Tests completados por el candidato (sin timer en admin)
`disc`, `valanti`, `wpi`, `eri`, `talent_map`

### Evaluaciones completadas por el administrador/evaluador
`desempeno` — solo admin

### Evaluaciones con flujo dual (autoevaluación + jefe)
`desempeno_lider`, `desempeno_medios`, `periodo_prueba`

El flujo dual usa dos páginas del evaluador:
1. `_employee_eval` — El empleado se autoevalúa (status pasa a `employee_done`)
2. `_jefe_eval` — El jefe completa la evaluación final (status pasa a `completed`)

> En `page_candidate_select_test()`, las evaluaciones de tipo admin/evaluador se excluyen del flujo del candidato.

## Patrones de Código

### Agregar un nuevo tipo de test

1. **`constants.py`** — Definir constantes: preguntas/ítems, escalas, clasificaciones, colores
2. **`calculations.py`** — Función `calculate_X_results(scores) → dict` con promedios, clasificaciones, fortalezas, recomendaciones
3. **`analysis.py`** *(opcional)* — Función `analyze_X_aptitude(scores) → dict` con fortalezas/alertas según posición
4. **`app.py`**:
   - Función de gráfico `create_X_plot(scores)`
   - Función de PDF `generate_X_pdf(candidate, scores, ...)`
   - Página de evaluación `page_X_eval()`
   - Función de resultados admin `show_X_results_admin(results, candidate, session)`
   - Registrar en `PAGE_MAP` y en los selectboxes de asignación

### Patrón de cálculo
```python
def calculate_X_results(scores):
    # 1. Promedios directos
    promedio = sum(scores.values()) / len(scores)
    # 2. Clasificación contra umbrales en CLASIFICACION_X dict
    clasificacion = next(
        (info for nivel, info in sorted(CLASIFICACION_X.items(), key=lambda x: x[1]["min"], reverse=True)
         if promedio >= info["min"]), None)
    # 3. Retornar dict con promedios, clasificacion, fortalezas, recomendaciones
    return {"promedio": round(promedio, 2), "clasificacion": clasificacion, ...}
```

### Guardado de resultados en BD
```python
# En la página de evaluación, al enviar el formulario:
results = calculate_X_results(scores)
db.save_test_results(session_id, results)
db.complete_session(session_id)
```

### Navegación (Streamlit)
```python
from utils import nav
nav("nombre_pagina")  # Actualiza st.session_state.page
st.rerun()            # Siempre llamar después de nav()
```

## Archivos de Preguntas (JSON)

| Archivo | Test |
|---------|------|
| `questions_es.json` | DISC |
| `questions_wpi.json` | WPI |
| `questions_eri.json` | ERI |
| `questions_talent_map.json` | Talent Map |
| `streangths.json` | Fortalezas/Debilidades por estilo DISC |

Las evaluaciones de desempeño usan ítems fijos definidos directamente en `constants.py`.

## Competencias Organizacionales (FO-GH-41 — Líderes)

7 competencias con niveles 1-6 por familia de cargo:

| Cargo | Nivel requerido aprox. |
|-------|----------------------|
| ANALISTA | 2 |
| COMERCIAL | 2-3 |
| COORDINADOR | 3-4 |
| LIDER | 4-5 |
| GERENTE/DIRECTOR | 5-6 |

Las competencias son: Pensamiento Estratégico, Flexibilidad y Agilidad, Orientación a Resultados, Toma de Decisiones y Evaluación de Riesgos, Orientación al Cliente, Autoliderazgo y Liderazgo, Comunicación/Trabajo en Equipo/Transparencia.

## Formularios Excel Originales

| Código | Archivo | Tipo en sistema |
|--------|---------|-----------------|
| FO-GH-40 | Evaluación Desempeño Operativo V.2 | `desempeno` |
| FO-GH-41 | Evaluación Desempeño Líderes V.2 | `desempeno_lider` |
| FO-GH-46 | Evaluación Período de Prueba V.1 | `periodo_prueba` |

## Convenciones

- `snake_case` para variables y funciones, `UPPER_CASE` para constantes
- Arquitectura funcional (sin clases)
- `st.session_state` para toda la persistencia entre páginas
- SHA256 para contraseñas (sin salt — solo para prototipo interno)
- Los IDs de sesión son UUID truncados a 8 caracteres
- Los resultados se serializan como JSON en `test_results.results_json`

## Notas de Deployment

- Dev: `streamlit run app.py` (puerto 8501)
- Prod: Docker + Nginx reverso con HTTPS (ver [DOCKER.md](DOCKER.md) y [DESPLIEGUE_PRODUCCION.md](DESPLIEGUE_PRODUCCION.md))
- **Flujo real de deploy:** `scp` al servidor → `docker cp` al contenedor → `docker restart` si es necesario. Ver detalles en deploy.md del repo memory.
- La BD debe estar en volumen Docker (`./data:/app/data`) para persistencia
- `docker-compose restart` NO actualiza código (usa imagen cacheada); siempre usar `docker cp`
- Base URL path en prod: `/evaluacionesrh` (configurado en `STREAMLIT_SERVER_BASE_URL_PATH`)
- Health check: `curl http://localhost:8501/evaluacionesrh/_stcore/health`
- Zona horaria: `TZ=America/Bogota` en compose + `datetime.now(timezone(timedelta(hours=-5)))` en código

## Pitfalls Conocidos

- `PRAGMA foreign_keys = ON` se activa en cada conexión en `database.py`
- Las evaluaciones de tipo "admin" (`desempeno`, `desempeno_lider`, `desempeno_medios`, `periodo_prueba`) deben filtrarse en `page_candidate_select_test()` 
- El flujo dual (`employee_eval` → `jefe_eval`) depende del status `employee_done` en `test_sessions`; si no se completa la autoevaluación, el jefe no puede evaluar
- Streamlit recarga el script completo en cada interacción — usar `st.session_state` para preservar estado
- `st.rerun()` siempre después de `nav()` para que el cambio de página tome efecto
- `docker-compose restart` NO actualiza el código (usa imagen cacheada); usar `docker cp` + `docker restart`
