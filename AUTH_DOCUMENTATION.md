# Authentication & Authorization System

## Overview

The Live Python Compiler now includes a comprehensive authentication and authorization system with the following features:

### Key Features

1. **JWT-Based Authentication**
   - Access tokens with configurable expiration (default: 60 minutes)
   - Refresh tokens for obtaining new access tokens (default: 7 days)
   - Token verification and validation using PyJWT

2. **User Management**
   - User registration with email and password
   - User login
   - Profile updates (name, email)
   - Password changes
   - Account deletion

3. **Role-Based Access Control (RBAC)**
   - User roles: "user" and "admin"
   - Role validation on protected endpoints
   - Future extensibility for admin features

4. **Code Management & Sharing**
   - Save and organize Python code snippets
   - Public code sharing
   - Private code sharing with specific users
   - Permission levels: "view" and "edit"
   - Code deletion with permission checks

5. **Security Features**
   - PBKDF2-based password hashing with 100,000 iterations
   - HMAC comparison for password verification
   - Bearer token authentication
   - HTTP-only cookie support (can be enabled)
   - CORS configuration

## API Endpoints

### Authentication

#### Register
- **POST** `/api/register`
- **Request:**
  ```json
  {
    "name": "string",
    "email": "string",
    "password": "string (6+ chars)"
  }
  ```
- **Response:**
  ```json
  {
    "token": "JWT access token",
    "refresh_token": "JWT refresh token",
    "user": {
      "id": "string",
      "name": "string",
      "email": "string",
      "role": "user"
    }
  }
  ```

#### Login
- **POST** `/api/login`
- **Request:**
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response:** Same as register

#### Refresh Token
- **POST** `/api/refresh`
- **Request:**
  ```json
  {
    "refresh_token": "JWT refresh token"
  }
  ```
- **Response:** Same as login

#### Get Current User
- **GET** `/api/me`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "id": "string",
    "name": "string",
    "email": "string",
    "role": "user",
    "created_at": "ISO 8601 timestamp",
    "updated_at": "ISO 8601 timestamp"
  }
  ```

#### Logout
- **POST** `/api/logout`
- **Response:** `{ "message": "Successfully logged out" }`

### User Profile

#### Update Profile
- **PUT** `/api/profile`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
  ```json
  {
    "name": "string (optional)",
    "email": "string (optional)"
  }
  ```
- **Response:** Updated user profile

#### Change Password
- **POST** `/api/change-password`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
  ```json
  {
    "old_password": "string",
    "new_password": "string (6+ chars)"
  }
  ```
- **Response:** `{ "message": "Password changed successfully" }`

#### Delete Account
- **DELETE** `/api/account`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** `{ "message": "Account deleted successfully" }`

### Code Management

#### Save Code
- **POST** `/api/saved-codes`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
  ```json
  {
    "title": "string",
    "code": "string",
    "language": "string (default: python)",
    "is_public": "boolean (default: false)"
  }
  ```
- **Response:**
  ```json
  {
    "id": "string",
    "user_id": "string",
    "title": "string",
    "language": "string",
    "code": "string",
    "is_public": "boolean",
    "created_at": "ISO 8601 timestamp",
    "updated_at": "ISO 8601 timestamp"
  }
  ```

#### Get Saved Codes
- **GET** `/api/saved-codes`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** Array of code entries

#### Get Specific Code
- **GET** `/api/saved-codes/{code_id}`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** Single code entry

#### Update Code
- **PUT** `/api/saved-codes/{code_id}`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
  ```json
  {
    "title": "string (optional)",
    "code": "string (optional)",
    "is_public": "boolean (optional)"
  }
  ```
- **Response:** Updated code entry

#### Delete Code
- **DELETE** `/api/saved-codes/{code_id}`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** `{ "message": "Code deleted successfully" }`

#### Get Public Codes
- **GET** `/api/public-codes`
- **Response:** Array of public code entries (no auth required)

### Code Sharing

#### Share Code
- **POST** `/api/saved-codes/{code_id}/share`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
  ```json
  {
    "shared_with_email": "string",
    "permission": "view | edit (default: view)"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Code shared with user@example.com",
    "permission": {
      "id": "string",
      "code_id": "string",
      "user_id": "string",
      "shared_with": "string",
      "permission": "view | edit",
      "created_at": "ISO 8601 timestamp",
      "updated_at": "ISO 8601 timestamp"
    }
  }
  ```

#### Get Shared Codes
- **GET** `/api/shared-codes`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** Array of code entries shared with user

#### Revoke Access
- **DELETE** `/api/saved-codes/{code_id}/share/{user_id}`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:** `{ "message": "Access revoked successfully" }`

#### Check Access
- **GET** `/api/saved-codes/{code_id}/access`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
  ```json
  {
    "has_access": "boolean",
    "permission": "own | view | edit | null"
  }
  ```

## Frontend Integration

### useAuth Hook

The `useAuth()` hook provides authentication state management:

```javascript
import { useAuth } from "./hooks/useAuth";

