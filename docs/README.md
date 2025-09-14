# 🚀 Universal Process Manager

Univerzální systém pro správu procesů s důrazem na oddělení funkcionality od aplikací.

## 📋 Přehled

Process Manager je modulární systém pro řízení životního cyklu aplikací s následujícími vlastnostmi:

- **Striktní oddělení** - Funkcionalita Process Manageru je kompletně oddělena od spravovaných aplikací
- **Univerzální podpora** - Podporuje Python, Node.js, Shell skripty a další typy procesů
- **Heartbeat monitoring** - Sledování zdraví procesů v reálném čase
- **Restart politiky** - Automatické restartování procesů podle nastavených pravidel
- **CLI rozhraní** - Jednoduché ovládání přes příkazovou řádku

## 🏗️ Architektura

```
Process Manager
├── core/                   # Jádro systému (oddělené od aplikací)
│   ├── registry.py        # Centrální registr procesů
│   ├── monitor.py         # Monitoring bez zásahu do procesů
│   ├── controller.py      # Řízení životního cyklu
│   └── heartbeat.py       # Heartbeat systém
├── cli/                   # CLI rozhraní
│   └── cli.py            # Příkazy pro ovládání
└── sample_apps/          # Vzorové aplikace (nezávislé)
    ├── python_app/       # Python aplikace
    └── nodejs_app/       # Node.js aplikace
```

### Klíčové principy oddělení:

1. **Registry** - Pouze ukládá metadata, nezasahuje do procesů
2. **Monitor** - Pouze pozoruje, nemění stav procesů
3. **Controller** - Pouze spouští/zastavuje, nemodifikuje aplikace
4. **Heartbeat** - Volitelná integrace, aplikace fungují i bez ní

## 🚀 Rychlý start

### Instalace

```bash
# Instalace závislostí
pip install -r requirements.txt

# Nastavení spustitelnosti CLI
chmod +x pm
```

### Základní použití

```bash
# Registrace Python aplikace
./pm register sample_apps/python_app/app.py \
    --name "python-app" \
    --type python \
    --port 5000 \
    --health-check /health \
    --restart-policy on-failure

# Registrace Node.js aplikace
./pm register sample_apps/nodejs_app/app.js \
    --name "nodejs-app" \
    --type nodejs \
    --port 3000 \
    --health-check /health

# Spuštění procesů
./pm start python-app
./pm start nodejs-app
# nebo všechny najednou
./pm start --all

# Zobrazení stavu
./pm status

# Zobrazení logů
./pm logs python-app --tail 50

# Restart procesu
./pm restart python-app

# Zastavení procesu
./pm stop python-app
# nebo všechny
./pm stop --all
```

## 📊 CLI Příkazy

| Příkaz | Popis | Příklad |
|--------|-------|---------|
| `register` | Registrace nového procesu | `./pm register app.py --name myapp --type python` |
| `unregister` | Odebrání procesu z registru | `./pm unregister myapp` |
| `start` | Spuštění procesu | `./pm start myapp` |
| `stop` | Zastavení procesu | `./pm stop myapp --force` |
| `restart` | Restart procesu | `./pm restart myapp` |
| `status` | Zobrazení stavu všech procesů | `./pm status --json` |
| `list` | Seznam registrovaných procesů | `./pm list` |
| `logs` | Zobrazení logů procesu | `./pm logs myapp --tail 100` |

## 🔧 Konfigurace procesů

### Restart politiky

- `never` - Proces se nikdy nerestartuje
- `on-failure` - Restart pouze při selhání (exit code != 0)
- `always` - Vždy restartovat (do limitu pokusů)
- `unless-stopped` - Restartovat pokud nebyl zastaven manuálně

### Environment proměnné

```bash
./pm register app.py --name myapp \
    --env "DEBUG=true" \
    --env "PORT=8080" \
    --env "DATABASE_URL=postgresql://..."
```

## 🏥 Health Checks a Monitoring

Process Manager automaticky:
- Sleduje CPU a paměť každého procesu
- Kontroluje health check endpointy
- Detekuje crashed procesy
- Sbírá metriky pro monitoring

### Heartbeat integrace (volitelná)

Aplikace mohou volitelně posílat heartbeaty:

```python
# Python
from process_manager.core.heartbeat import ProcessHeartbeatClient
client = ProcessHeartbeatClient(process_id)
client.start()
```

```javascript
// Node.js
// Heartbeat se posílá automaticky pokud je nastavena PM_PROCESS_ID
```

## 📁 Vzorové aplikace

### Python aplikace
- Flask server na portu 5000
- Health check endpoint `/health`
- Simulace background workeru
- Graceful shutdown handling

### Node.js aplikace
- Express server na portu 3000
- Health check endpoint `/health`
- Background worker s náhodnými hodnotami
- Signal handling pro clean shutdown

## 🔍 Monitoring a debugging

```bash
# Detailní status s metrikami
./pm status

# JSON výstup pro parsování
./pm status --json

# Sledování logů v reálném čase
./pm logs myapp --tail 50

# Force kill procesu
./pm stop myapp --force
```

## 🎯 Výhody řešení

1. **Čisté oddělení** - Process Manager nezasahuje do kódu aplikací
2. **Univerzalita** - Funguje s jakýmkoliv typem aplikace
3. **Spolehlivost** - Automatické restartování a monitoring
4. **Jednoduchost** - Intuitivní CLI rozhraní
5. **Rozšiřitelnost** - Modulární architektura umožňuje snadné přidání funkcí

## 📈 Roadmapa

- [ ] Web dashboard pro vizuální správu
- [ ] Distribuovaný mód pro více serverů
- [ ] Docker a Kubernetes integrace
- [ ] Prometheus metriky export
- [ ] Plugin systém pro custom runners

## 📝 License

MIT