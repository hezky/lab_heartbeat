# Analýza Správy Procesů - Process Manager

## 1. Současný Stav Systému

### 1.1 Architektura
Projekt využívá **hybridní přístup** ke správě procesů, kombinující:
- **Bash skripty** pro základní spouštění/zastavování
- **JSON soubor** pro sledování stavu (`.app_status.json`)
- **Heartbeat systém** pro monitoring v reálném čase
- **Backend/Frontend komponenty** pro interní správu

### 1.2 Klíčové Komponenty

#### A. Stavový soubor `.app_status.json`
**Umístění:** `.config/.app_status.json`

**Struktura:**
```json
{
  "last_updated_by": "backend|frontend",
  "heartbeat_interval_seconds": 120,
  "allowed_time_drift_seconds": 180,
  "frontend": {
    "last_heartbeat": "ISO 8601 timestamp",
    "state": "running|stopped|error|inactive",
    "version": "1.0.0",
    "uptime_seconds": number,
    "url": "current URL",
    "last_error": "error message"
  },
  "backend": {
    "last_heartbeat": "ISO 8601 timestamp",
    "state": "running|stopped|error",
    "version": "1.0.0", 
    "uptime_seconds": number,
    "pid": process_id
  }
}
```

#### B. Bash Skripty

**1. `start.sh`**
- Načítá konfiguraci portů z `.config/.config.json`
- Kontroluje volné porty pomocí `lsof`
- Zastavuje existující procesy
- Spouští backend (Python/uvicorn) a frontend (npm/React)
- Vytváří virtuální prostředí a instaluje závislosti
- Používá `nohup` pro běh na pozadí
- Loguje do `backend.log` a `frontend.log`

**2. `stop.sh`**
- Zastavuje procesy pomocí `pkill`
- Uvolňuje porty (8000, 3000)
- Kontroluje úspěšnost zastavení

**3. `state.sh`**
- Zobrazuje aktuální stav aplikace
- Kontroluje běžící procesy přes porty
- Čte heartbeat data z `.app_status.json`
- Zobrazuje využití paměti procesů

#### C. Backend Heartbeat Systém

**Soubor:** `backend/heartbeat.py`

**Třída HeartbeatManager:**
- **Inicializace:** Nastavuje komponentu, cestu k status souboru
- **Heartbeat interval:** 120 sekund
- **Allowed drift:** 180 sekund
- **Threading:** Běží v samostatném vlákně
- **Atomické zápisy:** Používá temp soubory a file locking
- **Health checking:** Kontroluje freshness heartbeatů

**Klíčové metody:**
- `start_heartbeat()`: Spouští heartbeat vlákno
- `update_heartbeat()`: Aktualizuje status
- `check_component_health()`: Kontroluje zdraví komponenty
- `get_system_status()`: Vrací celkový status systému

**Integrace v `main.py`:**
- Heartbeat se spouští při startu aplikace
- Zastavuje se při shutdown
- Registrován cleanup přes `atexit`
- Endpoint `/api/status` pro získání stavu

#### D. Frontend Heartbeat Systém

**Soubor:** `frontend/src/services/heartbeat.js`

**Třída HeartbeatManager:**
- **Interval:** 120 sekund
- **State tracking:** running, stopped, inactive, error
- **Browser events:** Reaguje na visibility změny a unload
- **sendBeacon:** Pro spolehlivé odeslání při zavření stránky

**Klíčové metody:**
- `start()`: Spouští heartbeat interval
- `updateHeartbeat()`: Posílá heartbeat na backend
- `getSystemStatus()`: Získává status ze serveru
- `handleVisibilityChange()`: Mění stav při skrytí/zobrazení

**Hook:** `useHeartbeat.js`
- React hook pro lifecycle management
- Automatický start/stop při mount/unmount

#### E. UI Komponenta SystemStatus

**Soubor:** `frontend/src/components/SystemStatus.jsx`

**Funkce:**
- Zobrazuje real-time status systému
- Auto-refresh každých X sekund
- Vizuální indikátory zdraví (ikony, barvy)
- Zobrazuje uptime, heartbeat časy
- Podporuje manuální refresh

