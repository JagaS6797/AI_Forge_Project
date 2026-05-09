# Authentication and Authorization

## Scope

Email/password auth, Google auth, JWT creation/validation, and request user resolution.

## Current Implementation

### Supported Login Modes

- Email/password registration and login.
- Google credential login via token verification.
- Access tokens returned as bearer JWT.

### Domain Restriction

- Only @amzur.com emails are allowed.
- Validation is performed server-side for all login modes.

### Password Handling

- Passwords are hashed with bcrypt.
- Verification uses bcrypt check function.

### JWT

- JWT subject is email.
- Expiration uses jwt_expire_minutes config.
- HS256 signing with configured secret_key.

### Request Authentication

1. Extract Authorization header.
2. Validate Bearer format.
3. Decode JWT and resolve email.
4. For development mode only, if no token exists, return placeholder user.
5. In non-development mode with no token, return 401.

## Step-by-Step Flow

### Register

1. Validate amzur email.
2. Check existing credential by email.
3. Hash password and create credential row.
4. Ensure user profile row exists.
5. Return JWT + user object.

### Login

1. Validate amzur email.
2. Load credential row.
3. Verify password hash.
4. Ensure user profile row exists.
5. Return JWT + user object.

### Google Login

1. Verify Google credential token with configured client ID.
2. Extract email claim.
3. Validate amzur email.
4. Ensure user row exists.
5. Return JWT + user object.

## Enhancement Hooks

- Replace dev fallback user with feature-flagged mock auth provider.
- Add refresh token rotation.
- Add account lockout on repeated failed login attempts.
- Add audit trail table for auth events.
