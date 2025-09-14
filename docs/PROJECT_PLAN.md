# 🎯 Project Plan: Univerzální Process Manager

## 📊 Celkový postup / Overall Progress

### Přehled fází / Phase Overview
- [x] **Fáze 0**: Analýza a plánování ✅ DOKONČENO
- [x] **Fáze 1**: MVP - Základní funkcionalita ✅ DOKONČENO
- [ ] **Fáze 2**: Monitoring (1 týden)
- [ ] **Fáze 3**: Restart Politiky (1 týden)
- [ ] **Fáze 4**: Web Dashboard (2 týdny)
- [ ] **Fáze 5**: Plugin System (2 týdny)
- [ ] **Fáze 6**: Production Features (2 týdny)

### Aktuální stav / Current Status
**📅 Datum zahájení / Start Date**: 12.9.2025
**🎯 Aktuální fáze / Current Phase**: Fáze 1 - MVP dokončeno
**✅ Dokončeno / Completed**: 2/7 fází
**📈 Celkový postup / Overall Progress**: 28%

---

## 📋 Obsah / Table of Contents

1. [Analýza problému / Problem Analysis](#analýza-problému--problem-analysis)
2. [Cíle projektu / Project Goals](#cíle-projektu--project-goals)
3. [Architektura řešení / Solution Architecture](#architektura-řešení--solution-architecture)
4. [Technologický stack / Technology Stack](#technologický-stack--technology-stack)
5. [Klíčové komponenty / Key Components](#klíčové-komponenty--key-components)
6. [Implementační roadmapa / Implementation Roadmap](#implementační-roadmapa--implementation-roadmap)
7. [Checklist úkolů / Task Checklist](#checklist-úkolů--task-checklist)

---

## Analýza problému / Problem Analysis

### 🇨🇿 Česká verze

Současné řešení správy procesů má několik zásadních problémů:
- **Fragmentace**: Různé nástroje pro různé technologie (PM2 pro Node.js, supervisor pro Python, systemd pro Linux služby)
- **Složitost**: Každý nástroj má vlastní konfiguraci, API a způsob ovládání
- **Nedostatečná univerzálnost**: Chybí jednotné řešení pro různé typy aplikací
- **Invazivnost**: Existující řešení často vyžadují významné změny v kódu aplikace
- **Omezená observabilita**: Obtížné centrální sledování všech procesů

### 🇬🇧 English Version

Current process management solutions have several fundamental problems:
- **Fragmentation**: Different tools for different technologies (PM2 for Node.js, supervisor for Python, systemd for Linux services)
- **Complexity**: Each tool has its own configuration, API, and control method
- **Lack of universality**: Missing unified solution for different application types
- **Invasiveness**: Existing solutions often require significant changes in application code
- **Limited observability**: Difficult central monitoring of all processes

---

## Cíle projektu / Project Goals

### 🇨🇿 Česká verze

1. **Univerzálnost**: Jeden nástroj pro všechny typy aplikací (Python, Node.js, Go, Java, atd.)
2. **Jednoduchost**: Minimální konfigurace, intuitivní ovládání
3. **Neinvazivnost**: Integrace pomocí 1-3 řádků kódu
4. **Spolehlivost**: Robustní správa procesů s automatickým restartem
5. **Observabilita**: Centrální monitoring všech procesů
6. **Škálovatelnost**: Od jednoduché aplikace po distribuované systémy

### 🇬🇧 English Version

1. **Universality**: One tool for all application types (Python, Node.js, Go, Java, etc.)
2. **Simplicity**: Minimal configuration, intuitive control
3. **Non-invasiveness**: Integration with 1-3 lines of code
4. **Reliability**: Robust process management with automatic restart
5. **Observability**: Central monitoring of all processes
6. **Scalability**: From simple application to distributed systems

---

## Architektura řešení / Solution Architecture

### 🇨🇿 Česká verze

```
┌─────────────────────────────────────────────┐
│              CLI Interface                  │
│         pm start | stop | status            │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│            Process Manager Core             │
├─────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────┐        │
│  │ Registry │ Monitor  │Controller│        │
│  └──────────┴──────────┴──────────┘        │
├─────────────────────────────────────────────┤
│            Storage Layer                    │
│  ┌──────────┬──────────┬──────────┐        │
│  │  SQLite  │  Redis   │   JSON   │        │
│  └──────────┴──────────┴──────────┘        │
├─────────────────────────────────────────────┤
│           Process Runners                   │
│  ┌──────────┬──────────┬──────────┐        │
│  │Subprocess│  Docker  │ SystemD  │        │
│  └──────────┴──────────┴──────────┘        │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│         Managed Applications                │
│   Python | Node.js | Go | Java | etc.       │
└─────────────────────────────────────────────┘
```

### 🇬🇧 English Version

The architecture follows a modular, layered approach with clear separation of concerns. Each layer can be independently extended or replaced, ensuring maximum flexibility and maintainability.

---

## Technologický stack / Technology Stack

### 🇨🇿 Česká verze

**Backend (Core)**:
- Python 3.10+ s FastAPI pro REST API
- SQLite pro lokální storage (výchozí)
- Redis pro distribuované prostředí (volitelné)
- asyncio pro asynchronní operace
- psutil pro systémové metriky

**Frontend (Dashboard)**:
- React 18+ s TypeScript
- TailwindCSS pro styling
- WebSocket pro real-time aktualizace
- Recharts pro vizualizace

**CLI**:
- Click (Python) pro command-line interface
- Rich pro formátovaný výstup

### 🇬🇧 English Version

**Backend (Core)**:
- Python 3.10+ with FastAPI for REST API
- SQLite for local storage (default)
- Redis for distributed environments (optional)
- asyncio for asynchronous operations
- psutil for system metrics

**Frontend (Dashboard)**:
- React 18+ with TypeScript
- TailwindCSS for styling
- WebSocket for real-time updates
- Recharts for visualizations

**CLI**:
- Click (Python) for command-line interface
- Rich for formatted output

---

## Klíčové komponenty / Key Components

### 🇨🇿 Česká verze

#### 1. Process Registry
- **Účel**: Centrální evidence všech procesů
- **Funkce**: 
  - Registrace nových procesů
  - Ukládání konfigurace
  - Správa metadat

#### 2. Process Monitor
- **Účel**: Sledování stavu procesů
- **Funkce**:
  - Heartbeat systém
  - Health checks
  - Sběr metrik (CPU, RAM, I/O)

#### 3. Process Controller
- **Účel**: Řízení životního cyklu procesů
- **Funkce**:
  - Start/Stop/Restart operace
  - Graceful shutdown
  - Restart politiky

#### 4. Plugin System
- **Účel**: Integrace s různými technologiemi
- **Funkce**:
  - Language-specific pluginy
  - Framework adaptéry
  - Custom runners

#### 5. Web Dashboard
- **Účel**: Vizuální správa a monitoring
- **Funkce**:
  - Real-time status
  - Logy a metriky
  - Ovládací prvky

### 🇬🇧 English Version

#### 1. Process Registry
- **Purpose**: Central registry of all processes
- **Functions**: 
  - New process registration
  - Configuration storage
  - Metadata management

#### 2. Process Monitor
- **Purpose**: Process status monitoring
- **Functions**:
  - Heartbeat system
  - Health checks
  - Metrics collection (CPU, RAM, I/O)

#### 3. Process Controller
- **Purpose**: Process lifecycle management
- **Functions**:
  - Start/Stop/Restart operations
  - Graceful shutdown
  - Restart policies

#### 4. Plugin System
- **Purpose**: Integration with various technologies
- **Functions**:
  - Language-specific plugins
  - Framework adapters
  - Custom runners

#### 5. Web Dashboard
- **Purpose**: Visual management and monitoring
- **Functions**:
  - Real-time status
  - Logs and metrics
  - Control elements

---

## Implementační roadmapa / Implementation Roadmap

### 🇨🇿 Česká verze

#### Fáze 1: MVP (1-2 týdny)
- [ ] Základní Process Registry s SQLite
- [ ] Subprocess runner pro Python/Node.js
- [ ] CLI s příkazy start/stop/status
- [ ] Jednoduchý heartbeat systém

#### Fáze 2: Monitoring (1 týden)
- [ ] Health check systém
- [ ] Sběr metrik (CPU, RAM)
- [ ] Strukturované logování
- [ ] Status API endpoint

#### Fáze 3: Restart Politiky (1 týden)
- [ ] on-failure/always/never politiky
- [ ] Exponenciální backoff
- [ ] Max retry limit
- [ ] Graceful shutdown

#### Fáze 4: Web Dashboard (2 týdny)
- [ ] React aplikace
- [ ] Real-time status přes WebSocket
- [ ] Vizualizace metrik
- [ ] Ovládací prvky

#### Fáze 5: Plugin System (2 týdny)
- [ ] Framework adaptéry (FastAPI, Express)
- [ ] Language pluginy
- [ ] Custom health checks
- [ ] Config management

#### Fáze 6: Production Features (2 týdny)
- [ ] Distribuovaný mód
- [ ] Security (JWT auth)
- [ ] Audit logging
- [ ] Backup/restore

### 🇬🇧 English Version

#### Phase 1: MVP (1-2 weeks)
- [ ] Basic Process Registry with SQLite
- [ ] Subprocess runner for Python/Node.js
- [ ] CLI with start/stop/status commands
- [ ] Simple heartbeat system

#### Phase 2: Monitoring (1 week)
- [ ] Health check system
- [ ] Metrics collection (CPU, RAM)
- [ ] Structured logging
- [ ] Status API endpoint

#### Phase 3: Restart Policies (1 week)
- [ ] on-failure/always/never policies
- [ ] Exponential backoff
- [ ] Max retry limit
- [ ] Graceful shutdown

#### Phase 4: Web Dashboard (2 weeks)
- [ ] React application
- [ ] Real-time status via WebSocket
- [ ] Metrics visualization
- [ ] Control elements

#### Phase 5: Plugin System (2 weeks)
- [ ] Framework adapters (FastAPI, Express)
- [ ] Language plugins
- [ ] Custom health checks
- [ ] Config management

#### Phase 6: Production Features (2 weeks)
- [ ] Distributed mode
- [ ] Security (JWT auth)
- [ ] Audit logging
- [ ] Backup/restore

---

## Checklist úkolů / Task Checklist

### 🇨🇿 Česká verze

#### ✅ Analýza a plánování (DOKONČENO)
- [x] Analyzovat existující řešení (PM2, supervisor, systemd)
- [x] Prostudovat současný stav projektu
- [x] Definovat cíle a požadavky
- [x] Vytvořit architekturu řešení
- [x] Sestavit implementační roadmapu
- [x] Vytvořit projektový plán

#### Příprava projektu ✅ DOKONČENO
- [x] Vytvořit projektovou strukturu
- [x] Nastavit Python virtuální prostředí
- [x] Inicializovat Git repository
- [x] Nastavit základní dependencies

#### Fáze 1: Core Components ✅ DOKONČENO
- [x] Implementovat Process Registry (SQLite)
- [x] Vytvořit Process Model a schéma
- [x] Implementovat základní Process Runner
- [x] Vytvořit CLI interface (Click)
- [x] Implementovat start/stop/status příkazy
- [x] Přidat heartbeat systém
- [x] Vytvořit vzorové aplikace pro testování

#### Fáze 2: Monitoring
- [ ] Implementovat Health Check systém
- [ ] Přidat sběr metrik (psutil)
- [ ] Vytvořit strukturované logování
- [ ] Implementovat REST API (FastAPI)
- [ ] Přidat status endpoint
- [ ] Vytvořit metrics endpoint

#### Fáze 3: Process Management
- [ ] Implementovat restart politiky
- [ ] Přidat exponenciální backoff
- [ ] Implementovat graceful shutdown
- [ ] Přidat dependency management
- [ ] Vytvořit process groups

#### Fáze 4: Dashboard
- [ ] Inicializovat React aplikaci
- [ ] Nastavit TailwindCSS
- [ ] Implementovat WebSocket client
- [ ] Vytvořit status komponenty
- [ ] Přidat metriky grafy
- [ ] Implementovat ovládací prvky

#### Fáze 5: Plugins
- [ ] Vytvořit plugin architekturu
- [ ] Implementovat Python plugin
- [ ] Implementovat Node.js plugin
- [ ] Přidat framework adaptéry
- [ ] Vytvořit custom runner API

#### Fáze 6: Production
- [ ] Přidat autentizaci (JWT)
- [ ] Implementovat audit logging
- [ ] Vytvořit backup/restore
- [ ] Přidat distribuovaný mód
- [ ] Napsat dokumentaci
- [ ] Vytvořit Docker image

### 🇬🇧 English Version

#### ✅ Analysis and Planning (COMPLETED)
- [x] Analyze existing solutions (PM2, supervisor, systemd)
- [x] Study current project state
- [x] Define goals and requirements
- [x] Create solution architecture
- [x] Build implementation roadmap
- [x] Create project plan

#### Project Setup
- [ ] Create project structure
- [ ] Set up Python virtual environment
- [ ] Initialize Git repository
- [ ] Set up basic dependencies

#### Phase 1: Core Components
- [ ] Implement Process Registry (SQLite)
- [ ] Create Process Model and schema
- [ ] Implement basic Process Runner
- [ ] Create CLI interface (Click)
- [ ] Implement start/stop/status commands
- [ ] Add heartbeat system
- [ ] Write unit tests

#### Phase 2: Monitoring
- [ ] Implement Health Check system
- [ ] Add metrics collection (psutil)
- [ ] Create structured logging
- [ ] Implement REST API (FastAPI)
- [ ] Add status endpoint
- [ ] Create metrics endpoint

#### Phase 3: Process Management
- [ ] Implement restart policies
- [ ] Add exponential backoff
- [ ] Implement graceful shutdown
- [ ] Add dependency management
- [ ] Create process groups

#### Phase 4: Dashboard
- [ ] Initialize React application
- [ ] Set up TailwindCSS
- [ ] Implement WebSocket client
- [ ] Create status components
- [ ] Add metrics charts
- [ ] Implement control elements

#### Phase 5: Plugins
- [ ] Create plugin architecture
- [ ] Implement Python plugin
- [ ] Implement Node.js plugin
- [ ] Add framework adapters
- [ ] Create custom runner API

#### Phase 6: Production
- [ ] Add authentication (JWT)
- [ ] Implement audit logging
- [ ] Create backup/restore
- [ ] Add distributed mode
- [ ] Write documentation
- [ ] Create Docker image

---

## Klíčové principy / Key Principles

### 🇨🇿 Česká verze

1. **KISS (Keep It Simple, Stupid)**: Jednoduchost je klíč
2. **DRY (Don't Repeat Yourself)**: Žádná duplikace kódu
3. **Zero-config**: Funguje bez konfigurace
4. **Progressive Enhancement**: Postupné přidávání funkcí
5. **Non-breaking**: Zpětná kompatibilita

### 🇬🇧 English Version

1. **KISS (Keep It Simple, Stupid)**: Simplicity is key
2. **DRY (Don't Repeat Yourself)**: No code duplication
3. **Zero-config**: Works without configuration
4. **Progressive Enhancement**: Gradual feature addition
5. **Non-breaking**: Backward compatibility

---

## Příklady použití / Usage Examples

### 🇨🇿 Česká verze

```bash
# Instalace
pip install uniprocess

# Registrace a spuštění aplikace
pm register ./backend --name "API Server" --type python
pm register ./frontend --name "Web UI" --type node
pm start all

# Monitoring
pm status
pm logs api-server --tail 50
pm metrics web-ui

# Správa
pm restart api-server
pm stop web-ui
pm config api-server --set "restart_policy=always"
```

### 🇬🇧 English Version

```bash
# Installation
pip install uniprocess

# Register and start application
pm register ./backend --name "API Server" --type python
pm register ./frontend --name "Web UI" --type node
pm start all

# Monitoring
pm status
pm logs api-server --tail 50
pm metrics web-ui

# Management
pm restart api-server
pm stop web-ui
pm config api-server --set "restart_policy=always"
```

---

## Integrace do existujícího kódu / Integration into Existing Code

### 🇨🇿 Česká verze

**Python (FastAPI)**:
```python
from uniprocess import ProcessManager

# Jediný řádek pro integraci
pm = ProcessManager("backend", auto_register=True)

# Existující kód zůstává nezměněný
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

**Node.js (Express)**:
```javascript
const ProcessManager = require('uniprocess');

// Jediný řádek pro integraci
const pm = new ProcessManager('frontend', { autoRegister: true });

// Existující kód zůstává nezměněný
const app = express();
app.listen(3000);
```

### 🇬🇧 English Version

**Python (FastAPI)**:
```python
from uniprocess import ProcessManager

# Single line for integration
pm = ProcessManager("backend", auto_register=True)

# Existing code remains unchanged
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

**Node.js (Express)**:
```javascript
const ProcessManager = require('uniprocess');

// Single line for integration
const pm = new ProcessManager('frontend', { autoRegister: true });

// Existing code remains unchanged
const app = express();
app.listen(3000);
```

---

## Očekávané výsledky / Expected Results

### 🇨🇿 Česká verze

1. **Jednotná správa**: Všechny procesy na jednom místě
2. **Zvýšená spolehlivost**: Automatický restart, health checks
3. **Lepší observabilita**: Centrální monitoring a logování
4. **Snížená složitost**: Jeden nástroj místo několika
5. **Rychlejší development**: Méně času stráveného správou infrastruktury

### 🇬🇧 English Version

1. **Unified management**: All processes in one place
2. **Increased reliability**: Automatic restart, health checks
3. **Better observability**: Central monitoring and logging
4. **Reduced complexity**: One tool instead of several
5. **Faster development**: Less time spent on infrastructure management

---

## Rizika a mitigace / Risks and Mitigation

### 🇨🇿 Česká verze

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|--------|-----------------|-------|----------|
| Výkonnostní overhead | Střední | Nízký | Optimalizace, caching |
| Kompatibilita s OS | Nízká | Střední | Testování na různých OS |
| Složitost integrace | Nízká | Vysoký | Jednoduché API, dokumentace |
| Race conditions | Střední | Vysoký | Proper locking, atomické operace |

### 🇬🇧 English Version

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Performance overhead | Medium | Low | Optimization, caching |
| OS compatibility | Low | Medium | Testing on different OS |
| Integration complexity | Low | High | Simple API, documentation |
| Race conditions | Medium | High | Proper locking, atomic operations |

---

## Závěr / Conclusion

### 🇨🇿 Česká verze

Tento projekt vytvoří univerzální, snadno použitelný Process Manager, který výrazně zjednoduší správu aplikací. Klíčem k úspěchu je postupná implementace s důrazem na jednoduchost a spolehlivost.

### 🇬🇧 English Version

This project will create a universal, easy-to-use Process Manager that will significantly simplify application management. The key to success is gradual implementation with emphasis on simplicity and reliability.

---

## 📝 Poznámky a aktualizace / Notes and Updates

### 🇨🇿 Česká verze

#### 12.9.2025 - Zahájení projektu
- ✅ Dokončena analýza existujících řešení (PM2, supervisor, systemd, Overmind, Goreman)
- ✅ Prostudovány dokumenty MANAGER_PROCESS_ANALYZE.md a navrh.md
- ✅ Vytvořen kompletní projektový plán s checklistem
- ✅ Definována architektura a roadmapa implementace
- 📋 Připraven detailní checklist s možností sledování postupu
- 🎯 Další krok: Zahájení Fáze 1 - vytvoření MVP

#### 13.9.2025 - Dokončení MVP
- ✅ Implementováno kompletní jádro Process Manageru
  - Process Registry s SQLite databází
  - Process Monitor pro sledování zdraví procesů
  - Process Controller pro řízení životního cyklu
  - Heartbeat Manager pro real-time monitoring
- ✅ Vytvořeno CLI rozhraní s Rich formátováním
- ✅ Implementovány vzorové aplikace (Python Flask, Node.js Express)
- ✅ Vytvořena dokumentace a demo skript
- 🎯 Systém připraven k testování a rozšíření

### 🇬🇧 English Version

#### September 12, 2025 - Project Initiation
- ✅ Completed analysis of existing solutions (PM2, supervisor, systemd, Overmind, Goreman)
- ✅ Studied documents MANAGER_PROCESS_ANALYZE.md and navrh.md
- ✅ Created complete project plan with checklist
- ✅ Defined architecture and implementation roadmap
- 📋 Prepared detailed checklist with progress tracking capability
- 🎯 Next step: Start Phase 1 - MVP creation