#### F. Process Management Services

**1. ProcessManager** (`backend/infrastructure/external/process_manager.py`)
- Low-level správa OS procesů
- Používá `subprocess` a `psutil`
- Start/stop/check procesů podle PID
- Získávání info o CPU, paměti

**2. ProcessService** (`backend/core/services/process_service.py`)
- Business logika pro správu procesů
- Integrace s databází (ProcessRepository)
- Správa procesů per projekt
- Restart, health check funkce

## 2. Identifikované Problémy a Omezení

### 2.1 Architektonické problémy
1. **Duplikace logiky** - správa procesů je rozdělena mezi bash skripty a Python kód
2. **Nekonzistentní state management** - různé komponenty mohou mít různý pohled na stav
3. **Chybí centrální autorita** - není jasné, co je "single source of truth"

### 2.2 Technické problémy
1. **Race conditions** - při současném zápisu do `.app_status.json`
2. **Zombie procesy** - pokud se proces ukončí neočekávaně
3. **Port conflicts** - pevně zadané porty mohou být obsazené
4. **Chybí health checks** - kromě heartbeatu není kontrola funkčnosti

### 2.3 Funkční omezení
1. **Pouze 2 komponenty** - systém je navržen jen pro frontend/backend
2. **Chybí konfigurace** - většina hodnot je hardcoded
3. **Omezené logování** - logy nejsou strukturované ani rotované
4. **Chybí restart politiky** - při pádu se proces nerestartuje

## 3. Doporučení pro Univerzální Řešení

### 3.1 Architektura
```
┌─────────────────────────────────────┐
│         Process Manager API         │
├─────────────────────────────────────┤
│          Core Engine                │
│  ┌──────────┬──────────┬─────────┐ │
│  │ Registry │ Monitor  │ Control │ │
│  └──────────┴──────────┴─────────┘ │
├─────────────────────────────────────┤
│         Storage Layer               │
│  ┌──────────┬──────────┬─────────┐ │
│  │   JSON   │   SQL    │  Redis  │ │
│  └──────────┴──────────┴─────────┘ │
├─────────────────────────────────────┤
│        Process Runners              │
│  ┌──────────┬──────────┬─────────┐ │
│  │  Shell   │  Docker  │ SystemD │ │
│  └──────────┴──────────┴─────────┘ │
└─────────────────────────────────────┘
```

### 3.2 Klíčové komponenty

#### A. Process Registry
- Centrální registr všech spravovaných procesů
- Unikátní ID pro každý proces
- Metadata: typ, config, dependencies, restart policy

#### B. Process Monitor
- Real-time monitoring všech procesů
- Health checks (HTTP, TCP, custom)
- Metriky (CPU, RAM, I/O)
- Alerting při problémech

#### C. Process Controller
- Start/stop/restart operace
- Graceful shutdown s timeouty
- Dependency management
- Rolling updates

#### D. Configuration Management
```yaml
processes:
  frontend:
    type: node
    command: npm start
    workdir: ./frontend
    env:
      NODE_ENV: production
    ports:
      - 3000
    health_check:
      type: http
      path: /health
      interval: 30s
    restart_policy:
      type: always
      max_retries: 3
      
  backend:
    type: python
    command: uvicorn main:app
    workdir: ./backend
    env:
      PYTHONPATH: .
    ports:
      - 8000
    dependencies:
      - database
    health_check:
      type: http
      path: /api/health
```

### 3.3 Implementační strategie

#### Fáze 1: Základní funkčnost
1. Vytvoření Process Manager API
2. Implementace základního registry
3. Jednoduché start/stop operace
4. JSON-based konfigurace

#### Fáze 2: Monitoring
1. Heartbeat systém
2. Health checks
3. Metriky a logování
4. Status dashboard

#### Fáze 3: Pokročilé funkce
1. Dependency management
2. Restart policies
3. Rolling updates
4. Multi-environment support

#### Fáze 4: Integrace
1. Docker support
2. SystemD integrace
3. Kubernetes operator
4. CI/CD pipeline hooks

### 3.4 API Design

