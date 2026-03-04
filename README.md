# 🚗 FleetOS — Sistema de Alquiler de Vehículos

Minicaso práctico que implementa **Arquitectura en Capas** con los patrones
**Factory Method, Adapter, Strategy y DAO**, y los principios **SOLID**.
Incluye una **API REST con Flask** y una **interfaz web** completa.

---

## Requisitos previos

- Python **3.10 o superior**
- pip (viene incluido con Python)

Verifica tu versión con:
```bash
python --version
```

---

## Estructura del proyecto

```
alquiler_vehiculos_proyecto/
│
├── requirements.txt                     ← Dependencias del proyecto
├── .gitignore                           ← Archivos a ignorar en Git
│
└── vehicle_rental/
    │
    ├── main.py                          ← CLI: punto de entrada consola
    │
    ├── api/
    │   └── app.py                       ← API REST Flask (servidor web)
    │
    ├── frontend/
    │   ├── templates/index.html         ← Interfaz web
    │   └── static/
    │       ├── css/style.css            ← Estilos
    │       └── js/app.js                ← Lógica del frontend
    │
    ├── presentation/
    │   └── cli.py                       ← Capa Presentación: menú CLI
    │
    ├── business/
    │   ├── factory/vehicle_factory.py   ← Patrón Factory Method
    │   ├── pricing/pricing_strategy.py  ← Patrón Strategy
    │   └── service/rental_service.py    ← Servicio central (orquesta todo)
    │
    ├── data/
    │   ├── models/entities.py           ← Entidades del dominio
    │   ├── dao/dao.py                   ← Patrón DAO (en memoria)
    │   ├── dao/json_dao.py              ← Patrón DAO (persistencia JSON)
    │   └── db/                          ← Archivos JSON generados al correr
    │       ├── vehicles.json
    │       ├── customers.json
    │       └── rentals.json
    │
    └── infrastructure/
        └── adapters/insurance_adapter.py  ← Patrón Adapter
```

---

## Instalación y configuración

### Paso 1 — Crear el entorno virtual

Un entorno virtual aisla las dependencias del proyecto para no afectar
otras instalaciones de Python en tu sistema.

**Linux / Mac:**
```bash
# Entra a la carpeta raíz del proyecto
cd alquiler_vehiculos_proyecto

# Crea el entorno virtual
python -m venv venv

# Actívalo
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
# Entra a la carpeta raíz del proyecto
cd alquiler_vehiculos_proyecto

# Crea el entorno virtual
python -m venv venv

# Actívalo
venv\Scripts\activate
```

> **Nota Windows:** Si PowerShell muestra un error de permisos al activar,
> ejecuta primero este comando y luego vuelve a activar:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Cuando el entorno esté activo, verás `(venv)` al inicio de tu terminal:
```
(venv) usuario@pc:~/alquiler_vehiculos_proyecto$   ← Linux/Mac
(venv) C:\...\alquiler_vehiculos_proyecto>         ← Windows
```

---

### Paso 2 — Instalar dependencias

Con el entorno virtual activo, instala todo con un solo comando:

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene:
```
flask
```

---

### Paso 3 — Correr el servidor web

```bash
python -m vehicle_rental.api.app
```

Deberías ver:
```
🚗  Sistema de Alquiler de Vehículos
📡  API corriendo en http://localhost:5000
🌐  Abre http://localhost:5000 en tu navegador
* Running on http://127.0.0.1:5000
```

Abre tu navegador en: **http://127.0.0.1:5000**

La primera vez que corras el sistema se crearán automáticamente los archivos
JSON con datos de ejemplo en `vehicle_rental/data/db/`.

---

## Desactivar el entorno virtual

Cuando termines de trabajar, desactiva el entorno con:

```bash
deactivate
```

---

## Referencia rápida de comandos

| Acción | Linux/Mac | Windows |
|--------|-----------|---------|
| Crear entorno | `python -m venv venv` | `python -m venv venv` |
| Activar entorno | `source venv/bin/activate` | `venv\Scripts\activate` |
| Instalar deps | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| Correr web | `python -m vehicle_rental.api.app` | `python -m vehicle_rental.api.app` |
| Correr CLI | `python -m vehicle_rental.main` | `python -m vehicle_rental.main` |
| Desactivar entorno | `deactivate` | `deactivate` |

---

## Patrones de diseño implementados

| Patrón | Archivo | Descripción |
|--------|---------|-------------|
| **Factory Method** | `business/factory/vehicle_factory.py` | Crea Car, Truck o SUV sin acoplar al cliente |
| **Strategy** | `business/pricing/pricing_strategy.py` | 4 estrategias de precio intercambiables en runtime |
| **Adapter** | `infrastructure/adapters/insurance_adapter.py` | Traduce ExternalInsuranceAPI a InsuranceService |
| **DAO** | `data/dao/json_dao.py` | Abstrae la persistencia, datos guardados en JSON |

## Estrategias de precio disponibles

| Nro | Estrategia | Fórmula |
|-----|------------|---------|
| 1 | Por día | `tarifa_diaria × días` |
| 2 | Por kilómetro | `$0.35 × km_estimados` |
| 3 | Tarifa plana | `$199.99` fijo |
| 4 | Semanal con descuento | Semanas completas −15% |

---

## Principios SOLID aplicados

- **S** – Cada clase tiene una única razón de cambio.
- **O** – Agregar vehículos, estrategias o proveedores no modifica código existente.
- **L** – Toda estrategia/fábrica es sustituible sin efectos secundarios.
- **I** – Interfaces pequeñas y específicas (`InsuranceService`, `BaseDAO`).
- **D** – `RentalService` depende de abstracciones, no de implementaciones concretas.
