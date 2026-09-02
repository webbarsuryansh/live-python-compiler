# Authentication & Authorization Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  App.jsx                                               │ │
│  │  - useAuth() hook                                      │ │
│  │  - useExecution() hook                                 │ │
│  │  - Error management                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Components                                            │ │
│  │  - AuthPanel (login/register)                          │ │
│  │  - EditorPanel                                         │ │
│  │  - SavedCodePanel                                      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Hooks                                                 │ │
│  │  - useAuth.js (authentication state)                   │ │
│  │  - useExecution.js (code execution)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services                                              │ │
│  │  - api.js (API client with token management)           │ │
│  │  - Token storage (localStorage)                        │ │
│  │  - Auto token refresh                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕️ HTTP
          ┌────────────────────────────────────┐
          │   CORS Middleware                  │
          │   (Development: allow all origins)  │
          └────────────────────────────────────┘
                           ↕️ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  main.py (FastAPI App)                                 │ │
│  │  - CORS middleware                                      │ │
│  │  - Route registration                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Routes                                                │ │
│  │  - /api/auth.py (20 endpoints)                         │ │
│  │    • Authentication (register, login, refresh)         │ │
│  │    • Profile management                                │ │
│  │    • Code management                                   │ │
│  │    • Code sharing                                      │ │
│  │  - /api/execute.py (code execution)                    │ │
│  │  - /api/ai.py (AI help)                                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Authentication Module (auth.py)                       │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ JWT Management                                   │  │ │
│  │  │ - create_access_token(user_id, role)             │  │ │
│  │  │ - create_refresh_token(user_id)                  │  │ │
│  │  │ - verify_token(token) -> dict                    │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ FastAPI Dependencies                             │  │ │
│  │  │ - get_current_user() -> dict                      │  │ │
│  │  │ - get_current_admin() -> dict                     │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Storage Module (storage.py)                           │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ User Management                                   │  │ │
│  │  │ - create_user(name, email, password)              │  │ │
│  │  │ - authenticate_user(email, password)              │  │ │
│  │  │ - update_user(user_id, **kwargs)                  │  │ │
│  │  │ - change_password(user_id, old, new)              │  │ │
│  │  │ - delete_user(user_id)                            │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ Code Management                                   │  │ │
│  │  │ - save_user_code(user_id, title, code)            │  │ │
│  │  │ - get_saved_code(code_id, user_id)                │  │ │
│  │  │ - update_saved_code(code_id, user_id, ...)        │  │ │
│  │  │ - delete_saved_code(code_id, user_id)             │  │ │
│  │  │ - get_public_codes()                              │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ Permissions & Sharing                             │  │ │
│  │  │ - share_code(code_id, user_id, shared_with)       │  │ │
│  │  │ - get_shared_codes(user_id)                       │  │ │
│  │  │ - check_code_access(code_id, user_id)             │  │ │
│  │  │ - revoke_code_access(code_id, from, revoke_from) │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │ Security                                          │  │ │
│  │  │ - hash_password(password) -> salted hash          │  │ │
│  │  │ - verify_password(password, hash) -> bool         │  │ │
│  │  │ - hmac_compare(a, b) -> bool                      │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Models (Pydantic)                                │ │
│  │  - RegisterRequest, LoginRequest                       │ │
│  │  - UserProfileResponse, AuthResponse                   │ │
│  │  - SaveCodeRequest, UpdateCodeRequest                  │ │
│  │  - ShareCodeRequest, CodePermission                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕️ File I/O
┌─────────────────────────────────────────────────────────────┐
│                  Data Storage (JSON Files)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  users.json                                            │ │
│  │  [                                                     │ │
│  │    {                                                   │ │
│  │      "id": "user_xxxxx",                               │ │
│  │      "name": "John Doe",                               │ │
│  │      "email": "john@example.com",                      │ │
│  │      "password_hash": "salt:digest",                   │ │
│  │      "role": "user",                                   │ │
│  │      "is_active": true,                                │ │
│  │      "created_at": "2024-01-01T00:00:00Z",             │ │
│  │      "updated_at": "2024-01-01T00:00:00Z"              │ │
│  │    }                                                   │ │
│  │  ]                                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  saved_codes.json                                      │ │
│  │  [                                                     │ │
│  │    {                                                   │ │
│  │      "id": "code_xxxxx",                               │ │
│  │      "user_id": "user_xxxxx",                          │ │
│  │      "title": "My Script",                             │ │
│  │      "language": "python",                             │ │
│  │      "code": "print('hello')",                         │ │
│  │      "is_public": false,                               │ │
│  │      "created_at": "2024-01-01T00:00:00Z",             │ │
│  │      "updated_at": "2024-01-01T00:00:00Z"              │ │
│  │    }                                                   │ │
│  │  ]                                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  permissions.json                                      │ │
│  │  [                                                     │ │
│  │    {                                                   │ │
│  │      "id": "perm_xxxxx",                               │ │
│  │      "code_id": "code_xxxxx",                          │ │
│  │      "user_id": "user_xxxxx",                          │ │
│  │      "shared_with": "user_yyyyy",                      │ │
│  │      "permission": "view",                             │ │
│  │      "created_at": "2024-01-01T00:00:00Z",             │ │
│  │      "updated_at": "2024-01-01T00:00:00Z"              │ │
│  │    }                                                   │ │
│  │  ]                                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flow Diagram