function MyComponent() {
  const auth = useAuth();
  
  // State
  const { user, token, refreshToken, loading, error, isAuthenticated } = auth;
  
  // Methods
  const { login, register, logout } = auth;
  
  // Usage
  if (auth.isAuthenticated) {
    return <div>Welcome, {auth.user.name}!</div>;
  }
}
```

### API Service

All API functions handle token management automatically:

```javascript
import * as api from "./services/api";

// Auth functions
await api.loginUser({ email, password });
await api.registerUser({ name, email, password });
await api.logoutUser();
await api.getCurrentUser();
await api.refreshAccessToken();

// Profile functions
await api.updateUserProfile({ name, email });
await api.changePassword({ old_password, new_password });
await api.deleteUserAccount();

// Code functions
await api.saveCode({ title, code, language, is_public });
await api.fetchSavedCodes();
await api.getCode(codeId);
await api.updateCode(codeId, { title, code, is_public });
await api.deleteCode(codeId);
await api.getPublicCodes();

// Sharing functions
await api.shareCode(codeId, { shared_with_email, permission });
await api.getSharedCodes();
await api.revokeCodeAccess(codeId, userId);
await api.checkCodeAccess(codeId);
```

## Environment Variables

```env
# Authentication
APP_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Security Considerations

1. **Password Hashing:** Uses PBKDF2 with 100,000 iterations and random salt
2. **Token Expiration:** Access tokens expire after configured period
3. **Refresh Tokens:** Longer-lived tokens for obtaining new access tokens
4. **CORS:** Configure appropriate CORS origins for production
5. **Secret Key:** Use a strong secret key in production (not "dev-...")
6. **HTTPS:** Always use HTTPS in production
7. **Token Storage:** Frontend stores tokens in localStorage (can migrate to secure cookies)

## Database Schema

### Users
```json
{
  "id": "user_xxxxx",
  "name": "User Name",
  "email": "user@example.com",
  "password_hash": "salt:digest",
  "role": "user",
  "is_active": true,
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

### Saved Codes
```json
{
  "id": "code_xxxxx",
  "user_id": "user_xxxxx",
  "title": "Script Title",
  "language": "python",
  "code": "print('hello')",
  "is_public": false,
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

### Permissions
```json
{
  "id": "perm_xxxxx",
  "code_id": "code_xxxxx",
  "user_id": "user_xxxxx",
  "shared_with": "user_yyyyy",
  "permission": "view",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

## Future Enhancements

1. **OAuth Integration:** Support for Google, GitHub login
2. **Two-Factor Authentication:** 2FA support
3. **API Keys:** Generate API keys for programmatic access
4. **Rate Limiting:** Implement rate limiting on auth endpoints
5. **Audit Logging:** Log all authentication events
6. **Email Verification:** Require email verification on registration
7. **Password Reset:** Implement password reset flow
8. **Admin Dashboard:** Admin panel for user management
9. **Team Collaboration:** Teams and team-based code sharing
10. **Activity History:** Track code edit history and sharing events

## Development

### Testing

```bash
# Install dependencies
pip install -r backend/requirements.txt
npm install # in frontend

# Run backend
cd backend && python -m uvicorn app.main:app --reload

# Run frontend
npm run dev # in frontend
```

### Example Usage

```bash
# Register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}'

# Get Current User (replace TOKEN with actual token)
curl -X GET http://localhost:8000/api/me \
  -H "Authorization: Bearer TOKEN"
```
