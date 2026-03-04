# Glossary

This glossary defines key terms used throughout the Read Receipt documentation.

## Table of Contents

- [Tracking Terms](#tracking-terms)
- [Technical Terms](#technical-terms)
- [Deployment Terms](#deployment-terms)
- [Analytics Terms](#analytics-terms)
- [Extension Terms](#extension-terms)

## Tracking Terms

### Tracking Pixel

A 1x1 pixel transparent image (PNG or GIF) embedded in an email. When the recipient opens the email and images load, the pixel is requested from the server, logging the event.

**Also known as:** Web pixel, email pixel, tracking image

### UUID (Unique Identifier)

A 128-bit number used to uniquely identify tracking pixels. In Read Receipt, UUIDs are generated in the format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

**Example:** `550e8400-e29b-41d4-a716-446655440000`

### Tracking Event

A recorded instance of a recipient opening an email. Each event includes:
- Timestamp
- IP address
- Country (derived from IP)
- User agent (email client)
- Referrer information

### Recipient

An email address that is being tracked. Recipients are stored in the database with:
- UUID for tracking
- Email address
- Description/name

### Open Rate

The percentage of sent emails that are opened by recipients. Calculated as:

```
Open Rate = (Unique Opens / Sent Emails) × 100
```

### Unique Open

An open from a distinct recipient. Different from total opens, as one recipient may open multiple times.

### Total Opens

The total number of times tracking pixels were loaded, including multiple opens by the same recipient.

## Technical Terms

### REST API

A RESTful (Representational State Transfer) API that uses HTTP methods (GET, POST, PUT, DELETE) to interact with resources.

### Flask

A lightweight Python web framework used for the Read Receipt backend. Known for simplicity and flexibility.

### SQLAlchemy

A SQL toolkit and Object-Relational Mapping (ORM) library for Python. Used to interact with the database.

### ORM (Object-Relational Mapping)

A technique that maps database tables to Python classes, allowing database operations using object-oriented patterns.

### Virtual Environment

A self-contained directory containing a Python installation for a particular version of Python, plus a number of additional packages.

### Vite

A modern frontend build tool that provides fast development and optimized production builds for React applications.

### React

A JavaScript library for building user interfaces, particularly single-page applications.

### Node.js

A JavaScript runtime built on Chrome's V8 engine that executes JavaScript code outside a web browser.

### PostgreSQL

An open-source relational database system. Recommended for production deployments of Read Receipt.

### SQLite

A lightweight, file-based database. Used for development and testing in Read Receipt.

### CORS (Cross-Origin Resource Sharing)

A mechanism that allows restricted resources on a web page to be requested from another domain outside the domain from which the first resource was served.

### User Agent

A string that identifies the client software (browser, email client) making a request. Used to detect which email client opened the email.

## Deployment Terms

### Docker

A platform for developing, shipping, and running applications in containers. Containers package code and dependencies for consistent execution.

### Container

A standard unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another.

### Kubernetes (K8s)

An open-source container orchestration engine for automating deployment, scaling, and management of containerised applications.

### Helm

A package manager for Kubernetes. Helm charts define, install, and upgrade Kubernetes applications.

### Helm Chart

A collection of files that describe a related set of Kubernetes resources. Used to deploy Read Receipt to Kubernetes.

### Load Balancer

A device or service that distributes network traffic across multiple servers to improve responsiveness and availability.

### Reverse Proxy

A server that sits in front of web servers and forwards client requests to those web servers. nginx is commonly used as a reverse proxy.

### SSL/TLS

Security protocols that provide encryption for data transmitted between clients and servers. TLS (Transport Layer Security) is the successor to SSL.

### Let's Encrypt

A free, automated, and open certificate authority that provides SSL/TLS certificates.

### CI/CD (Continuous Integration/Continuous Deployment)

A software engineering practice where code changes are automatically tested and deployed. Read Receipt uses GitHub Actions for CI/CD.

### Environment Variables

Dynamic values that can affect the way running processes behave on a computer. Used to configure Read Receipt (e.g., `ADMIN_TOKEN`, `SQLALCHEMY_DATABASE_URI`).

## Analytics Terms

### Time-Series Data

Data points indexed in time order. In Read Receipt, tracking events are stored with timestamps for time-series analysis.

### Geographic Distribution

The breakdown of tracking events by geographic location (country-level). Shows where emails are being opened.

### Email Client Breakdown

The distribution of opens by email client (Gmail, Outlook, Apple Mail, etc.). Helps understand recipient preferences.

### Engagement Rate

A metric measuring how actively recipients interact with emails. High engagement indicates interested recipients.

### Conversion Funnel

The path from email sent → email opened → action taken. Tracking helps optimise each stage.

### Cohort Analysis

Analysis of groups of recipients who share a common characteristic over a time period.

### A/B Testing

Comparing two versions of emails to determine which performs better. Tracking data informs A/B test results.

## Extension Terms

### Browser Extension

A small software module that customises the web browser. Read Receipt has extensions for Chrome and Firefox.

### Content Script

JavaScript code that runs in the context of web pages. The Read Receipt content script injects tracking pixels.

### Background Script (Service Worker)

JavaScript code that runs in the background, independent of web pages. Handles extension state and browser events.

### Manifest File

A JSON file (`manifest.json`) that describes the extension, including its metadata, permissions, and resources.

### Manifest V3

The latest version of the Chrome extension manifest format. Provides improved security and performance.

### Host Permissions

Domains that the extension can access. Read Receipt requests permissions for Gmail, Outlook, and Yahoo domains.

### Popup UI

The user interface that appears when clicking the extension icon. Provides configuration and status.

### MutationObserver

A JavaScript API that watches for changes in the DOM. Used to detect when Gmail compose windows open.

### Chrome APIs

Browser-specific APIs that extensions use. Read Receipt uses: tabs, storage, activeTab, runtime.

## Security Terms

### Token Authentication

Authentication method where clients send a token in the Authorization header. Read Receipt uses bearer tokens.

### Bearer Token

A security token that gives the bearer access to resources. Format: `Authorization: Bearer <token>`

### Input Validation

The process of ensuring input data is correct and secure. Prevents injection attacks and data corruption.

### SQL Injection

A code injection technique that exploits security vulnerabilities in an application's database layer. Prevented by SQLAlchemy ORM.

### XSS (Cross-Site Scripting)

A security vulnerability where attackers inject malicious scripts into web pages. Prevented by proper escaping.

### CSP (Content Security Policy)

A security layer that helps detect and mitigate certain types of attacks, including XSS and data injection.

### HTTPS

Secure HTTP protocol that encrypts data transmitted between client and server. Recommended for production.

### GDPR (General Data Protection Regulation)

EU regulation on data protection and privacy. Read Receipt users should comply with GDPR requirements.

### CCPA (California Consumer Privacy Act)

California state statute intended to enhance privacy rights for California residents.

## Database Terms

### Schema

The structure of a database, describing tables, columns, relationships, and constraints.

### Migration

Version control for databases. Allows schema changes to be applied incrementally.

### Index

A database structure that improves the speed of data retrieval operations. Read Receipt uses indexes for performance.

### Primary Key

A column or set of columns that uniquely identifies each row in a table.

### Foreign Key

A column that references a primary key in another table, establishing a relationship.

### Connection Pooling

A technique that maintains multiple database connections in a pool, improving performance by reusing connections.

### WAL (Write-Ahead Logging)

A method for ensuring data integrity in databases. SQLite WAL mode improves concurrent access.

## Monitoring Terms

### Health Check

An endpoint that reports the health status of an application. Used to verify the service is running.

### Metrics

Quantitative measurements of system performance. Read Receipt can export Prometheus metrics.

### Prometheus

An open-source monitoring and alerting toolkit. Can be integrated with Read Receipt.

### Grafana

An open-source platform for monitoring and observability. Visualises metrics from Prometheus.

### Log Aggregation

Collecting logs from multiple sources into a central location for analysis.

### Alerting

Automated notifications when specific conditions are met (e.g., high error rate, service down).

## Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| **API** | Application Programming Interface |
| **CORS** | Cross-Origin Resource Sharing |
| **CSP** | Content Security Policy |
| **CSS** | Cascading Style Sheets |
| **CSV** | Comma-Separated Values |
| **DOM** | Document Object Model |
| **GDPR** | General Data Protection Regulation |
| **HMR** | Hot Module Replacement |
| **HTML** | Hypertext Markup Language |
| **HTTP** | Hypertext Transfer Protocol |
| **HTTPS** | HTTP Secure |
| **IP** | Internet Protocol |
| **K8s** | Kubernetes |
| **ORM** | Object-Relational Mapping |
| **PNG** | Portable Network Graphics |
| **REST** | Representational State Transfer |
| **SSL** | Secure Sockets Layer |
| **TLS** | Transport Layer Security |
| **UUID** | Unique Identifier |
| **XPI** | Firefox Extension Package |
| **XSS** | Cross-Site Scripting |

---

**Need clarification?** Check this glossary or ask in [GitHub Discussions](https://github.com/yasn77/readreceipt/discussions).
