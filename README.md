# 🛡️ ARMMS — Military Asset Request & Mission Management System

> A production-quality, full-stack defense logistics simulator built for educational and portfolio purposes.
> Demonstrates clean architecture, secure authentication, role-based access control, REST API design, and a rich tactical UI.

![Status](https://img.shields.io/badge/Status-Operational-brightgreen?style=flat-square)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-009688?style=flat-square)
![Frontend](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## ⚠️ Disclaimer

This project is a **fictional defense logistics simulator** created purely for **educational and portfolio purposes**.

- ❌ Does **NOT** simulate weapon control, combat operations, targeting, or offensive military capabilities
- ✅ Focuses on asset management, logistics, mission planning, inventory, maintenance, and reporting
- ✅ All data is synthetic/seeded — no real military information is used or implied

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Roles & Permissions](#-roles--permissions)
- [Getting Started](#-getting-started)
- [Demo Credentials](#-demo-credentials)
- [API Documentation](#-api-documentation)
- [Pages & Modules](#-pages--modules)
- [Testing](#-testing)
- [Architecture Decisions](#-architecture-decisions)

---

## ✨ Features

### Core Modules
| Module | Description |
|--------|-------------|
| 🔐 Authentication | JWT-based login with bcrypt password hashing |
| 👥 User Directory | Full CRUD, role assignment, activate/deactivate |
| 🚛 Asset Management | Fleet registry with status tracking and history |
| 🎯 Mission Board | Mission planning with asset-assignment and status tracking |
| 📋 Asset Requests | State machine workflow: Draft → Submitted → Approved/Rejected → Fulfilled |
| ✅ Approvals Hub | Commander/Admin approval queue with comments |
| 🔧 Maintenance Hub | Work orders, scheduling, technician notes |
| 📦 Inventory Supply | Stock tracking, low-stock alerts, supply chain metrics |
| 🔔 Notifications | Real-time alert center with type and read-status filters |
| 📊 Reports & Export | PDF and Excel export for every module with date-range filters |
| 🕵️ Audit Trail | Immutable log of all system actions — Admin only |
| ⚙️ Settings | Platform preferences: notifications, security, display, system |
| 👤 Profile | Edit personal info, change password, activity history |

### Technical Highlights
- **State Machine** — Asset request lifecycle enforced server-side
- **Recommendation Engine** — Rule-based scoring to match assets to missions
- **RBAC** — 5 roles with endpoint-level enforcement via dependency injection
- **Audit Logging** — Every mutating operation is logged automatically
- **Graceful Fallbacks** — Frontend shows demo data if backend is unavailable
- **Auto-seeding** — DB populated with 20 users, 60 assets, 50 missions, 100 requests on first run
- **41 pytest cases** — Covering auth flows, RBAC, state machine, and data integrity

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | REST API framework |
| **SQLAlchemy** | ORM + database abstraction |
| **SQLite** | Development database (easily swappable to PostgreSQL) |
| **Pydantic v2** | Request/response validation and serialization |
| **python-jose** | JWT token signing and verification |
| **passlib + bcrypt** | Password hashing |
| **reportlab** | PDF report generation |
| **openpyxl** | Excel report generation |
| **pytest** | Automated test suite |
| **uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18** | UI component framework |
| **Vite** | Build tool and dev server |
| **Tailwind CSS 3** | Utility-first styling |
| **React Router v6** | Client-side routing |
| **Axios** | HTTP client with JWT interceptors |
| **Recharts** | Dashboard analytics charts |
| **Lucide React** | Icon library |
| **React Hook Form** | Form state management |

---

## 📁 Project Structure

```
military-asset-system/
│
├── backend/
│   ├── main.py                    # App entry, CORS, router assembly
│   ├── requirements.txt           # Python dependencies
│   ├── military_assets.db         # SQLite database (auto-created)
│   ├── venv/                      # Python virtual environment
│   │
│   ├── app/
│   │   ├── api/                   # Route handlers
│   │   │   ├── auth.py            # /auth/login, /auth/me
│   │   │   ├── users.py           # /users/ CRUD
│   │   │   ├── assets.py          # /assets/ CRUD
│   │   │   ├── missions.py        # /missions/ CRUD
│   │   │   ├── requests.py        # /requests/ + state machine
│   │   │   ├── maintenance.py     # /maintenance/ CRUD
│   │   │   ├── inventory.py       # /inventory/ CRUD
│   │   │   ├── notifications.py   # /notifications/ CRUD
│   │   │   ├── reports.py         # /reports/* export endpoints
│   │   │   ├── audit.py           # /audit-logs/ read-only
│   │   │   └── deps.py            # Auth + RBAC dependencies
│   │   │
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── asset.py
│   │   │   ├── mission.py
│   │   │   ├── request.py
│   │   │   ├── maintenance.py
│   │   │   ├── inventory.py
│   │   │   ├── notification.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/               # Pydantic schemas (request/response)
│   │   ├── services/              # Business logic
│   │   │   ├── recommendation.py  # Asset-to-mission scoring engine
│   │   │   └── reports.py         # PDF/Excel generation logic
│   │   │
│   │   ├── core/
│   │   │   ├── config.py          # Environment/app settings
│   │   │   ├── security.py        # JWT, bcrypt helpers
│   │   │   └── database.py        # DB engine + session factory
│   │   │
│   │   └── seed/
│   │       └── seed_data.py       # Demo data generator
│   │
│   └── tests/
│       └── test_suite.py          # 41 automated test cases
│
└── frontend/
    ├── index.html                 # App shell with font imports
    ├── vite.config.js             # Vite config + /api proxy
    ├── tailwind.config.js         # Tailwind + custom defense color palette
    ├── package.json               # NPM dependencies
    │
    └── src/
        ├── main.jsx               # React DOM mount point
        ├── App.jsx                # Router + ProtectedRoute components
        ├── index.css              # Tailwind directives + custom utilities
        │
        ├── context/
        │   └── AuthContext.jsx    # Auth state, login, logout, hasRole()
        │
        ├── services/
        │   └── api.js             # Axios instance + interceptors
        │
        ├── components/
        │   ├── Layout.jsx         # App shell: Sidebar + Navbar + Outlet
        │   ├── Sidebar.jsx        # Role-filtered navigation
        │   └── Navbar.jsx         # Top bar with breadcrumbs
        │
        └── pages/
            ├── Login.jsx          # Tactical login screen
            ├── Dashboard.jsx      # KPI cards + charts
            ├── Assets.jsx         # Asset fleet table
            ├── AssetDetails.jsx   # Individual asset profile
            ├── Missions.jsx       # Mission board
            ├── AssetRequests.jsx  # Request form + workflow
            ├── Approvals.jsx      # Approval queue
            ├── Inventory.jsx      # Supply table
            ├── Maintenance.jsx    # Work orders
            ├── Notifications.jsx  # Alert center
            ├── Reports.jsx        # Export cards
            ├── AuditLogs.jsx      # Audit trail
            ├── Users.jsx          # User management
            ├── Settings.jsx       # System preferences
            └── Profile.jsx        # Personal profile
```

---

## 🔒 Roles & Permissions

| Role | Dashboard | Assets | Missions | Requests | Approvals | Inventory | Maintenance | Reports | Audit | Users |
|------|:---------:|:------:|:--------:|:--------:|:---------:|:---------:|:-----------:|:-------:|:-----:|:-----:|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Commander** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Logistics Officer** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Technician** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Unit Officer** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** (optional)

### 1. Clone or Open the Project

```bash
# If using git
git clone <your-repo-url>
cd military-asset-system

# Or just navigate to the project folder
cd C:\Users\CED-9\.gemini\antigravity\scratch\military-asset-system
```

### 2. Backend Setup

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the backend server (auto-seeds DB on first run)
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

> The database will be automatically created and seeded with demo data on first launch.

### 3. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

### 4. Open the App

| Service | URL |
|---------|-----|
| 🌐 App | http://localhost:3000 |
| ⚙️ API | http://127.0.0.1:8000 |
| 📖 Swagger Docs | http://127.0.0.1:8000/docs |
| 📘 ReDoc | http://127.0.0.1:8000/redoc |

> **Note (Windows):** If `npm` is not recognized in PowerShell, prepend:
> ```powershell
> $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path', 'User')
> ```

---

## 🔑 Demo Credentials

The database is auto-seeded with the following accounts:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@armms.mil` | `admin123` |
| **Commander** | `commander1@armms.mil` | `password123` |
| **Logistics Officer** | `logistics1@armms.mil` | `password123` |
| **Technician** | `tech1@armms.mil` | `password123` |
| **Unit Officer** | `unit1@armms.mil` | `password123` |

---

## 📖 API Documentation

Once the backend is running, interactive Swagger UI is available at:
**http://127.0.0.1:8000/docs**

### Key Endpoints

```
POST   /api/v1/auth/login          # Authenticate and get JWT token
GET    /api/v1/auth/me             # Get current user profile

GET    /api/v1/assets/             # List all assets (with filters)
POST   /api/v1/assets/             # Create new asset (Admin/Logistics)
GET    /api/v1/assets/{id}         # Get single asset
PUT    /api/v1/assets/{id}         # Update asset
DELETE /api/v1/assets/{id}         # Delete asset (Admin)

GET    /api/v1/missions/           # List missions
POST   /api/v1/missions/           # Create mission

GET    /api/v1/requests/           # List asset requests
POST   /api/v1/requests/           # Submit new request
PATCH  /api/v1/requests/{id}/approve  # Approve request (Commander+)
PATCH  /api/v1/requests/{id}/reject   # Reject request (Commander+)

GET    /api/v1/maintenance/        # List maintenance records
GET    /api/v1/inventory/          # List inventory items
GET    /api/v1/notifications/      # Get user notifications
GET    /api/v1/audit-logs/         # View audit trail (Admin only)

GET    /api/v1/reports/assets      # Export asset report (PDF/Excel)
GET    /api/v1/reports/missions    # Export mission report
GET    /api/v1/reports/maintenance # Export maintenance report
GET    /api/v1/reports/inventory   # Export inventory report
```

---

## 🧪 Testing

The backend includes a comprehensive pytest suite with **41 test cases**.

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Run all tests
pytest tests/test_suite.py -v

# Run with coverage report
pytest tests/test_suite.py -v --tb=short
```

### Test Coverage Areas
- ✅ Authentication flows (login, token validation, logout)
- ✅ RBAC enforcement — unauthorized access returns 403
- ✅ Asset CRUD operations
- ✅ Mission CRUD operations
- ✅ Request state machine (all valid and invalid transitions)
- ✅ Approval workflow
- ✅ Audit log generation
- ✅ Data integrity and validation

---

## 🏗 Architecture Decisions

### Why FastAPI?
- Automatic OpenAPI docs generation
- Native async support
- Pydantic integration for validation
- Python type hints as first-class citizens

### Why SQLite (not PostgreSQL)?
- Zero-config for portfolio/demo purposes
- The ORM layer (SQLAlchemy) makes migration to PostgreSQL trivial — just change the `DATABASE_URL` in `core/config.py`

### Why State Machine for Requests?
Asset requests follow a strict lifecycle to enforce military-grade accountability:
```
DRAFT → SUBMITTED → PENDING_REVIEW → APPROVED → FULFILLED
                                   ↘ REJECTED
                                   ↘ CANCELLED
```
Invalid transitions are rejected at the API level.

### Why Graceful Frontend Fallbacks?
Pages display realistic mock data when the backend is unavailable, making the portfolio demo accessible even without a running server.

---

## 📦 requirements.txt (Backend)

```
fastapi==0.110.0
uvicorn[standard]==0.27.1
sqlalchemy==2.0.28
pydantic[email]==2.6.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
reportlab==4.1.0
openpyxl==3.1.2
pytest==8.1.1
httpx==0.27.0
email-validator==2.1.1
```

---

## 🎨 Design System

The UI follows a **tactical dark theme** with:
- **Primary Color**: Emerald (`#10B981`) — operational/active states
- **Warning Color**: Amber (`#F59E0B`) — caution/pending states
- **Danger Color**: Rose (`#F43F5E`) — critical/rejected states
- **Info Color**: Cyan (`#06B6D4`) — informational states
- **Background**: Deep Slate (`#090D16`) — tactical dark
- **Typography**: Inter (UI) + JetBrains Mono (data/codes)
- **Effects**: Glassmorphism panels, glow shadows, micro-animations

---

## 📄 License

This project is licensed under the **MIT License** — free for educational and portfolio use.

---

## 🤝 Contributing

This is a portfolio project. Feel free to fork, adapt, and build on it.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

*Built with ❤️ as a full-stack portfolio demonstration — ARMMS Defense Simulator v1.0*