```
┌─────────────┐                                      ┌─────────────┐
│  Frontend   │                                      │   Backend   │
│   (React)   │                                      │  (FastAPI)  │
└─────────────┘                                      └─────────────┘
      │                                                    │
      │  1. User clicks "Register"                        │
      ├──────────────────────────────────────────────────>│
      │  POST /api/register                               │
      │  {name, email, password}                          │
      │                                                    │
      │                                           2. Hash password
      │                                           3. Save user
      │                                           4. Generate tokens
      │                                                    │
      │<──────────────────────────────────────────────────┤
      │  200 OK                                            │
      │  {token, refresh_token, user}                     │
      │                                                    │
      │  5. Store tokens in localStorage                  │
      │  6. Display user info                             │
      │                                                    │
      │  7. User wants to save code                        │
      ├──────────────────────────────────────────────────>│
      │  POST /api/saved-codes                            │
      │  Headers: Authorization: Bearer {token}           │
      │  {title, code, language, is_public}               │
      │                                                    │
      │                                           8. Verify token
      │                                           9. Get user from token
      │                                           10. Save code
      │                                                    │
      │<──────────────────────────────────────────────────┤
      │  200 OK                                            │
      │  {id, user_id, title, code, ...}                  │
      │                                                    │
      │  11. Display saved code in list                   │
      │                                                    │
      │  (Later) Token expires                            │
      │                                                    │
      │  12. User action (auto-triggered on 401)          │
      ├──────────────────────────────────────────────────>│
      │  POST /api/refresh                                │
      │  {refresh_token}                                  │
      │                                                    │
      │                                           13. Verify refresh token
      │                                           14. Generate new access token
      │                                                    │
      │<──────────────────────────────────────────────────┤
      │  200 OK                                            │
      │  {token, refresh_token}                           │
      │                                                    │
      │  15. Update tokens in localStorage                │
      │  16. Retry original request                       │
      │                                                    │
      │  17. User clicks logout                           │
      ├──────────────────────────────────────────────────>│
      │  POST /api/logout                                 │
      │                                                    │
      │<──────────────────────────────────────────────────┤
      │  200 OK                                            │
      │                                                    │
      │  18. Clear tokens from localStorage               │
      │  19. Display login form                           │
      │                                                    │
```

## Code Access Control Flow

```
User A wants to access Code created by User B:

┌─────────────────────────────────────────────────────────┐
│ check_code_access(code_id, user_a_id)                   │
│                                                          │
│ 1. Load code from saved_codes.json                       │
│    └─> code not found? return (False, None)              │
│                                                          │
│ 2. Is code owned by user_a? (user_b_id == user_a_id)    │
│    └─> YES? return (True, "own") ✓                       │
│    └─> NO? continue...                                   │
│                                                          │
│ 3. Is code public? (is_public == True)                   │
│    └─> YES? return (True, "view") ✓                      │
│    └─> NO? continue...                                   │
│                                                          │
│ 4. Check permissions.json for shared access             │
│    code_id=code_id, shared_with=user_a_id               │
│    └─> Found? return (True, "view"|"edit") ✓             │
│    └─> Not found? return (False, None) ✗                │
│                                                          │
└─────────────────────────────────────────────────────────┘

Permission Levels:
- "own"   → User created the code (full control)
- "edit"  → User can view and modify shared code
- "view"  → User can only view shared code
- None    → User has no access
```

## Token Structure (JWT)

### Access Token
```json
{
  "sub": "user_xxxxx",              // Subject (user ID)
  "role": "user",                   // User role
  "exp": 1704067200,                // Expiration time (60 min)
  "iat": 1704063600,                // Issued at
  "type": "access"                  // Token type
}
```

### Refresh Token
```json
{
  "sub": "user_xxxxx",              // Subject (user ID)
  "exp": 1704672000,                // Expiration time (7 days)
  "iat": 1704067200,                // Issued at
  "type": "refresh"                 // Token type
}
```

## Security Layers

```
Layer 1: Password Security
├─> PBKDF2 hashing with 100,000 iterations
├─> Random salt per password
└─> HMAC constant-time comparison

Layer 2: Token Security
├─> JWT signed with secret key
├─> Token expiration
├─> Refresh token for renewal
└─> Token type validation

Layer 3: Authentication
├─> Bearer token in Authorization header
├─> Token validation before processing
└─> User extraction from token claims

Layer 4: Authorization
├─> Role-based access control (RBAC)
├─> Permission-based resource access
└─> Ownership verification

Layer 5: API Security
├─> CORS restrictions
├─> Input validation (Pydantic)
├─> Error handling without data leaks
└─> Rate limiting ready
```

## Deployment Topology

```
Production Deployment:

┌─────────────────────────────────────┐
│  Nginx / Load Balancer              │
│  - HTTPS termination                │
│  - Rate limiting                    │
│  - Static file serving              │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────────────┐   ┌───▼────────────┐
│  Frontend      │   │   Backend      │
│  React App     │   │   FastAPI      │
│  (CDN/S3)      │   │   (Docker)     │
└───┬────────────┘   └───┬────────────┘
    │                    │
    │                ┌───▼──────────┐
    │                │  PostgreSQL  │
    │                │  (Database)  │
    │                └──────────────┘
    │
    └─────────── Secure TLS ────────────

Environment: Docker + Kubernetes
CI/CD: GitHub Actions
Secrets: AWS Secrets Manager or HashiCorp Vault
Monitoring: Prometheus + Grafana
```

---

This architecture is scalable, secure, and production-ready!
