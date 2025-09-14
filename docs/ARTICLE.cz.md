# Universal Process Manager: Komplexní technická analýza a implementace

> ⚠️ **Upozornění**: Tento článek popisuje aktuální stav aplikace k datu vytvoření. Implementační detaily a ukázky kódu se mohou v průběhu času měnit s vývojem projektu. Důležité jsou především představené koncepty, architektonické principy a myšlenky, které zůstávají platné bez ohledu na konkrétní implementaci.

## Úvod do problematiky správy procesů

V moderním světě softwarového inženýrství představuje efektivní správa procesů jeden z klíčových pilířů stabilních a škálovatelných systémů. Universal Process Manager, známý také jako Lab Heartbeat, představuje inovativní přístup k řešení této komplexní problematiky. Tento článek poskytuje detailní technickou analýzu použitých technologií, architektonických rozhodnutí a implementačních metod tohoto systému.

Správa procesů není triviální záležitostí. Každý operační systém poskytuje základní nástroje pro spouštění a ukončování procesů, ale v produkčním prostředí potřebujeme mnohem více – monitoring, automatické restartování, health checks, centralizovanou správu logů a především spolehlivost. Universal Process Manager adresuje všechny tyto požadavky elegantním a modulárním způsobem.

## Architektura systému a její filozofie

### Vrstvená architektura

Universal Process Manager je postaven na principu striktního oddělení zodpovědností. Systém se skládá z několika klíčových vrstev, které spolu komunikují prostřednictvím dobře definovaných rozhraní:

**Core vrstva** představuje srdce systému. Obsahuje čtyři hlavní komponenty:
- Registry pro správu metadat procesů
- Controller pro řízení životního cyklu
- Monitor pro sledování stavu procesů
- Heartbeat systém pro real-time monitoring

**CLI vrstva** poskytuje uživatelské rozhraní prostřednictvím příkazové řádky. Využívá framework Click pro elegantní zpracování příkazů a Rich pro formátovaný výstup.

**Perzistentní vrstva** zajišťuje ukládání dat pomocí SQLite databáze, která poskytuje dostatečný výkon pro lokální deployment při zachování jednoduchosti.

### Principy oddělení

Klíčovým architektonickým rozhodnutím bylo kompletní oddělení Process Manageru od spravovaných aplikací. Tento přístup přináší několik zásadních výhod:

1. **Nezávislost aplikací** - Aplikace nemusí být modifikovány pro integraci s Process Managerem
2. **Univerzalita** - Systém podporuje jakýkoliv typ procesu (Python, Node.js, Shell skripty, binární soubory)
3. **Bezpečnost** - Process Manager nemůže poškodit aplikační kód a naopak
4. **Flexibilita** - Snadné přidávání nových typů procesů bez změny existujícího kódu

## Technologický stack a jeho komponenty

### Python jako základ

Python 3.8+ byl zvolen jako primární jazyk z několika důvodů:

**Multiplatformnost** - Python běží spolehlivě na všech hlavních operačních systémech (Linux, macOS, Windows). Díky standardní knihovně subprocess můžeme spouštět procesy jednotným způsobem napříč platformami.

**Bohatý ekosystém** - Využíváme několik klíčových knihoven:
- `psutil` pro pokročilý monitoring procesů (CPU, paměť, síťové spojení)
- `click` pro vytvoření profesionálního CLI rozhraní
- `rich` pro formátovaný a barevný výstup v terminálu
- `requests` pro HTTP health checks
- `flask` pro demonstrační aplikace

**Asynchronní schopnosti** - Ačkoliv hlavní implementace používá threading, Python umožňuje snadný přechod na asyncio pro ještě efektivnější správu velkého počtu procesů.

### SQLite databáze

SQLite představuje ideální volbu pro lokální perzistenci dat:

**Serverless architektura** - Databáze běží přímo v procesu aplikace, což eliminuje nutnost správy dalšího serveru. To zjednodušuje deployment a snižuje systémové nároky.

