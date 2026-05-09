# Flow 01: User Authentication

## Scope

End-to-end login/register/google flow from UI to JWT-enabled backend session.

## Actors

- User
- ChatPage
- frontend API client
- /api/auth endpoints
- auth credential and user tables

## Step-by-Step Flow (As Implemented)

### A. Register with Email/Password

1. User fills register form in ChatPage.
2. Frontend validates password length and confirmation.
3. Frontend calls POST /api/auth/register.
4. Backend validates @amzur.com domain and uniqueness.
5. Backend hashes password and stores credential.
6. Backend ensures user row exists.
7. Backend returns access_token + user.
8. Frontend redirects user to login screen with success message.

### B. Login with Email/Password

1. User submits login form.
2. Frontend calls POST /api/auth/login.
3. Backend validates domain.
4. Backend verifies bcrypt hash.
5. Backend ensures user row exists.
6. Backend returns token and user.
7. Frontend stores token in localStorage and memory.
8. Frontend loads threads and opens chat screen.

### C. Login with Google

1. User completes Google login widget.
2. Frontend sends credential to POST /api/auth/google.
3. Backend verifies Google token using configured client ID.
4. Backend validates @amzur.com domain.
5. Backend ensures user row exists.
6. Backend issues JWT and returns user.
7. Frontend loads threads and opens chat screen.

## Failure Paths

- Invalid password -> 401 unauthorized.
- Existing account on register -> 409 conflict.
- Missing Google config -> 503 not_configured.
- DB unavailable -> 503 db_error.

## Enhancement Hooks

- Add MFA checkpoint after successful credential validation.
- Add email verification state before issuing full-scope token.
- Add separate auth provider abstraction for SSO expansion.
