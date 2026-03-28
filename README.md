# TruthLens 🔍

**Real-Time Deepfake & Media Authenticity Detection Platform**

TruthLens is a production-ready platform that detects AI-generated and manipulated videos, images, and audio in real time — before users are deceived.

---

## Architecture

```
truthlens/
├── backend/          # Python 3.11 + FastAPI + PyTorch ML backend
├── extension/        # Chrome Extension (React 18 + Manifest V3)
├── dashboard/        # Web Dashboard (React 18 + TypeScript + Recharts)
└── docker-compose.yml
```

### Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Python 3.11, FastAPI, PyTorch, ONNX Runtime, Redis, PostgreSQL |
| ML Models  | EfficientNet-B4 (video), Wav2Vec 2.0 (audio), CLIP (images) |
| Extension  | React 18, TypeScript, Manifest V3, TailwindCSS, Vite |
| Dashboard  | React 18, TypeScript, Recharts, TailwindCSS, Zustand |
| Auth       | JWT tokens + API key system |
| Deployment | Docker + docker-compose |

---

## Quick Start

### 1. Start all services with Docker

```bash
git clone https://github.com/Rahulchaube1/TruthLens-
cd TruthLens-

# Optional: set secrets
export JWT_SECRET_KEY=your-super-secret-key
export POSTGRES_PASSWORD=your-db-password

docker-compose up --build
```

Services:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### 2. Run backend locally (development)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Run dashboard locally

```bash
cd dashboard
npm install
npm run dev   # http://localhost:3000
```

### 4. Build & install Chrome Extension

```bash
cd extension
npm install
npm run build   # outputs to extension/dist/
```

Then in Chrome:
1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `extension/dist/`

---

## API Reference

### Authentication

```http
POST /api/auth/register
{ "email": "user@example.com", "password": "secret", "name": "Alice" }

POST /api/auth/login
{ "email": "user@example.com", "password": "secret" }

GET /api/auth/apikey
Authorization: Bearer <jwt_token>
```

### Detection Endpoints

#### Video Deepfake Detection
```http
POST /api/detect/video
Authorization: Bearer <token>
{
  "url": "https://example.com/video.mp4",
  "frames": ["<base64_frame>", ...]
}
```
Response:
```json
{
  "is_deepfake": true,
  "confidence": 0.87,
  "frame_scores": [0.82, 0.91, 0.79, ...],
  "detection_time_ms": 342,
  "risk_level": "high"
}
```

#### Audio Voice Clone Detection
```http
POST /api/detect/audio
Authorization: Bearer <token>
{
  "audio_base64": "<base64_audio>",
  "duration_seconds": 12.5
}
```
Response:
```json
{
  "is_cloned": true,
  "confidence": 0.73,
  "voice_artifacts": ["high_spectral_flatness"],
  "synthesis_model_guess": "Tortoise-TTS / VALL-E"
}
```

#### Image AI Generation Detection
```http
POST /api/detect/image
Authorization: Bearer <token>
{
  "image_base64": "<base64_image>",
  "check_metadata": true
}
```
Response:
```json
{
  "is_ai_generated": true,
  "confidence": 0.94,
  "gan_artifacts": true,
  "metadata_inconsistencies": ["No EXIF metadata found"],
  "generator_model_guess": "Stable Diffusion / DALL-E"
}
```

#### Scan History
```http
GET /api/history?limit=50
Authorization: Bearer <token>
```

---

## ML Detection Logic

### Video Deepfake Detection
1. Extract 30 evenly-spaced frames from video (OpenCV)
2. Run each frame through **EfficientNet-B4** fine-tuned on FaceForensics++
3. Detect facial regions using **MTCNN** face detector
4. Aggregate per-frame scores via weighted average
5. Flag as deepfake if >40% of frames score >0.7 confidence

### Audio Voice Clone Detection
1. Resample audio to 16kHz mono
2. Extract **Wav2Vec 2.0** embeddings
3. Check for spectral flatness, prosody anomalies, synthesis artifacts
4. Compare against known TTS/voice-clone model signatures

### Image AI Generation Detection
1. Run through **CLIP-based** authenticity classifier
2. Check for GAN-specific artifacts (checkerboard patterns via FFT)
3. Analyze EXIF metadata for inconsistencies
4. Detect upscaling artifacts and unnatural textures

---

## Chrome Extension

The extension injects content scripts into major social media platforms and automatically flags suspicious media with visual overlays.

**Supported platforms:** YouTube, Twitter/X, Facebook, LinkedIn, Instagram, Reddit, TikTok

**Permissions:** `activeTab`, `scripting`, `storage`, `alarms`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing secret |
| `POSTGRES_PASSWORD` | `changeme` | PostgreSQL password |
| `DATABASE_URL` | — | Full PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `VITE_API_BASE` | `/api` | Dashboard API base URL |

---

## Security

- JWT tokens with 24-hour expiry
- API key authentication for Chrome extension
- Redis-backed sliding-window rate limiting (60 req/min)
- CORS configured (restrict `allow_origins` in production)

---

## License

MIT