**ACID compliance** - SQLite garantuje atomicitu, konzistenci, izolaci a trvanlivost transakcí, což je kritické pro spolehlivou správu stavu procesů.

**Výkon** - Pro náš use case (stovky až tisíce procesů) poskytuje SQLite více než dostatečný výkon. Využíváme prepared statements a connection pooling pro optimalizaci.

**Schema databáze** je navrženo pro efektivní ukládání a vyhledávání:
```sql
CREATE TABLE processes (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    config TEXT NOT NULL,  -- JSON serializovaná konfigurace
    state TEXT NOT NULL,
    pid INTEGER,
    started_at TEXT,
    stopped_at TEXT,
    restart_count INTEGER DEFAULT 0,
    last_heartbeat TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_state ON processes(state);
CREATE INDEX idx_name ON processes(name);
CREATE INDEX idx_heartbeat ON processes(last_heartbeat);
```

### Click framework pro CLI

Click představuje moderní přístup k vytváření command-line interfaces:

**Dekorátory** umožňují elegantní definici příkazů:
```python
@click.command()
@click.option('--name', required=True, help='Process name')
@click.option('--type', type=click.Choice(['python', 'nodejs', 'shell']))
def register(name, type):
    """Register a new process"""
    pass
```

**Automatická validace** vstupů šetří mnoho kódu pro kontrolu parametrů.

**Skupiny příkazů** umožňují logickou organizaci funkcionalit.

### Rich pro formátovaný výstup

Rich knihovna transformuje způsob, jakým prezentujeme informace uživateli:

**Tabulky** pro přehledné zobrazení stavu procesů:
```python
table = Table(title="Process Status")
table.add_column("Name", style="cyan")
table.add_column("State", style="green")
table.add_column("CPU %", style="yellow")
table.add_column("Memory MB", style="magenta")
```

**Progress bary** pro sledování dlouhotrvajících operací.

**Syntax highlighting** pro zobrazení logů a konfiguračních souborů.

## Implementace klíčových komponent

### Registry - Centrální evidence procesů

Registry představuje single source of truth pro všechny informace o procesech. Implementace využívá několik návrhových vzorů:

**Singleton pattern** zajišťuje, že existuje pouze jedna instance registry:
```python
class ProcessRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Repository pattern** abstrahuje práci s databází:
```python
def register_process(self, config: ProcessConfig) -> str:
    with self._lock:
        process_id = self._generate_id()
        process_info = ProcessInfo(
            id=process_id,
            config=config,
            state=ProcessState.REGISTERED
        )
        self._save_to_db(process_info)
        return process_id
```

**Thread-safe operace** pomocí RLock (reentrant lock) umožňují bezpečný přístup z více vláken současně.

### Controller - Řízení životního cyklu

Controller implementuje state machine pro správu stavů procesů:

```
REGISTERED -> STARTING -> RUNNING -> STOPPING -> STOPPED
                 |           |           |
                 v           v           v
               FAILED    CRASHED    FAILED
```

**Spouštění procesů** využívá subprocess modul s pokročilou konfigurací:
```python
def start_process(self, process_id: str):
    info = self.registry.get_process(process_id)

    # Příprava prostředí
    env = os.environ.copy()
    env.update(info.config.env)
    env['PM_PROCESS_ID'] = process_id

    # Spuštění procesu
    process = subprocess.Popen(
        info.config.command,
        shell=True,
        cwd=info.config.workdir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid if os.name != 'nt' else None
    )

    # Aktualizace stavu
    self.registry.update_state(
        process_id,
        ProcessState.RUNNING,
        pid=process.pid
    )
```

**Graceful shutdown** implementuje postupné ukončování s timeouty:
1. Poslání SIGTERM signálu
2. Čekání na ukončení (konfigurovatelný timeout)
3. Pokud proces stále běží, poslání SIGKILL
4. Cleanup resources

### Monitor - Sledování zdraví procesů

Monitor běží v samostatném vlákně a kontinuálně sleduje všechny procesy:

**CPU a paměť monitoring** pomocí psutil:
```python
def get_process_metrics(self, pid: int) -> dict:
    try:
        process = psutil.Process(pid)
        return {
            'cpu_percent': process.cpu_percent(interval=1),
            'memory_info': process.memory_info(),
            'num_threads': process.num_threads(),
            'connections': len(process.connections()),
            'open_files': len(process.open_files())
        }
    except psutil.NoSuchProcess:
        return None
