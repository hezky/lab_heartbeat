# 🚀 Universal Process Manager

Robustní systém pro správu procesů s automatickým restartováním, monitoringem zdraví a čistým oddělením od spravovaných aplikací.

## ✨ Klíčové vlastnosti

- **Univerzální podpora** - Spravuje Python, Node.js, Shell skripty, Docker kontejnery
- **Nulové závislosti** - Spravované aplikace nevyžadují žádné úpravy
- **Inteligentní monitoring** - CPU, paměť, health checks a podpora heartbeat
- **Automatická obnova** - Konfigurovatelné restart politiky (always, on-failure, never)
- **Čistá architektura** - Kompletní oddělení mezi manažerem a aplikacemi
- **Bohaté CLI** - Krásné terminálové rozhraní s barevným výstupem a tabulkami

## 🚀 Rychlý start

```bash
# Nastavení
./setup.sh

# Registrace Python aplikace
./pm register app.py --name myapp --type python --port 5000

# Spuštění procesu
./pm start myapp

# Zobrazení stavu
./pm status

# Zobrazení logů
./pm logs myapp
```

## 📋 Příkazy

| Příkaz | Popis |
|--------|-------|
| `register` | Registrace nového procesu |
| `unregister` | Odebrání procesu z registru |
| `start` | Spuštění procesu/procesů |
| `stop` | Zastavení procesu/procesů |
| `restart` | Restart procesu |
| `status` | Zobrazení stavu procesů |
| `logs` | Zobrazení logů procesu |
| `list` | Seznam všech procesů |

## 🏗️ Architektura

```
lab_heartbeat/
├── process_manager/      # Hlavní aplikace
│   ├── core/            # Registry, Controller, Monitor, Heartbeat
│   ├── cli/             # CLI rozhraní
│   │   └── commands/    # Modularizované příkazy
│   └── data/            # SQLite databáze
├── sample_apps/         # Ukázkové aplikace
├── docs/                # Dokumentace
└── venv/                # Python virtuální prostředí
```

### Modularizované CLI

CLI je rozděleno podle principů SOLID:
- `cli.py` - Hlavní vstupní bod (54 řádků)
- `utils.py` - Sdílené utility a singleton komponenty
- `commands/process_commands.py` - Příkazy životního cyklu
- `commands/info_commands.py` - Informační příkazy

## 🔧 Restart politiky

- `never` - Žádné automatické restartování
- `on-failure` - Restart při pádu (exit code != 0)
- `always` - Vždy restartovat (respektuje max_retries)
- `unless-stopped` - Restartovat pokud nebyl manuálně zastaven

## 📦 Požadavky

- Python 3.8+
- SQLite3
- Virtuální prostředí (pro Python aplikace)

## 🔐 Bezpečnost

- Databáze je uložena v `process_manager/data/`
- Citlivé environment proměnné jsou filtrovány
- Procesy běží v oddělených pracovních adresářích
- Žádné hardcoded cesty - projekt je plně přenositelný

## 💡 Tipy pro použití

### Registrace s health checks

```bash
./pm register app.py --name myapp \
    --type python \
    --port 5000 \
    --health-check /health \
    --restart-policy on-failure \
    --max-retries 3
```

### Environment proměnné

```bash
./pm register app.py --name myapp \
    --env "DEBUG=true" \
    --env "PORT=8080" \
    --env "DATABASE_URL=postgresql://..."
```

### Hromadné operace

```bash
# Spustit všechny procesy
./pm start --all

# Zastavit všechny běžící procesy
./pm stop --all

# JSON výstup pro automatizaci
./pm status --json
```

## 🔍 Debugging

```bash
# Detailní logy
./pm logs myapp --tail 100

# Vynucené zastavení
./pm stop myapp --force

# Status s metrikami
./pm status
```

## 📈 Budoucí vylepšení

- [ ] Web dashboard pro vizuální správu
- [ ] Distribuovaný mód pro více serverů
- [ ] Docker a Kubernetes integrace
- [ ] Prometheus metriky export
- [ ] Plugin systém pro custom runners

## 📝 Licence

MIT