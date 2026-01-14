# Rclone Web GUI

Een moderne webinterface voor rclone gebouwd met React/TypeScript frontend en Rust backend. Deze applicatie biedt een gebruiksvriendelijke interface voor het beheren van rclone remotes, bestanden en mounts zonder complexe terminalcommando's te hoeven gebruiken.

## Features

- **File Explorer**: Blader door je rclone remotes met een intuïtieve bestandenverkenner
- **Remote Management**: Bekijk en beheer geconfigureerde remotes
- **Mount Management**: Mount en unmount rclone remotes als lokale drives
- **Real-time Status**: Monitor rclone jobs en mount status
- **Responsive Design**: Werkt op desktop en mobile apparaten

## Architectuur

Het project bestaat uit twee componenten:

### Backend (Rust + Axum)
- **Poort**: 3001
- **Functionaliteit**: API proxy naar rclone RC API
- **Technologieën**: Rust, Axum, Tokio, Reqwest

### Frontend (React + TypeScript)
- **Poort**: 3000
- **Functionaliteit**: Web interface
- **Technologieën**: React, TypeScript, Vite, Mantine UI

## Vereisten

### Voor Docker installatie:
- [Docker](https://docker.com/) en Docker Compose

### Voor handmatige installatie:
- [Rust](https://rustup.rs/) (voor backend)
- [Node.js](https://nodejs.org/) (voor frontend)
- [rclone](https://rclone.org/) met RC server actief

## Installatie

### Optie 1: Docker (Aanbevolen - Alles in 1 container)

1. **Clone het project**:
   ```bash
   git clone <repository-url>
   cd rclone-web-gui
   ```

2. **Optioneel: Configureer environment**:
   ```bash
   cp env.example .env
   # Bewerk .env naar wens
   ```

3. **Build en start alles**:
   ```bash
   # Build de image en start services
   ./build.sh

   # Of handmatig:
   docker-compose up --build -d
   ```

4. **Open je browser** naar `http://localhost:8080`

**Wat draait er in de container:**
- ✅ **rclone RC server** (poort 5572) - Beheert alle rclone operaties
- ✅ **Rust backend API** (poort 3001) - JSON API proxy naar rclone
- ✅ **React frontend** via nginx (poort 80) - Moderne web interface
- ✅ **Supervisor** - Beheert alle processen en herstart bij crashes
- ✅ **Persistent storage** - Rclone config blijft behouden
- ✅ **Health checks** - Automatische monitoring van alle services

### Optie 2: Handmatige installatie

1. **Clone het project**:
   ```bash
   git clone <repository-url>
   cd rclone-web-gui
   ```

2. **Start rclone RC server**:
   ```bash
   rclone rcd --rc-addr=localhost:5572 --rc-user=admin --rc-pass=secret
   ```

3. **Backend opzetten**:
   ```bash
   cd backend
   cargo build --release
   ```

4. **Frontend opzetten**:
   ```bash
   cd ../frontend
   npm install
   ```

## Gebruik

### Docker Commands

```bash
# Start alle services
docker-compose up -d

# Bekijk realtime logs
docker-compose logs -f

# Stop alle services
docker-compose down

# Update naar nieuwste versie
docker-compose pull && docker-compose up --build -d

# Controleer status
docker-compose ps

# Toegang tot container shell
docker-compose exec rclone-web-gui bash
```

**Service URLs:**
- **Web GUI**: http://localhost:8080
- **Backend API**: http://localhost:3001
- **Rclone RC**: http://localhost:5572

### Environment Variables (Docker)

Je kunt de standaard configuratie aanpassen via environment variables in `docker-compose.yml`:

```yaml
environment:
  - RCLONE_RC_USER=your_username
  - RCLONE_RC_PASS=your_password
  - RCLONE_RC_ADDR=localhost:5572
  - FRONTEND_PORT=80
  - BACKEND_PORT=3001
```

### Persistent Data

Rclone configuratie wordt automatisch opgeslagen in een Docker volume:
- **Config bestand**: `/data/rclone.conf`
- **Volume naam**: `rclone-data`

Bekijk de config:
```bash
docker-compose exec rclone-web-gui cat /data/rclone.conf
```

Of mount een lokale directory:
```yaml
volumes:
  - ./my-rclone-config:/data
```

### Handmatig gebruik

1. **Start de backend**:
   ```bash
   cd backend
   cargo run -- --rclone-url http://localhost:5572 --username admin --password secret
   ```

2. **Start de frontend** (in een nieuwe terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open je browser** naar `http://localhost:3000`

## API Endpoints

### Backend API (interne communicatie)

- `GET /api/health` - Health check
- `GET /api/remotes` - Lijst van remotes
- `GET /api/files?fs=<remote>&remote=<path>` - Bestanden in remote
- `GET /api/config` - Config dump
- `GET /api/jobs` - Lopende jobs
- `GET /api/mounts` - Actieve mounts
- `POST /api/mount` - Maak nieuwe mount
- `POST /api/unmount` - Verwijder mount
- `POST /api/copy` - Kopieer bestand
- `POST /api/move` - Verplaats bestand
- `POST /api/delete` - Verwijder bestand
- `POST /api/mkdir` - Maak directory

## Configuratie

### Backend opties

```bash
cargo run -- --help
```

- `--bind`: Bind adres (default: 127.0.0.1:3001)
- `--rclone-url`: Rclone RC server URL (default: http://localhost:5572)
- `--username`: Rclone RC gebruikersnaam
- `--password`: Rclone RC wachtwoord

### Rclone RC Server

Zorg ervoor dat je rclone RC server draait met de juiste configuratie:

```bash
rclone rcd --rc-addr=localhost:5572 --rc-user=admin --rc-pass=secret --rc-allow-origin="*"
```

## Ontwikkeling

### Backend ontwikkelen

```bash
cd backend
cargo watch -x run
```

### Frontend ontwikkelen

```bash
cd frontend
npm run dev
```

### Tests uitvoeren

```bash
# Backend tests
cd backend
cargo test

# Frontend tests
cd frontend
npm test
```

## Rclone RC API Referentie

Dit project gebruikt de [rclone Remote Control API](https://rclone.org/rc/). De belangrijkste endpoints zijn:

- `config/listremotes` - Lijst remotes
- `operations/list` - Lijst bestanden
- `mount/mount` - Mount remote
- `mount/unmount` - Unmount remote
- `operations/copyfile` - Kopieer bestand
- `operations/movefile` - Verplaats bestand
- `operations/deletefile` - Verwijder bestand
- `operations/mkdir` - Maak directory

## Bijdragen

1. Fork het project
2. Maak een feature branch (`git checkout -b feature/nieuwe-feature`)
3. Commit je wijzigingen (`git commit -am 'Voeg nieuwe feature toe'`)
4. Push naar de branch (`git push origin feature/nieuwe-feature`)
5. Maak een Pull Request

## Licentie

MIT License - zie LICENSE bestand voor details.