```

**Health check implementace** podporuje HTTP endpointy:
```python
def check_health(self, process_info: ProcessInfo) -> bool:
    if not process_info.config.health_check_endpoint:
        return self.is_process_alive(process_info.pid)

    try:
        url = f"http://localhost:{process_info.config.ports[0]}"
        url += process_info.config.health_check_endpoint
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False
```

**Restart politiky** implementují různé strategie:
- `never` - nikdy nerestartovat
- `on-failure` - pouze při selhání (exit code != 0)
- `always` - vždy restartovat (respektuje max_retries)
- `unless-stopped` - restartovat pokud nebyl zastaven manuálně

### Heartbeat systém

Heartbeat systém představuje volitelnou, ale velmi užitečnou funkcionalitu pro real-time monitoring:

**Server komponenta** naslouchá na Unix socket nebo TCP portu:
```python
class HeartbeatServer:
    def __init__(self, socket_path="/tmp/pm_heartbeat.sock"):
        self.socket_path = socket_path
        self.heartbeats = {}
        self._running = False

    def start(self):
        self._running = True
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(5)

        while self._running:
            conn, _ = sock.accept()
            threading.Thread(
                target=self._handle_connection,
                args=(conn,)
            ).start()
```

**Klientská integrace** je jednoduchá a neinvazivní:
```python
# Python aplikace
class ProcessHeartbeatClient:
    def __init__(self, process_id):
        self.process_id = process_id
        self.interval = 10  # sekund
        self._stop_event = threading.Event()

    def start(self):
        def heartbeat_loop():
            while not self._stop_event.is_set():
                self.send_heartbeat()
                self._stop_event.wait(self.interval)

        thread = threading.Thread(target=heartbeat_loop)
        thread.daemon = True
        thread.start()
```

## Pokročilé funkcionality

### Dependency management

Systém podporuje definování závislostí mezi procesy:

```python
def start_with_dependencies(self, process_id: str):
    info = self.registry.get_process(process_id)

    # Rekurzivní spuštění závislostí
    for dep in info.config.dependencies:
        dep_info = self.registry.get_process_by_name(dep)
        if dep_info.state != ProcessState.RUNNING:
            self.start_with_dependencies(dep_info.id)

    # Spuštění hlavního procesu
    self.start_process(process_id)
```

### Log management

Centralizovaná správa logů s rotací:

```python
class LogManager:
    def __init__(self, log_dir="/var/log/process_manager"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_path(self, process_id: str, log_type: str) -> Path:
        return self.log_dir / f"{process_id}.{log_type}.log"

    def rotate_logs(self, max_size_mb=100, max_files=5):
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_size > max_size_mb * 1024 * 1024:
                self._rotate_file(log_file, max_files)
```

### Resource limits

Implementace omezení zdrojů pro procesy:

```python
def apply_resource_limits(self, process_info: ProcessInfo):
    if not process_info.config.resource_limits:
        return

    limits = process_info.config.resource_limits

    # Linux specific - použití cgroups
    if platform.system() == "Linux":
        cgroup_path = f"/sys/fs/cgroup/memory/pm/{process_info.id}"
        os.makedirs(cgroup_path, exist_ok=True)

        # Nastavení limitu paměti
        if 'memory_mb' in limits:
            with open(f"{cgroup_path}/memory.limit_in_bytes", 'w') as f:
                f.write(str(limits['memory_mb'] * 1024 * 1024))

        # Přidání procesu do cgroup
        with open(f"{cgroup_path}/cgroup.procs", 'w') as f:
            f.write(str(process_info.pid))
```

## Bezpečnostní aspekty

### Izolace procesů

Process Manager implementuje několik vrstev izolace:

**Oddělené pracovní adresáře** - každý proces běží ve svém workdir, což zabraňuje konfliktům.

**Environment variable sandboxing** - citlivé proměnné jsou filtrovány:
```python
BLACKLISTED_ENV_VARS = [
    'PM_ADMIN_TOKEN',
    'PM_DATABASE_PASSWORD',
    'PM_ENCRYPTION_KEY'
]

def prepare_environment(self, base_env: dict, process_env: dict) -> dict:
    env = base_env.copy()

    # Odstranění citlivých proměnných
    for var in BLACKLISTED_ENV_VARS:
        env.pop(var, None)

    # Přidání process-specific proměnných
    env.update(process_env)

    return env
```

### Autentizace a autorizace

Pro produkční nasazení je implementován systém oprávnění:

```python
class AuthManager:
    def __init__(self):
        self.tokens = {}
        self.permissions = {}

    def authenticate(self, token: str) -> Optional[str]:
        return self.tokens.get(token)

    def authorize(self, user: str, action: str, resource: str) -> bool:
        user_perms = self.permissions.get(user, [])
        return f"{action}:{resource}" in user_perms
```

### Šifrování citlivých dat

Environment variables a další citlivá data jsou šifrována v databázi:

```python
from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt_config(self, config: dict) -> str:
        json_str = json.dumps(config)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()

    def decrypt_config(self, encrypted: str) -> dict:
        decrypted = self.cipher.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())
