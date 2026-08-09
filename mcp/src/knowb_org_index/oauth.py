"""Google desktop OAuth 2.0 with PKCE and macOS Keychain refresh storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen


class OAuthError(RuntimeError):
    """Raised when Google desktop authorization cannot complete safely."""


_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_KEYCHAIN_SERVICE = "knowb-ai.github.io Google Drive OAuth"
_DEFAULT_SCOPES = ("https://www.googleapis.com/auth/drive",)
_CALLBACK_PATH = "/oauth2callback"
_CALLBACK_TIMEOUT_SECONDS = 300


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = _base64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


class _CallbackHandler(BaseHTTPRequestHandler):
    """Capture one OAuth response without logging query parameters."""

    def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP handler API
        parsed = urlsplit(self.path)
        if parsed.path != _CALLBACK_PATH:
            self.send_error(404)
            return
        callback = getattr(self.server, "oauth_callback", None)
        if callback is None:
            callback = {}
            setattr(self.server, "oauth_callback", callback)
        callback.update(parse_qs(parsed.query, keep_blank_values=True))
        body = (
            b"<html><body><h1>KnowB authorization complete</h1>"
            b"<p>You can close this window and return to KnowB.</p></body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: Any) -> None:
        """Do not log OAuth query strings or account details."""


class _KeychainStore:
    """Store one refresh grant in the current macOS user's Keychain."""

    def __init__(self, account_key: str) -> None:
        self.account = account_key

    @staticmethod
    def _require_security() -> None:
        if sys.platform != "darwin" or shutil.which("security") is None:
            raise OAuthError(
                "macOS Keychain storage is required for browser OAuth on this platform"
            )

    def load(self) -> dict[str, Any] | None:
        self._require_security()
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                _KEYCHAIN_SERVICE,
                "-a",
                self.account,
                "-w",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            detail = (result.stderr or "").casefold()
            if "could not be found" in detail or "item not found" in detail:
                return None
            raise OAuthError("Cannot read the KnowB Google OAuth grant from Keychain")
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise OAuthError("Stored KnowB Google OAuth grant is invalid") from exc
        if not isinstance(value, dict) or not isinstance(value.get("refresh_token"), str):
            raise OAuthError("Stored KnowB Google OAuth grant is invalid")
        return value

    def save(self, grant: dict[str, Any]) -> None:
        self._require_security()
        serialized = json.dumps(grant, separators=(",", ":"))
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-U",
                "-s",
                _KEYCHAIN_SERVICE,
                "-a",
                self.account,
                "-w",
                serialized,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            raise OAuthError("Cannot store the KnowB Google OAuth grant in Keychain")

    def delete(self) -> None:
        self._require_security()
        subprocess.run(
            [
                "security",
                "delete-generic-password",
                "-s",
                _KEYCHAIN_SERVICE,
                "-a",
                self.account,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )


class GoogleOAuth:
    """Acquire and refresh Drive credentials without putting tokens in `.env`."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        client_id, client_secret = self._client_credentials()
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = self._scopes()
        account_key = hashlib.sha256(
            f"{self.client_id}|{' '.join(self.scopes)}".encode("utf-8")
        ).hexdigest()[:32]
        self.store = _KeychainStore(account_key)

    @staticmethod
    def _client_credentials() -> tuple[str, str | None]:
        client_id = os.environ.get("KNOWB_GOOGLE_OAUTH_CLIENT_ID", "").strip()
        client_secret = os.environ.get("KNOWB_GOOGLE_OAUTH_CLIENT_SECRET", "").strip() or None
        client_file = os.environ.get("KNOWB_GOOGLE_OAUTH_CLIENT_FILE", "").strip()
        if client_file:
            path = Path(client_file).expanduser().resolve()
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise OAuthError(f"Cannot read Google OAuth client file: {path}") from exc
            if not isinstance(data, dict):
                raise OAuthError("Google OAuth client file must contain an object")
            installed = data.get("installed") or data.get("desktop") or data
            if not isinstance(installed, dict):
                raise OAuthError("Google OAuth client file has no desktop client")
            client_id = client_id or str(installed.get("client_id", "")).strip()
            client_secret = client_secret or str(installed.get("client_secret", "")).strip() or None
        if not client_id:
            raise OAuthError(
                "Configure KNOWB_GOOGLE_OAUTH_CLIENT_ID or "
                "KNOWB_GOOGLE_OAUTH_CLIENT_FILE before browser authorization"
            )
        return client_id, client_secret

    @staticmethod
    def _scopes() -> tuple[str, ...]:
        raw = os.environ.get("KNOWB_GOOGLE_OAUTH_SCOPES", "").strip()
        scopes = tuple(raw.split()) if raw else _DEFAULT_SCOPES
        if not scopes or any(not scope.startswith("https://") for scope in scopes):
            raise OAuthError("KNOWB_GOOGLE_OAUTH_SCOPES must contain HTTPS OAuth scopes")
        return scopes

    def _token_request(self, values: dict[str, str]) -> dict[str, Any]:
        request = Request(
            _TOKEN_ENDPOINT,
            data=urlencode(values).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read(16_384)
        except HTTPError as exc:
            try:
                detail = exc.read(1500).decode("utf-8", errors="replace").strip()
            except OSError:
                detail = ""
            raise OAuthError(f"Google OAuth token exchange failed ({exc.code}): {detail}") from exc
        except (OSError, URLError) as exc:
            raise OAuthError(f"Google OAuth token exchange failed: {exc}") from exc
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OAuthError("Google OAuth token endpoint returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise OAuthError("Google OAuth token endpoint returned an invalid object")
        if result.get("error"):
            raise OAuthError(f"Google OAuth token exchange failed: {result['error']}")
        return result

    def access_token(self) -> str:
        if self._access_token and time.time() < self._access_token_expires_at - 60:
            return self._access_token
        grant = self.store.load()
        if grant is None:
            raise OAuthError(
                "No Google OAuth grant is stored; run `knowb-org design-assets-auth` "
                "to approve access in the browser"
            )
        if grant.get("scope") != " ".join(self.scopes):
            self.store.delete()
            raise OAuthError(
                "Stored Google OAuth grant has different scopes; "
                "run `knowb-org design-assets-auth` again"
            )
        try:
            result = self._token_request(
                {
                    "client_id": self.client_id,
                    "refresh_token": grant["refresh_token"],
                    "grant_type": "refresh_token",
                    **({"client_secret": self.client_secret} if self.client_secret else {}),
                }
            )
        except OAuthError as exc:
            if "invalid_grant" in str(exc):
                self.store.delete()
                raise OAuthError(
                    "Google OAuth grant was invalidated; run `knowb-org design-assets-auth` again"
                ) from exc
            raise
        token = result.get("access_token")
        if not isinstance(token, str) or not token:
            raise OAuthError("Google OAuth response did not include an access token")
        self._access_token = token
        self._access_token_expires_at = time.time() + int(result.get("expires_in", 3600))
        return token

    def authenticate(self) -> dict[str, Any]:
        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(32)
        server = HTTPServer(("127.0.0.1", 0), _CallbackHandler)
        server.timeout = 1
        redirect_uri = f"http://127.0.0.1:{server.server_port}{_CALLBACK_PATH}"
        query = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        authorization_url = f"{_AUTH_ENDPOINT}?{urlencode(query)}"
        browser_opened = webbrowser.open(authorization_url, new=1, autoraise=True)
        callback: dict[str, list[str]] | None = None
        deadline = time.monotonic() + _CALLBACK_TIMEOUT_SECONDS
        try:
            while time.monotonic() < deadline:
                server.handle_request()
                callback = getattr(server, "oauth_callback", None)
                if callback is not None:
                    break
        finally:
            server.server_close()
        if callback is None:
            raise OAuthError("Timed out waiting for Google browser authorization")
        returned_state = callback.get("state", [""])[0]
        if not secrets.compare_digest(returned_state, state):
            raise OAuthError("Google OAuth state validation failed")
        if callback.get("error"):
            raise OAuthError(f"Google authorization was not granted: {callback['error'][0]}")
        code = callback.get("code", [""])[0]
        if not code:
            raise OAuthError("Google authorization callback did not include a code")
        values = {
            "client_id": self.client_id,
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        if self.client_secret:
            values["client_secret"] = self.client_secret
        result = self._token_request(values)
        refresh_token = result.get("refresh_token")
        if not isinstance(refresh_token, str) or not refresh_token:
            raise OAuthError(
                "Google did not return a refresh token; revoke the prior grant and authorize again"
            )
        self.store.save(
            {
                "refresh_token": refresh_token,
                "scope": " ".join(self.scopes),
                "stored_at": int(time.time()),
            }
        )
        access_token = result.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OAuthError("Google OAuth response did not include an access token")
        self._access_token = access_token
        self._access_token_expires_at = time.time() + int(result.get("expires_in", 3600))
        return {
            "status": "authenticated",
            "browser_opened": bool(browser_opened),
            "redirect": "127.0.0.1 loopback",
            "refresh_token_storage": "macOS Keychain",
            "authorization_url": authorization_url if not browser_opened else None,
        }
