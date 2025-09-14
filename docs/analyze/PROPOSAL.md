# 🚀 Roadmapa pro production-ready process manager

## Fáze 1 – Základní jádro (MVP)
🎯 **Cíl**: spustit, zastavit a sledovat procesy stabilně, bez race condition.  
- **Registry**: centrální evidence všech procesů (SQLite nebo Redis → kvůli locking problémům spolehlivější než JSON).  
- **Runner**: implementace subprocess runneru (Python `subprocess`, Node `child_process`).  
- **CLI**: příkazy `pm start <job>`, `pm stop <job>`, `pm status`.  
- **Heartbeat**: každý proces zapisuje stav (čas posledního ticku, exit code, PID).  
- **Monitoring**: jednoduchý HTTP endpoint (`/status` → JSON).  

---

## Fáze 2 – Restart a politika běhu
🎯 **Cíl**: nástroj zvládne běžné produkční problémy.  
- **Restart policy** (on-failure, always, never).  
- **Exponenciální backoff** (např. 1s → 2s → 4s → max 1min).  
- **Max retry count** (ochrana proti restart-loopu).  
- **Graceful shutdown** (SIGTERM, timeout, pak SIGKILL).  

---

## Fáze 3 – Observability & UX
🎯 **Cíl**: vývojář i admin má přehled o tom, co se děje.  
- **Logy**: standardní výstup zachytávat, ukládat do souborů (rotace, např. `logrotate` nebo vestavěná rotace).  
- **Strukturované logy** (JSON/NDJSON → snadno parsovatelné do ELK nebo Grafany).  
- **CLI vylepšení**: barevný výstup, tabulky (např. `pm list` s přehledem všech jobů).  
- **Metrics endpoint**: `/metrics` kompatibilní s Prometheus (CPU, paměť, uptime, počet restartů).  

---

## Fáze 4 – Integrace s frameworky
🎯 **Cíl**: aby vývojář mohl nástroj použít v různých prostředích.  
- **Plugin API**: definice runneru (např. pro FastAPI, Express, React build).  
- **Custom heartbeat**: proces může posílat stav (např. `POST /pm/heartbeat` z frontendu → info o online uživateli).  
- **Env a config**: YAML/JSON konfigurace pro definici jobů.  

---

## Fáze 5 – Dashboard
🎯 **Cíl**: vizualizace a jednoduchá správa přes web.  
- **Frontend SPA** (React/Vue/Svelte): přehled běžících jobů, logy, restart tlačítko.  
- **Realtime update**: WebSocket nebo SSE pro změny stavu.  
- **Role-based access** (admin vs. read-only).  

---

## Fáze 6 – Production grade
🎯 **Cíl**: nasazení v reálném provozu.  
- **Distribuovaný mód** (1 Registry, více Runner agentů na různých serverech).  
- **High availability**: Leader election (pokud Registry padne, jiný převezme).  
- **Security**: autentizace k dashboardu a API (JWT nebo OAuth2).  
- **Backups & audit log**: log každé změny (kdo spustil, kdy se job restartoval).  

---

# 🔑 Shrnutí
- Začít **malým, ale stabilním jádrem** (registry + subprocess + CLI).  
- Postupně přidávat restart policy, monitoring a logy.  
- V další fázi pluginy, heartbeat z aplikací a dashboard.  
- Na konci škálovat na více serverů → distribuovaný orchestrátor.  