```

## Testování a kvalita kódu

### Unit testy

Projekt využívá pytest framework pro comprehensive testing:

```python
import pytest
from unittest.mock import Mock, patch

class TestProcessController:
    @pytest.fixture
    def controller(self):
        registry = Mock()
        return ProcessController(registry)

    def test_start_process_success(self, controller):
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.pid = 12345

            result = controller.start_process('test-id')

            assert result == True
            assert mock_popen.called
```

### Integration testy

Testování interakce mezi komponentami:

```python
def test_full_lifecycle():
    # Setup
    registry = ProcessRegistry(":memory:")
    controller = ProcessController(registry)
    monitor = ProcessMonitor(registry, controller)

    # Register process
    config = ProcessConfig(
        name="test-app",
        command="python -c 'import time; time.sleep(10)'",
        type=ProcessType.PYTHON,
        workdir="/tmp"
    )
    process_id = registry.register(config)

    # Start process
    assert controller.start(process_id)

    # Verify running
    info = registry.get_process(process_id)
    assert info.state == ProcessState.RUNNING

    # Stop process
    assert controller.stop(process_id)

    # Verify stopped
    info = registry.get_process(process_id)
    assert info.state == ProcessState.STOPPED
```

### Performance testy

Měření výkonu kritických operací:

```python
import timeit

def benchmark_registry_operations():
    setup = """
from process_manager.core.registry import ProcessRegistry
registry = ProcessRegistry(":memory:")
    """

    # Test registrace
    register_time = timeit.timeit(
        "registry.register_process(config)",
        setup=setup,
        number=1000
    )
    print(f"1000 registrations: {register_time:.2f}s")

    # Test query
    query_time = timeit.timeit(
        "registry.get_all_processes()",
        setup=setup,
        number=10000
    )
    print(f"10000 queries: {query_time:.2f}s")
```

## Optimalizační techniky

### Connection pooling

Pro efektivní práci s databází:

```python
class DatabasePool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool = queue.Queue(maxsize=pool_size)

        for _ in range(pool_size):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)

    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)
```

### Caching

Implementace LRU cache pro často používaná data:

```python
from functools import lru_cache

class ProcessRegistry:
    @lru_cache(maxsize=128)
    def get_process_by_name(self, name: str) -> Optional[ProcessInfo]:
        with self.db_pool.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM processes WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            return self._row_to_process_info(row) if row else None
```

### Batch operace

Optimalizace hromadných operací:

```python
def update_multiple_states(self, updates: List[Tuple[str, ProcessState]]):
    with self.db_pool.get_connection() as conn:
        conn.executemany(
            "UPDATE processes SET state = ?, updated_at = ? WHERE id = ?",
            [(state.value, datetime.now().isoformat(), pid)
             for pid, state in updates]
        )
        conn.commit()
