# Amzur AI Chat - Backend (Project 3)

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `POST /api/auth/register`
  - Request: `{ "email": "employee@amzur.com", "password": "Password123" }`
  - Response: registered user object

- `POST /api/auth/login`
  - Request: `{ "email": "employee@amzur.com", "password": "Password123" }`
  - Response: `{ "user": ..., "messages": [...], "threads": [...] }`
  - Side effect: sets JWT in httpOnly cookie

- `GET /api/auth/google/login`
  - Redirects to Google OAuth consent page

- `GET /api/auth/google/callback?code=...`
  - Exchanges code for profile, upserts user, sets JWT httpOnly cookie, redirects to frontend

- `POST /api/auth/logout`
  - Clears auth cookie

- `GET /api/auth/me`
  - Returns current authenticated user

- `POST /api/chat`
  - Auth required via cookie
  - Request: `{ "message": "Hello", "thread_id": "optional-uuid" }`
  - Response: `{ "reply": "...", "thread_id": "..." }`
  - Side effect: stores user and assistant messages in PostgreSQL

- `GET /api/chat/messages`
  - Auth required via cookie
  - Optional query: `thread_id`
  - Response: `{ "messages": [...] }`

- `GET /api/threads`
  - Returns all threads for authenticated user

- `POST /api/threads`
  - Creates a new thread

- `PATCH /api/threads/{thread_id}`
  - Updates thread title

- `DELETE /api/threads/{thread_id}`
  - Deletes thread and associated messages

- `GET /health`
  - Response: `{ "status": "ok" }`

## Environment Variables

Required:
- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_EXPIRE_MINUTES`
- `COOKIE_NAME`
- `EMPLOYEE_EMAIL_DOMAIN`
- `FRONTEND_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `LITELLM_PROXY_URL`
- `LITELLM_API_KEY`
- `LLM_MODEL`
