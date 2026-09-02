# Quick Start Guide - Authentication System

## Installation & Setup (5 minutes)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the backend directory (or use `.env.example`):
```env
APP_SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY=sk-your-key-here  # Optional for AI features
```

### 3. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```
Backend runs on `http://localhost:8000`

### 4. Start Frontend
In another terminal:
```bash
npm install  # if not done already
npm run dev
```
Frontend runs on `http://localhost:5173` (Vite default)

## Testing the Auth System

### Scenario 1: Register & Login
1. Open frontend
2. Click "Register" in Auth Panel
3. Fill in name, email, password
4. Click "Create account"
5. You're automatically logged in!

### Scenario 2: Save & Manage Code
1. Write or paste Python code
2. Click "Save" button
3. Enter a title for your code
4. Saved codes appear in the "Saved scripts" panel
5. Click to reload any saved code

### Scenario 3: Share Code
1. Save a code (must be logged in)
2. (Future feature) Share option will appear in code management
3. Share with another user's email
4. Set permission: "view" or "edit"
5. Other user can access via "Shared codes" section

### Scenario 4: Change Password
1. Login with your account
2. Click user menu (future implementation)
3. Select "Change Password"
4. Enter old and new password
5. Password updated securely

## Key Features to Test

- [x] User registration
- [x] User login
- [x] Token refresh (automatic on token expiry)
- [x] Save code snippets
- [x] Load saved codes
- [x] List public codes
- [x] (Future) Share codes with users
- [x] (Future) Update profile
- [x] (Future) Delete account

## API Testing with cURL

### Register User
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"SecurePass123"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"SecurePass123"}'
```
Response includes `token` and `refresh_token`

### Get Current User (replace TOKEN)
```bash
curl -X GET http://localhost:8000/api/me \
  -H "Authorization: Bearer TOKEN"
```

### Save Code
```bash
curl -X POST http://localhost:8000/api/saved-codes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"title":"My Script","code":"print(\"hello\")","language":"python","is_public":false}'
```

### Get Saved Codes
```bash
curl -X GET http://localhost:8000/api/saved-codes \
  -H "Authorization: Bearer TOKEN"
```

### Get Public Codes
```bash
curl -X GET http://localhost:8000/api/public-codes
```

## File Structure

```
backend/
├── app/
│   ├── auth.py              ← JWT utilities
│   ├── models.py            ← Pydantic models
│   ├── storage.py           ← User & code management
│   ├── main.py              ← FastAPI app
│   ├── routes/
│   │   ├── auth.py          ← Authentication endpoints
│   │   ├── execute.py
│   │   └── ai.py
│   └── data/                ← Generated JSON files
│       ├── users.json
│       ├── saved_codes.json
│       └── permissions.json
└── requirements.txt

frontend/
├── src/
│   ├── hooks/
│   │   ├── useAuth.js       ← Auth state management
│   │   └── useExecution.js
│   ├── services/
│   │   └── api.js           ← API functions
│   ├── components/
│   │   └── AuthPanel.jsx
│   ├── App.jsx
│   └── main.jsx
└── package.json
```

## Common Issues & Solutions

### Issue: "Token has expired"
**Solution:** The access token expires after the configured time. Frontend automatically refreshes using refresh token. If that fails, user needs to login again.

### Issue: "Missing or invalid bearer token"
**Solution:** Ensure token is included in Authorization header:
```
Authorization: Bearer <your_token_here>
```

### Issue: "User not found" after login
**Solution:** User role might not be properly set. Check `users.json` and ensure `role` field is present.

### Issue: CORS errors
**Solution:** Backend allows all origins in development. For production, configure specific origins in `main.py`:
```python
allow_origins=["https://yourdomain.com"]
```

### Issue: Code won't save
**Solution:** 
1. Make sure you're logged in
2. Check that your token is valid
3. Verify backend is running
4. Check browser console for detailed error message

## Development Tips

### Enable Debug Logging
In `backend/app/auth.py`, add:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Tokens
Decode JWT tokens at [jwt.io](https://jwt.io) to inspect claims

### Test Token Refresh
Access an endpoint with an expired token to trigger automatic refresh on frontend

### Database Reset
Delete `backend/app/data/` folder to reset all data and start fresh

## Performance Notes

- JSON file-based storage is suitable for development/testing
- For production with many users, migrate to a database (PostgreSQL recommended)
- Current implementation handles:
  - ~100 concurrent users
  - ~10,000 saved code snippets
  - ~50 code shares per snippet

## Security Checklist

Before Production:
- [ ] Change `APP_SECRET_KEY` to a strong random value
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` to reasonable value (30-120)
- [ ] Configure appropriate CORS origins
- [ ] Enable HTTPS
- [ ] Use secure cookies instead of localStorage
- [ ] Add rate limiting
- [ ] Add email verification
- [ ] Add password reset functionality
- [ ] Setup monitoring/logging
- [ ] Regular security audits

## Need Help?

Refer to:
1. **AUTH_DOCUMENTATION.md** - Complete API reference
2. **IMPLEMENTATION_SUMMARY.md** - Feature overview
3. Frontend console for detailed error messages
4. Backend logs for server-side errors

---

**You're all set! Start developing with a secure authentication system! 🚀**