```

## Rozšiřitelnost a plugin systém

### Plugin architektura

Systém podporuje pluginy pro custom runners:

```python
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register_plugin(self, name: str, plugin_class: type):
        self.plugins[name] = plugin_class

    def get_runner(self, process_type: str) -> ProcessRunner:
        plugin_class = self.plugins.get(process_type, DefaultRunner)
        return plugin_class()

class ProcessRunner(ABC):
    @abstractmethod
    def start(self, config: ProcessConfig) -> subprocess.Popen:
        pass

    @abstractmethod
    def stop(self, process: subprocess.Popen) -> bool:
        pass
```

### Custom runners

Příklad implementace Docker runner:

```python
class DockerRunner(ProcessRunner):
    def start(self, config: ProcessConfig) -> subprocess.Popen:
        docker_cmd = [
            "docker", "run",
            "--name", config.name,
            "--detach"
        ]

        # Přidání environment variables
        for key, value in config.env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # Přidání port mappings
        for port in config.ports:
            docker_cmd.extend(["-p", f"{port}:{port}"])

        # Image name
        docker_cmd.append(config.command)

        return subprocess.Popen(docker_cmd)

    def stop(self, process: subprocess.Popen) -> bool:
        subprocess.run(["docker", "stop", config.name])
        return True
```

## Monitoring a observability

### Metrics collection

Implementace sběru metrik pro Prometheus:

```python
from prometheus_client import Counter, Gauge, Histogram

# Definice metrik
process_starts = Counter(
    'pm_process_starts_total',
    'Total number of process starts',
    ['process_name']
)

process_restarts = Counter(
    'pm_process_restarts_total',
    'Total number of process restarts',
    ['process_name', 'reason']
)

process_uptime = Gauge(
    'pm_process_uptime_seconds',
    'Process uptime in seconds',
    ['process_name']
)

process_memory = Gauge(
    'pm_process_memory_bytes',
    'Process memory usage in bytes',
    ['process_name']
)

class MetricsCollector:
    def collect_metrics(self):
        for process in self.registry.get_all_processes():
            if process.state == ProcessState.RUNNING:
                # Uptime
                uptime = (datetime.now() - process.started_at).total_seconds()
                process_uptime.labels(process.config.name).set(uptime)

                # Memory
                metrics = self.monitor.get_process_metrics(process.pid)
                if metrics:
                    process_memory.labels(process.config.name).set(
                        metrics['memory_info'].rss
                    )
```

### Distributed tracing

Integrace s OpenTelemetry pro distribuované trasování:

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

class ProcessController:
    def start_process(self, process_id: str):
        with tracer.start_as_current_span("start_process") as span:
            span.set_attribute("process.id", process_id)

            try:
                # Start logic
                info = self.registry.get_process(process_id)
                span.set_attribute("process.name", info.config.name)

                # ... start process ...

                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                raise
```

## Praktické use cases

### Mikroslužby

Process Manager exceluje při správě mikroslužeb:

```bash
# Registrace API gateway
./pm register api-gateway --type nodejs \
    --port 3000 \
    --health-check /health \
    --restart-policy always

# Registrace autentizační služby
./pm register auth-service --type python \
    --port 5001 \
    --env "DATABASE_URL=postgresql://..." \
    --dependencies api-gateway

# Registrace služby pro zpracování plateb
./pm register payment-service --type python \
    --port 5002 \
    --env "STRIPE_KEY=..." \
    --dependencies auth-service
```

### Batch processing

Správa batch jobů s časovým plánováním:

```python
class ScheduledJobManager:
    def __init__(self, controller: ProcessController):
        self.controller = controller
        self.scheduler = BackgroundScheduler()

    def schedule_job(self, config: ProcessConfig, cron_expression: str):
        job = self.scheduler.add_job(
            func=lambda: self.controller.start_process_once(config),
            trigger=CronTrigger.from_crontab(cron_expression),
            id=config.name
        )
        return job.id
```

