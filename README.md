# Rclone Web GUI (Python)

Een moderne webinterface voor rclone gebouwd met Python FastAPI backend en vanilla JavaScript frontend in één HTML bestand.

## ✨ Features

- **Single HTML File**: Complete webinterface in één bestand - geen complex build proces
- **Python Backend**: Moderne FastAPI server met async support
- **File Explorer**: Blader door je rclone remotes met een intuïtieve interface
- **Remote Management**: Bekijk en beheer geconfigureerde remotes
- **Mount Management**: Create/delete mounts via webinterface
- **Real-time Status**: Monitor rclone jobs en mount status
- **Responsive Design**: Werkt op desktop en mobile apparaten
- **Docker Ready**: Volledig containerized voor eenvoudige deployment

## 🏗️ Architectuur

```
┌─────────────────┐    HTTP     ┌─────────────────┐    HTTP     ┌─────────────────┐
│   Browser       │────────────▶│   FastAPI       │────────────▶│   rclone RC     │
│   (HTML/JS)     │             │   Backend       │             │   Server        │
└─────────────────┘             └─────────────────┘             └─────────────────┘
```

**Componenten:**
- **Frontend**: Vanilla JavaScript + HTML + CSS (single file)
- **Backend**: Python FastAPI met async request handling
- **Storage**: rclone RC API voor alle file operaties
- **Container**: Docker met geïntegreerde rclone

## 🚀 Snel Start (Docker)

1. **Clone en bouw**:
   ```bash
   git clone <repository-url>
   cd rclone-web-gui-python
   ./build.sh
   ```

2. **Start applicatie**:
   ```bash
   docker-compose up -d
   ```

3. **Open browser**: http://localhost:8080

**Klaar!** De applicatie draait nu volledig in Docker containers.

## 📋 Vereisten

### Voor Docker deployment:
- [Docker](https://docker.com/) en Docker Compose
- Minimaal 1GB RAM beschikbaar
- Internet verbinding voor eerste build

### Voor development:
- Python 3.11+
- pip
- rclone (voor lokale testing)

## ⚙️ Configuratie

### Environment Variables

Maak een `.env` bestand (voorbeeld in `env.example`):

```bash
# Rclone instellingen
RCLONE_RC_USER=your_username
RCLONE_RC_PASS=your_password

# Webserver instellingen
HOST=0.0.0.0
PORT=8000
```

### Rclone Configuratie

De rclone configuratie wordt automatisch opgeslagen in Docker volume:
- **Config bestand**: `/data/rclone.conf`
- **Volume naam**: `rclone-data`

**Bestaande config gebruiken**:
```yaml
volumes:
  - /path/to/your/rclone.conf:/data/rclone.conf
```

## 🛠️ Development

### Lokale development:

1. **Start rclone RC server**:
   ```bash
   rclone rcd --rc-addr=localhost:5572 --rc-user=admin --rc-pass=secret
   ```

2. **Installeer dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start de applicatie**:
   ```bash
   python main.py
   ```

4. **Open browser**: http://localhost:8000

### Frontend aanpassen:

De complete frontend zit in `main.py` in de `get_index()` functie. Bewerk de HTML/JavaScript/CSS direct in die functie.

## 📡 API Endpoints

### Health & Status
- `GET /health` - Server health check
- `GET /` - Single-page application

### Remotes
- `GET /api/remotes` - Lijst van remotes
- `GET /api/config` - Config dump

### Files
- `GET /api/files?fs=<remote>&remote=<path>` - Bestanden in remote
- `POST /api/mkdir` - Directory aanmaken
- `POST /api/copy` - Bestand kopiëren
- `POST /api/move` - Bestand verplaatsen
- `POST /api/delete` - Bestand verwijderen

### Mounts
- `GET /api/mounts` - Actieve mounts
- `POST /api/mount` - Mount aanmaken
- `POST /api/unmount` - Mount verwijderen

### Jobs
- `GET /api/jobs` - Lopende jobs

## 🐳 Docker Commands

```bash
# Start alle services
docker-compose up -d

# Bekijk logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild na wijzigingen
docker-compose build --no-cache

# Toegang tot container shell
docker-compose exec rclone-web-gui-python bash

# Update naar nieuwste versie
docker-compose pull && docker-compose up -d
```

## 🔍 Troubleshooting

### Veelvoorkomende problemen:

**"Connection refused" errors:**
```bash
# Controleer of rclone RC container draait
docker-compose ps

# Controleer rclone logs
docker-compose logs rclone-rc
```

**"Permission denied" errors:**
```bash
# Reset Docker volumes
docker-compose down -v
docker-compose up -d
```

**Build failures:**
```bash
# Clean rebuild
docker system prune -f
docker-compose build --no-cache
```

**Port conflicts:**
```yaml
# Wijzig poorten in docker-compose.yml
ports:
  - "8081:8000"  # Wijzig 8080 naar beschikbare poort
```

### Logs bekijken:

```bash
# Alle logs
docker-compose logs -f

# Specifieke service
docker-compose logs -f rclone-web-gui-python
docker-compose logs -f rclone-rc
```

## 🔒 Security

- Gebruik sterke wachtwoorden voor rclone RC
- Beperk netwerk toegang tot Docker containers
- Regular updates van Docker images
- Monitor logs voor verdachte activiteit

## 📊 Monitoring

### Health checks:
- Automatische health checks elke 30 seconden
- Container restart bij failures
- Log rotatie voor opslag efficiency

### Metrics:
- API response tijden
- File operation success rates
- Mount status monitoring

## 🤝 Bijdragen

1. Fork het project
2. Maak een feature branch
3. Test je wijzigingen met Docker
4. Commit je changes
5. Push naar je fork
6. Maak een Pull Request

## 📄 Licentie

MIT License - zie LICENSE bestand voor details.
