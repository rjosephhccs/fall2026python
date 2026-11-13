"""Ask Java to verify each token; read only the four permitted user fields."""
import os
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

bearer = HTTPBearer(auto_error=False)
ROLES = {'SUPER_USER', 'INVENTORY_MANAGER', 'PRODUCT_MANAGER'}


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    username: str
    role: str


def unauthorized():
    return HTTPException(
        401, 'Missing, invalid or expired login token.',
        headers={'WWW-Authenticate': 'Bearer'},
    )


def validate_with_java(token: str) -> str:
    base_url = os.getenv('JAVA_AUTH_URL', 'http://localhost:8081').rstrip('/')
    try:
        # Use a short timeout and disable environment proxy settings to avoid
        # Hanging the API if the Java service is down or misconfigured.
        with httpx.Client(timeout=5.0, trust_env=False, follow_redirects=False) as client:
            response = client.post(base_url + '/auth/validate', data={'token': token})
    except httpx.RequestError:
        raise HTTPException(503, 'Java authentication service is unavailable.') from None

    # Current Java implementation may return 500 for an invalid JWT.
    # Never accept an identity from a failed response or decode an unverified JWT.
    if response.status_code != 200:
        raise unauthorized()
    username = response.text
    if not username or len(username) > 50:
        raise unauthorized()
    return username


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or not credentials.credentials or len(credentials.credentials) > 8192:
        raise unauthorized()

    username = validate_with_java(credentials.credentials)
    row = db.execute(text(
        'SELECT user_id, username, role, is_active '
        'FROM public.users WHERE username = :username'
    ), {'username': username}).mappings().first()
    if row is None or not row['is_active']:
        raise unauthorized()
    if row['role'] not in ROLES:
        raise HTTPException(403, 'Unrecognized employee role.')
    return CurrentUser(row['user_id'], row['username'], row['role'])


def require_roles(*allowed_roles: str):
    def check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(403, 'Your role cannot perform this operation.')
        return user
    return check
