# Architecture

This document provides a comprehensive overview of the Read Receipt system architecture, including component design, data flow, technology decisions, and database schema.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Database Schema](#database-schema)
- [API Architecture](#api-architecture)
- [Security Architecture](#security-architecture)
- [Scalability Considerations](#scalability-considerations)

## System Overview

Read Receipt is a self-hosted email tracking system that enables users to monitor when recipients open their emails. The system consists of three main components:

1. **Browser Extensions** - Chrome and Firefox extensions that automatically inject tracking pixels into outgoing emails
2. **Flask Backend** - RESTful API that handles tracking events, admin operations, and analytics
3. **React Admin Dashboard** - Single-page application for managing recipients and viewing analytics

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Read Receipt System                              │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Chrome     │         │   Firefox    │         │   Future     │
│  Extension   │         │  Extension   │         │  Extensions  │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │  Tracking Pixel        │                        │
       │  Injection             │                        │
       ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Flask Backend API                             │
│                                                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │   Public   │  │    Admin   │  │ Analytics  │  │  Tracking  │     │
│  │  Endpoints │  │    API     │  │   Service  │  │  Handler   │     │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                    Middleware Layer                          │     │
│  │  Authentication │ Logging │ CORS │ Error Handling │ Cache   │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
       │                        │
       │ SQLAlchemy ORM         │ REST API
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  PostgreSQL  │         │   React      │
│  / SQLite    │         │   Dashboard  │
│  Database    │         │   (Vite)     │
└──────────────┘         └──────────────┘
```

## Component Architecture

### Browser Extensions

The browser extensions are responsible for automatically injecting tracking pixels into outgoing emails.

**Components:**
- **Content Script** - Injects tracking pixels into email compose windows
- **Background Service Worker** - Manages extension state and handles browser events
- **Popup UI** - Provides user interface for configuration and status

**Key Features:**
- Automatic detection of email compose windows
- UUID generation for unique tracking
- Configurable tracking server URL
- Toggle tracking on/off

**File Structure:**
```
extensions/
├── chrome/
│   ├── manifest.json      # Extension metadata and permissions
│   ├── background.js      # Service worker
│   ├── content.js         # Content script for pixel injection
│   └── popup.html         # Extension popup UI
└── firefox/
    ├── manifest.json
    ├── background.js
    ├── content.js
    └── popup.html
```

### Flask Backend

The backend is built with Flask and provides a RESTful API for all system operations.

**Components:**
- **Routes** - HTTP endpoint handlers
- **Models** - SQLAlchemy ORM models for database operations
- **Services** - Business logic (future enhancement)
- **Middleware** - Authentication, logging, error handling

**Key Features:**
- Tracking pixel endpoint with no-cache headers
- Admin authentication via token
- Comprehensive analytics endpoints
- Database migrations support

**File Structure:**
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Tool configuration
└── tests/
    └── test_readreceipt.py
```

### React Admin Dashboard

A modern single-page application built with React and Vite for managing the system.

**Components:**
- **Pages** - Dashboard, Recipients, Analytics, Settings, Login
- **API Client** - Axios-based API communication layer
- **Components** - Reusable UI components (future enhancement)

**Key Features:**
- Token-based authentication
- Real-time analytics visualisations
- Recipient management (CRUD operations)
- Data export functionality

**File Structure:**
```
admin-dashboard/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Recipients.jsx
│   │   ├── Analytics.jsx
│   │   ├── Settings.jsx
│   │   └── Login.jsx
│   ├── api/
│   │   └── api.js
│   ├── components/        # (Future)
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```

## Data Flow

### Email Tracking Flow

```
1. User composes email in Gmail
         │
         ▼
2. Extension detects compose window
         │
         ▼
3. Generate unique UUID
         │
         ▼
4. Inject 1x1 tracking pixel into email body
   <img src="https://server/img/{uuid}" width="1" height="1" />
         │
         ▼
5. User sends email to recipient
         │
         ▼
6. Recipient opens email
         │
         ▼
7. Email client requests tracking pixel
         │
         ▼
8. Backend logs tracking event with metadata:
   - Timestamp
   - IP Address (via Cloudflare headers)
   - Country (from IP)
   - User Agent
   - Referrer
         │
         ▼
9. Return 1x1 transparent PNG
         │
         ▼
10. Analytics updated and available in dashboard
```

### Admin Dashboard Flow

```
1. User navigates to admin dashboard
         │
         ▼
2. Login with admin token
         │
         ▼
3. Token stored in localStorage
         │
         ▼
4. API requests include Authorization header
         │
         ▼
5. Backend validates token
         │
         ▼
6. Return requested data (recipients, analytics, etc.)
         │
         ▼
7. Dashboard renders data with visualisations
```

## Technology Stack

### Backend

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **Python 3.11+** | Programming language | Type hints, performance, modern features |
| **Flask** | Web framework | Lightweight, flexible, extensive ecosystem |
| **SQLAlchemy** | ORM | Database abstraction, type safety, migrations |
| **PostgreSQL** | Database (production) | Reliability, performance, advanced features |
| **SQLite** | Database (development) | Zero configuration, file-based |
| **Flask-Migrate** | Database migrations | Alembic-based schema versioning |
| **Pillow** | Image processing | Generate tracking pixel dynamically |
| **ua-parser** | User agent parsing | Identify email clients |
| **SQLAlchemy-Utils** | Enhanced SQLAlchemy types | Country, IP address types |

### Frontend

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **React 18** | UI framework | Component-based, large ecosystem |
| **Vite** | Build tool | Fast HMR, modern bundling |
| **React Router** | Routing | Client-side navigation |
| **Axios** | HTTP client | Interceptors, error handling |
| **Recharts** | Charts | Declarative, React-native |
| **Tailwind CSS** | Styling | Utility-first, rapid development |
| **date-fns** | Date manipulation | Lightweight, modular |

### Browser Extensions

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **Manifest V3** | Extension format | Latest Chrome extension standard |
| **JavaScript (ES6+)** | Programming language | Browser-native, no build step needed |
| **Chrome APIs** | Browser integration | Tabs, storage, runtime APIs |

### DevOps & Infrastructure

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **Docker** | Containerisation | Consistent environments |
| **Helm** | Kubernetes packaging | Standardised K8s deployments |
| **GitHub Actions** | CI/CD | Integrated with repository |
| **pytest** | Testing | Comprehensive Python testing |
| **Ruff** | Linting | Fast Python linter |
| **Black** | Code formatting | Consistent code style |
| **MyPy** | Type checking | Static type analysis |

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────┐
│       Recipients            │
├─────────────────────────────┤
│ PK  recipient_id (INTEGER)  │
│     r_uuid (VARCHAR(36))    │
│     description (VARCHAR)   │
│     email (VARCHAR(100))    │
└─────────────────────────────┘
              │
              │ 1:N
              │
              ▼
┌─────────────────────────────┐
│       Tracking              │
├─────────────────────────────┤
│ PK  tracking_id (INTEGER)   │
│ FK  recipients_id (INTEGER) │
│     timestamp (DATETIME)    │
│     ip_country (VARCHAR)    │
│     connecting_ip (INET)    │
│     user_agent (VARCHAR)    │
│     details (JSON)          │
└─────────────────────────────┘
```

### Recipients Table

Stores information about email recipients being tracked.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `recipient_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `r_uuid` | VARCHAR(36) | NOT NULL | UUID for tracking pixel URL |
| `description` | VARCHAR(200) | NULLABLE | Human-readable description |
| `email` | VARCHAR(100) | NULLABLE | Recipient email address |

**Example:**
```sql
INSERT INTO recipients (r_uuid, description, email)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'John Doe', 'john@example.com');
```

### Tracking Table

Records each time a tracking pixel is loaded.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `tracking_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `recipients_id` | INTEGER | FOREIGN KEY → Recipients | Reference to recipient |
| `timestamp` | DATETIME | NOT NULL | When the email was opened |
| `ip_country` | VARCHAR | NULLABLE | Country from IP address |
| `connecting_ip` | INET | NULLABLE | Client IP address |
| `user_agent` | VARCHAR(255) | NULLABLE | Email client user agent |
| `details` | JSON | NULLABLE | Additional metadata (headers, etc.) |

**Example:**
```sql
INSERT INTO tracking (recipients_id, timestamp, ip_country, connecting_ip, user_agent, details)
VALUES (
  1,
  '2024-01-15 10:30:00',
  'US',
  '192.168.1.1',
  'Mozilla/5.0...',
  '{"referrer": "https://mail.google.com", ...}'
);
```

### Indexes

Recommended indexes for performance:

```sql
-- Speed up tracking lookups by UUID
CREATE INDEX idx_recipients_r_uuid ON recipients(r_uuid);

-- Speed up recipient lookups in tracking
CREATE INDEX idx_tracking_recipients_id ON tracking(recipients_id);

-- Speed up time-based queries
CREATE INDEX idx_tracking_timestamp ON tracking(timestamp);

-- Speed up geographic queries
CREATE INDEX idx_tracking_ip_country ON tracking(ip_country);
```

## API Architecture

### RESTful Design

The API follows RESTful principles:

- **Resources** identified by URLs
- **Standard HTTP methods** (GET, POST, PUT, DELETE)
- **JSON** request and response bodies
- **Stateless** communication
- **Token-based** authentication

### Endpoint Categories

#### Public Endpoints

No authentication required:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint (health check) |
| GET | `/new-uuid` | Generate tracking UUID |
| GET | `/img/<uuid>` | Tracking pixel endpoint |

#### Admin Endpoints

Require `Authorization: Bearer <token>` header:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/login` | Authenticate admin |
| GET | `/api/admin/recipients` | List recipients |
| POST | `/api/admin/recipients` | Create recipient |
| PUT | `/api/admin/recipients/<id>` | Update recipient |
| DELETE | `/api/admin/recipients/<id>` | Delete recipient |
| GET | `/api/admin/stats` | Dashboard statistics |
| GET | `/api/admin/settings` | Get settings |
| PUT | `/api/admin/settings` | Update settings |

#### Analytics Endpoints

Require authentication:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/summary` | Summary statistics |
| GET | `/api/analytics/events` | Time-series data |
| GET | `/api/analytics/recipients` | Top recipients |
| GET | `/api/analytics/geo` | Geographic distribution |
| GET | `/api/analytics/clients` | Email client breakdown |
| GET | `/api/analytics/export` | Export CSV |

### Authentication Flow

```
1. Client sends POST /api/admin/login with token
         │
         ▼
2. Backend validates token against ADMIN_TOKEN env var
         │
         ▼
3. If valid, return { "status": "authenticated" }
         │
         ▼
4. Client stores token in localStorage
         │
         ▼
5. Subsequent requests include Authorization header
         │
         ▼
6. Backend validates token on each request
         │
         ▼
7. If invalid/expired, return 401 Unauthorized
```

## Security Architecture

### Authentication

- **Token-based** authentication for admin endpoints
- **Environment variable** storage for admin token
- **Bearer token** format in Authorization header
- **No session state** maintained on server

### Input Validation

- **Email validation** on recipient creation
- **Type checking** on all input parameters
- **SQL injection prevention** via SQLAlchemy ORM
- **XSS prevention** through proper output escaping

### HTTP Security Headers

- **Cache-Control**: no-store, no-cache on tracking endpoints
- **Pragma**: no-cache
- **Expires**: -1
- **Content-Type**: application/json for API responses

### Extension Security

- **Minimal permissions** (tabs, storage, activeTab)
- **Scoped host permissions** (only required domains)
- **Content Security Policy** compliant
- **No external dependencies**

### Data Protection

- **HTTPS recommended** for production deployments
- **IP address storage** (consider anonymisation for GDPR)
- **User agent logging** (contains browser/device info)
- **Database access controls** (application-level only)

## Scalability Considerations

### Current Limitations

- **Single-threaded** Flask development server
- **No connection pooling** configured by default
- **No caching layer** (Redis, Memcached)
- **No rate limiting** on API endpoints
- **Monolithic** architecture

### Scaling Strategies

#### Horizontal Scaling

- Deploy multiple Flask instances behind a load balancer
- Use PostgreSQL for concurrent connections
- Implement sticky sessions if needed (stateless by design)

#### Database Scaling

- **Read replicas** for analytics queries
- **Connection pooling** (PgBouncer for PostgreSQL)
- **Index optimisation** for common queries
- **Partitioning** for large tracking tables (by date)

#### Caching

- **Redis** for session/cache storage
- **CDN** for static assets (admin dashboard)
- **Browser caching** for static resources

#### Performance Optimisations

- **Async tracking** - Log tracking events asynchronously
- **Batch operations** - Bulk recipient imports
- **Query optimisation** - Use database indexes effectively
- **Compression** - Enable gzip for API responses

### Monitoring & Observability

**Recommended additions:**

- **Prometheus** metrics endpoint
- **Structured logging** (JSON format)
- **Distributed tracing** (Jaeger, Zipkin)
- **Health check** endpoints
- **Alert rules** for errors and latency

---

**Next Steps:**
- [Getting Started Guide](getting-started.md) - Installation and setup
- [API Reference](api-reference.md) - Detailed API documentation
- [Deployment Guide](deployment.md) - Production deployment
