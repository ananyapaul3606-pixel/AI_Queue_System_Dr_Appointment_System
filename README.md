# MediQueue — Smart Doctor Booking & Queue Prediction System

A production-ready full-stack application for real-time doctor appointment booking with Redis-powered live queue management and wait-time prediction.

---

## Tech Stack

**Backend:** Python · FastAPI (async) · PostgreSQL · Redis · SQLAlchemy ORM · Pydantic · JWT Auth  
**Frontend:** React 18 · TypeScript · SCSS Modules · Axios · Recharts  
**Infrastructure:** Docker · Docker Compose

---

## Architecture

```
smart-doctor-booking/
├── backend/
│   ├── app/
│   │   ├── api/             # Route handlers (auth, doctors, appointments, queue)
│   │   ├── core/            # Config, security, dependency injection
│   │   ├── db/              # Session, Base declaration
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (auth, doctor, appointment, queue)
│   │   └── main.py          # FastAPI app entry
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/      # Layout, shared UI
│   │   ├── context/         # AuthContext
│   │   ├── pages/           # All page components
│   │   ├── services/        # Axios API client
│   │   └── styles/          # Global SCSS variables
│   ├── package.json
│   ├── Dockerfile
│   └── .env
├── docker-compose.yml
└── README.md
```

---

## Redis Queue Design

```
Key:    queue:doctor:{doctor_id}
Type:   Sorted Set
Score:  Unix timestamp (FIFO ordering)
Value:  appointment_id (string)
```

**Wait Time Formula:**
```
Estimated Wait = Queue Position × Avg Consultation Minutes (per doctor)
```

---

## Quick Start (Docker)

### Prerequisites
- Docker Desktop installed and running

### 1. Clone and start

```bash
git clone <repo-url>
cd smart-doctor-booking
docker-compose up --build
```

### 2. Access the app

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |

---

## Manual Setup (Development)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis locally (or use Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=doctordb postgres:15-alpine
docker run -d -p 6379:6379 redis:7-alpine

# Update .env with local URLs
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/doctordb
# REDIS_URL=redis://localhost:6379

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

# Update .env
# VITE_API_URL=http://localhost:8000

npm run dev
```

---

## API Reference

### Auth
| Method | Endpoint           | Description        |
|--------|--------------------|--------------------|
| POST   | /auth/register     | Register user      |
| POST   | /auth/login        | Login, get token   |

### Doctors
| Method | Endpoint             | Description          |
|--------|----------------------|----------------------|
| GET    | /doctors             | List all doctors     |
| GET    | /doctors/{id}        | Get doctor by ID     |
| POST   | /doctors/profile     | Create doctor profile|
| PATCH  | /doctors/profile     | Update availability  |

### Appointments
| Method | Endpoint                 | Description              |
|--------|--------------------------|--------------------------|
| POST   | /appointments            | Book appointment         |
| GET    | /appointments/my         | Patient's appointments   |
| GET    | /appointments/doctor/all | Doctor's appointments    |
| POST   | /appointments/complete   | Mark as done (Doctor)    |

### Queue
| Method | Endpoint                    | Description            |
|--------|-----------------------------|------------------------|
| GET    | /queue/{doctor_id}          | Get live queue         |
| GET    | /queue/wait-time/{doctor_id}| Get wait time estimate |

---

## Seed Data (Optional)

Register a doctor account, then create a profile via:

```bash
curl -X POST http://localhost:8000/doctors/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "specialization": "Cardiologist",
    "qualification": "MBBS, MD",
    "experience_years": 10,
    "avg_consultation_minutes": 15,
    "consultation_fee": 800,
    "bio": "Senior cardiologist with 10 years of experience."
  }'
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                    | Default                                              |
|-----------------------------|------------------------------------------------------|
| DATABASE_URL                | postgresql+asyncpg://postgres:postgres@db:5432/doctordb |
| REDIS_URL                   | redis://redis:6379                                   |
| SECRET_KEY                  | change-this-in-production                            |
| ALGORITHM                   | HS256                                                |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440                                                 |

### Frontend (`frontend/.env`)

| Variable      | Default                   |
|---------------|---------------------------|
| VITE_API_URL  | http://localhost:8000     |

---

## Key Features

- **JWT Authentication** — stateless, role-based (patient / doctor)
- **Redis Sorted Set Queue** — FIFO ordering by booking timestamp
- **Live queue polling** — frontend auto-refreshes every 8–10 seconds
- **Wait time prediction** — `position × avg_consultation_minutes`
- **Doctor availability toggle** — real-time on/off from dashboard
- **Interactive charts** — Area trend, Bar breakdown, Radial load gauge (Recharts)
- **Clean architecture** — routers → services → models, no logic leaks
- **Async throughout** — full async/await stack (FastAPI + asyncpg + redis-py async)

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a long random string
- [ ] Set `DEBUG=false`
- [ ] Use a managed PostgreSQL (e.g., RDS, Neon)
- [ ] Use a managed Redis (e.g., Upstash, ElastiCache)
- [ ] Add HTTPS via nginx reverse proxy
- [ ] Add rate limiting on auth endpoints
- [ ] Set up Alembic for database migrations
"# AI_Queue_System_Dr_Appointment_System" 
