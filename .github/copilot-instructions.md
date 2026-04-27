# Copilot Instructions — Evaluaciones RH

## Descripción del Proyecto
Sistema integral de **evaluaciones psicométricas y de desempeño** para RRHH, construido con **Streamlit + SQLite**. Multi-tenant (empresas), soporte para candidatos y evaluadores externos.

## Stack
- **Frontend/Backend:** Streamlit (Python 3.11)
- **Base de datos:** SQLite (`/app/data/evaluaciones_rh.db` en Docker, `data/evaluaciones_rh.db` en local)
- **PDFs:** ReportLab
- **Gráficos:** Matplotlib
- **Deploy:** Docker + Nginx (VPS `164.68.118.86`)
- **Container producción:** `evaluaciones-rh-prod`

## Arquitectura de Módulos (refactorizada)

```
app.py              → Punto de entrada: config Streamlit, CSS global, PAGE_MAP, routing
database.py         → Capa de datos SQLite — todas las operaciones CRUD
constants.py        → Constantes de todas las evaluaciones (preguntas, escalas, colores)
calculations.py     → Funciones de cálculo psicométrico por tipo de test
analysis.py         → Análisis e interpretación de resultados (aptitud, fortalezas, alertas)
utils.py            → nav(), render_timer(), load_disc_questions(), load_disc_descriptions(), load_wpi_questions()
theme.py            → _apply_theme_override(), _render_theme_switcher()
auth.py             → Sesión admin: login, logout, idle timeout, ADMIN_SESSION_SECRET
charts.py           → 13 funciones matplotlib: DISC, VALANTI, WPI, ERI, Talent Map, Desempeño
pdfs.py             → 8 funciones ReportLab de generación PDF por tipo de evaluación
pages/
  __init__.py       → Vacío (paquete)
  admin.py          → page_admin_login, page_admin_dashboard, show_*_results_admin
  candidate.py      → page_candidate_login, page_candidate_select_test, page_disc_test, page_valanti_test, page_wpi_test, page_eri_test, page_candidate_done
  desempeno.py      → page_desempeno_eval, show_desempeno_results_admin, page_desempeno_lider_eval, show_desempeno_lider_results_admin, page_periodo_prueba_eval, show_periodo_prueba_results_admin
  evaluador.py      → page_evaluador_login, page_evaluador_dashboard, page_desempeno_lider_employee_eval, page_periodo_prueba_employee_eval, page_desempeno_lider_jefe_eval, page_periodo_prueba_jefe_eval
  talent_map.py     → page_talent_map_test, show_talent_map_results_admin
```

## Tipos de Evaluación (`test_type`)
| Valor | Nombre | Completado por |
|-------|--------|----------------|
| `disc` | DISC Personalidad | Candidato |
| `valanti` | Valores Universales | Candidato |
| `wpi` | Work Personality Index | Candidato |
| `eri` | Riesgo e Integridad | Candidato |
| `talent_map` | Mapeo de Competencias | Candidato |
| `desempeno` | Desempeño Operativo | Admin |
| `desempeno_lider` | Desempeño Líderes | Admin + Evaluador |
| `periodo_prueba` | Período de Prueba | Admin + Evaluador |

## Base de Datos — Tablas Principales
| Tabla | Descripción |
|-------|-------------|
| `admins` | Usuarios admin (`role`: admin/superadmin, password SHA256) |
| `empresas` | Multi-tenant |
| `candidates` | Empleados/candidatos |
| `test_sessions` | Sesiones de evaluación (`test_type`, `status`, `questions_data` JSON) |
| `test_answers` | Respuestas individuales |
| `test_results` | Resultado completo como JSON |

## Patrones Importantes

### Navegación
```python
from utils import nav
nav("nombre_pagina")
st.rerun()
```

### Valores None en BD (patrón correcto)
```python
# CORRECTO — maneja NULL de SQLite:
(c.get("campo") or "").lower()
# INCORRECTO — falla si el valor existe pero es None:
c.get("campo", "").lower()
```

### Deploy a producción (NO usar docker-compose restart)
```bash
# Subir archivos al servidor
scp -i ~/.ssh/id_rsa archivo.py root@164.68.118.86:/tmp/
ssh -i ~/.ssh/id_rsa root@164.68.118.86 "docker cp /tmp/archivo.py evaluaciones-rh-prod:/app/archivo.py"
ssh -i ~/.ssh/id_rsa root@164.68.118.86 "docker restart evaluaciones-rh-prod"
```

### Deploy local Docker
```powershell
# Build (desde la carpeta del proyecto)
docker build -t evaluaciones-rh-local "c:\ruta\al\proyecto"
# Levantar con BD de producción
docker run -d --name evaluaciones-rh-local -p 8501:8501 -v "ruta\data:/app/data" evaluaciones-rh-local
# Actualizar un archivo sin rebuild
docker cp archivo.py evaluaciones-rh-local:/app/archivo.py
```

## Archivos de Preguntas (JSON)
| Archivo | Test |
|---------|------|
| `questions_es.json` | DISC |
| `questions_wpi.json` | WPI |
| `questions_eri.json` | ERI |
| `questions_talent_map.json` | Talent Map |

## Reglas de Desarrollo
- No usar `docker-compose restart` en producción — solo `docker cp` + `docker restart`
- El container de producción se llama `evaluaciones-rh-prod` (no `evaluaciones-rh-app`)
- La BD de producción está en el container en `/app/data/evaluaciones_rh.db`
- Para extraer la BD de producción: `docker cp evaluaciones-rh-prod:/app/data/evaluaciones_rh.db /tmp/` → SCP
- `render_timer` vive en `utils.py`, importado en `pages/candidate.py` y `pages/talent_map.py`