```python
class ProcessManager:
    def register_process(self, config: ProcessConfig) -> ProcessID
    def start_process(self, process_id: ProcessID) -> bool
    def stop_process(self, process_id: ProcessID, graceful: bool = True) -> bool
    def restart_process(self, process_id: ProcessID) -> bool
    def get_process_status(self, process_id: ProcessID) -> ProcessStatus
    def list_processes(self, filter: ProcessFilter = None) -> List[ProcessInfo]
    def update_process_config(self, process_id: ProcessID, config: ProcessConfig) -> bool
    def get_process_logs(self, process_id: ProcessID, tail: int = 100) -> List[LogEntry]
    def get_process_metrics(self, process_id: ProcessID) -> ProcessMetrics
```

### 3.5 Výhody navrhovaného řešení

1. **Jednotné rozhraní** - jedna API pro všechny operace
2. **Flexibilita** - podpora různých typů procesů a runnerů
3. **Škálovatelnost** - od jednoduché aplikace po mikroservices
4. **Spolehlivost** - health checks, restart policies, monitoring
5. **Rozšiřitelnost** - plugin systém pro custom funkce
6. **Observability** - centrální logování a metriky

## 4. Migrace ze současného systému

### 4.1 Zachování kompatibility
- Wrapper skripty pro start.sh/stop.sh
- Migrace `.app_status.json` do nového formátu
- Postupná migrace komponent

### 4.2 Minimální narušení
1. Nový systém běží paralelně
2. Postupné přepojování komponent
3. Fallback na starý systém
4. Validace funkčnosti

## 5. Plug & Play Integrace - Minimálně Invazivní Řešení

### 5.1 Koncept "Zero-Touch Integration"

Řešení bude navrženo jako **samostatný modul**, který lze přidat k jakékoliv aplikaci s minimálními změnami:

#### A. Pro Backend (Python/Node.js/Java/Go)
```python
# Jediný řádek pro integraci
from process_manager import ProcessManagerPlugin

# Inicializace při startu aplikace
pm = ProcessManagerPlugin("backend", auto_register=True)
pm.start_monitoring()  # Automaticky začne hlídat aplikaci

# Volitelně: custom health check
@pm.health_check
def check_database():
    return db.is_connected()
```

#### B. Pro Frontend (React/Vue/Angular)
```javascript
// Jediný import
import ProcessManager from '@process-manager/client';

// Auto-inicializace
ProcessManager.init('frontend', {
  autoStart: true,
  dashboard: true  // Zobrazí floating widget
});

// Aplikace běží normálně, PM běží na pozadí
```

### 5.2 Architektura Plug & Play Řešení

```
┌─────────────────────────────────────────────┐
│              Vaše Aplikace                  │
│  ┌────────────────────────────────────────┐ │
│  │   Váš kód (99% nezměněný)              │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │   Process Manager Plugin (1 řádek)     │ │
│  │   ┌──────────┬──────────┬───────────┐ │ │
│  │   │ Monitor  │ Reporter │ Controller│ │ │
│  │   └──────────┴──────────┴───────────┘ │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────┐
│        Process Manager Service              │
│   (Běží samostatně nebo embedded)           │
│  ┌────────────────────────────────────────┐ │
│  │ • REST API / WebSocket                 │ │
│  │ • Web Dashboard                        │ │
│  │ • Process Registry                     │ │
│  │ • Health Monitoring                    │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 5.3 Klíčové Features pro Minimální Invazi

#### 1. **Auto-Discovery**
- PM automaticky detekuje typ aplikace
- Načte si port, název, dependencies
- Nepotřebuje konfiguraci

#### 2. **Standalone nebo Embedded Mode**
```yaml
# process-manager.yml (volitelný)
mode: standalone  # nebo embedded
service:
  port: 9999  # PM dashboard port
  
# Pokud config neexistuje, PM běží embedded
```

#### 3. **Universal Installer**
```bash
# One-liner instalace
curl -sSL https://get.process-manager.io | bash