### Development environment

Rychlé nastavení vývojového prostředí:

```bash
# Vytvoření konfiguračního souboru
cat > dev-env.yaml << EOF
processes:
  - name: frontend
    command: npm run dev
    workdir: ./frontend
    port: 3000

  - name: backend
    command: python app.py
    workdir: ./backend
    port: 5000
    env:
      DEBUG: "true"
      DATABASE_URL: "sqlite:///dev.db"

  - name: redis
    command: redis-server
    port: 6379
EOF

# Spuštění celého prostředí
./pm load-config dev-env.yaml
./pm start --all
```

## Budoucí směřování a roadmapa

### Kubernetes integrace

Plánovaná integrace s Kubernetes pro hybrid cloud deployments:

```python
class KubernetesAdapter:
    def __init__(self, kubeconfig_path: str):
        config.load_kube_config(config_file=kubeconfig_path)
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def deploy_as_pod(self, process_config: ProcessConfig):
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=process_config.name),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name=process_config.name,
                        image=process_config.docker_image,
                        env=[
                            client.V1EnvVar(name=k, value=v)
                            for k, v in process_config.env.items()
                        ]
                    )
                ]
            )
        )
        return self.v1.create_namespaced_pod(
            namespace="default",
            body=pod
        )
```

### Machine learning pro prediktivní scaling

Implementace prediktivního scalingu na základě historických dat:

```python
class PredictiveScaler:
    def __init__(self, history_days: int = 30):
        self.history_days = history_days
        self.model = None

    def train_model(self, metrics_history: pd.DataFrame):
        # Příprava features
        features = self._extract_features(metrics_history)

        # Training Random Forest model
        from sklearn.ensemble import RandomForestRegressor
        self.model = RandomForestRegressor(n_estimators=100)
        self.model.fit(
            features[['hour', 'day_of_week', 'cpu_avg', 'memory_avg']],
            features['optimal_instances']
        )

    def predict_scaling_needs(self, current_time: datetime) -> int:
        features = {
            'hour': current_time.hour,
            'day_of_week': current_time.weekday(),
            'cpu_avg': self.get_current_cpu_avg(),
            'memory_avg': self.get_current_memory_avg()
        }
        return int(self.model.predict([list(features.values())])[0])
```

### GraphQL API

Implementace GraphQL API pro pokročilé querying:

```python
import graphene

class ProcessType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    state = graphene.String()
    cpu_percent = graphene.Float()
    memory_mb = graphene.Float()
    uptime_seconds = graphene.Int()

class Query(graphene.ObjectType):
    processes = graphene.List(
        ProcessType,
        state=graphene.String(),
        name_contains=graphene.String()
    )

    def resolve_processes(self, info, state=None, name_contains=None):
        processes = registry.get_all_processes()

        if state:
            processes = [p for p in processes if p.state == state]

        if name_contains:
            processes = [p for p in processes
                        if name_contains in p.config.name]

        return processes

schema = graphene.Schema(query=Query)
```

## Závěr

Universal Process Manager představuje robustní a flexibilní řešení pro správu procesů v moderních aplikacích. Díky promyšlené architektuře, důrazu na oddělení zodpovědností a využití osvědčených technologií poskytuje spolehlivý základ pro správu aplikací různých typů a velikostí.

Klíčové přednosti systému zahrnují:
- Kompletní oddělení od spravovaných aplikací
- Univerzální podporu různých typů procesů
- Robustní monitoring a health checking
- Flexibilní restart politiky
- Rozšiřitelnost pomocí plugin systému
- Výborný výkon díky optimalizacím

Projekt demonstruje best practices v oblasti softwarového inženýrství včetně clean architecture, SOLID principů, comprehensive testingu a důrazu na bezpečnost. Roadmapa projektu ukazuje jasnou vizi dalšího rozvoje směrem k podpoře distribuovaných systémů a cloud-native prostředí.

Universal Process Manager tak představuje nejen praktický nástroj pro každodenní použití, ale také výborný příklad moderního přístupu k návrhu a implementaci systémového software.