# Nebo přes package managery
npm install -g @process-manager/cli
pip install process-manager
go get github.com/process-manager/pm
```

#### 4. **Smart Integration Points**

**Python/FastAPI:**
```python
# main.py
from fastapi import FastAPI
from process_manager.fastapi import setup_pm

app = FastAPI()
setup_pm(app)  # Přidá endpoints: /pm/status, /pm/health
```

**Node.js/Express:**
```javascript
const express = require('express');
const { setupPM } = require('@process-manager/express');

const app = express();
setupPM(app);  // Automaticky přidá middleware
```

**React/Next.js:**
```jsx
// _app.js nebo index.js
import { ProcessManagerProvider } from '@process-manager/react';

function App() {
  return (
    <ProcessManagerProvider>
      <YourApp />
    </ProcessManagerProvider>
  );
}
```

### 5.4 Vzorová Aplikace - Process Manager Demo

#### Struktura:
```
process-manager-demo/
├── core/                   # Jádro PM
│   ├── manager.py         # Hlavní engine
│   ├── monitor.py         # Monitoring
│   └── registry.py        # Process registry
├── plugins/               # Integrační pluginy
│   ├── python/           
│   ├── nodejs/           
│   └── frontend/         
├── dashboard/             # Web UI
│   ├── index.html        # Single-page dashboard
│   └── api.js            # API client
├── examples/              # Ukázkové integrace
│   ├── fastapi-app/      
│   ├── express-app/      
│   └── react-app/        
└── install.sh            # Universal installer
```

#### Použití ve vzorové aplikaci:
```bash
# 1. Instalace PM
./install.sh

# 2. Spuštění PM služby
pm start --mode standalone

# 3. Registrace aplikací
pm register ./my-backend --name "API Server"
pm register ./my-frontend --name "Web UI"

# 4. Dashboard běží na http://localhost:9999
```

### 5.5 Minimální Změny v Existujícím Kódu

#### Před:
```python
# main.py
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Po:
```python
# main.py
from process_manager import pm

if __name__ == "__main__":
    pm.wrap(uvicorn.run, app, host="0.0.0.0", port=8000)
    # nebo ještě jednodušeji:
    # pm.run("uvicorn main:app --port 8000")
```

### 5.6 Univerzální CLI

```bash
# Základní příkazy
pm start [app]        # Spustí aplikaci s monitoringem
pm stop [app]         # Zastaví aplikaci
pm restart [app]      # Restartuje aplikaci
pm status            # Zobrazí status všech procesů
pm logs [app]        # Zobrazí logy
pm dashboard         # Otevře web dashboard

# Auto-detekce a start
pm auto .            # Najde a spustí všechny aplikace v adresáři
```

### 5.7 Výhody Tohoto Přístupu

1. **Minimální invaze** - 1-3 řádky kódu
2. **Univerzální** - funguje s jakoukoliv technologií
3. **Okamžitá hodnota** - monitoring hned po instalaci
4. **Postupná adopce** - můžete začít s jednou aplikací
5. **Zero-config** - funguje out-of-the-box
6. **Lightweight** - malý overhead (< 10MB RAM)

## 6. Závěr

Navrhované řešení Process Manageru je koncipováno jako **univerzální, minimálně invazivní nástroj**, který lze přidat k jakékoliv aplikaci pomocí jediného řádku kódu. Kombinuje jednoduchost použití s pokročilými funkcemi monitoringu a správy procesů.

### Prioritní kroky pro implementaci:
1. **Vytvoření Core modulu** - základní funkcionalita (Python)
2. **Implementace pluginů** - pro populární frameworky
3. **Web Dashboard** - jednoduchý HTML/JS interface
4. **CLI nástroj** - univerzální ovládání
5. **Vzorové integrace** - ukázky pro různé technologie

### Klíčové principy:
- **"It just works"** - bez konfigurace
- **Progressive enhancement** - postupné přidávání funkcí
- **Technology agnostic** - nezávislé na technologii
- **Developer friendly** - intuitivní API
- **Production ready** - od začátku stabilní

Toto řešení umožní vývojářům **okamžitě získat přehled** o běžících procesech bez nutnosti přepisovat existující kód nebo měnit architekturu aplikace.