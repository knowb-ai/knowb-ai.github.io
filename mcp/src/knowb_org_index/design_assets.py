"""Private Google Drive design-asset vault with identity and ACL gates."""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .index import LocalIndex
from .models import DesignAssetConfig
from .oauth import GoogleOAuth, OAuthError


class DesignAssetError(RuntimeError):
    """Raised when the private design-asset policy cannot be satisfied."""


_DRIVE_API = "https://www.googleapis.com/drive/v3"
_USERINFO_API = "https://www.googleapis.com/oauth2/v3/userinfo"
_FOLDER_MIME = "application/vnd.google-apps.folder"
_MAX_TREE_ITEMS = 2000


class _GoogleDriveClient:
    """Small stdlib-only Drive REST client; tokens never enter tool arguments or logs."""

    def __init__(self, oauth_factory: Callable[[], GoogleOAuth]) -> None:
        self._oauth_factory = oauth_factory

    def _url(self, base: str, params: dict[str, Any] | None = None) -> str:
        if not params:
            return base
        parts = urlsplit(base)
        query = urlencode([(key, value) for key, value in params.items() if value is not None])
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        body: bytes | None = None,
        content_type: str | None = None,
        expect_json: bool = True,
    ) -> Any:
        try:
            token = self._oauth_factory().access_token()
        except OAuthError as exc:
            raise DesignAssetError(str(exc)) from exc
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        request = Request(
            self._url(url, params), data=body, headers=headers, method=method.upper()
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read(20_971_521)
        except HTTPError as exc:
            try:
                detail = exc.read(1500).decode("utf-8", errors="replace").strip()
            except OSError:
                detail = ""
            raise DesignAssetError(
                f"Google Drive request failed ({exc.code}): {detail or exc.reason}"
            ) from exc
        except (OSError, URLError) as exc:
            raise DesignAssetError(f"Google Drive request failed: {exc}") from exc
        if not expect_json:
            return raw
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DesignAssetError("Google Drive returned invalid JSON") from exc

    def userinfo(self) -> dict[str, Any]:
        result = self._request("GET", _USERINFO_API)
        if not isinstance(result, dict):
            raise DesignAssetError("Google userinfo response was not an object")
        return result

    def file(self, file_id: str) -> dict[str, Any]:
        result = self._request(
            "GET",
            f"{_DRIVE_API}/files/{quote(file_id, safe='')}",
            params={
                "supportsAllDrives": "true",
                "fields": "id,name,mimeType,size,modifiedTime,parents,webViewLink,trashed",
            },
        )
        if not isinstance(result, dict):
            raise DesignAssetError("Google Drive file response was not an object")
        return result

    def permissions(self, file_id: str) -> list[dict[str, Any]]:
        result = self._request(
            "GET",
            f"{_DRIVE_API}/files/{quote(file_id, safe='')}/permissions",
            params={
                "supportsAllDrives": "true",
                "fields": "permissions(type,emailAddress,role,domain,allowFileDiscovery)",
                "pageSize": 100,
            },
        )
        permissions = result.get("permissions", []) if isinstance(result, dict) else []
        if not isinstance(permissions, list):
            raise DesignAssetError("Google Drive permissions response was invalid")
        return [item for item in permissions if isinstance(item, dict)]

    def children(self, folder_id: str, page_token: str | None = None) -> dict[str, Any]:
        query = f"'{folder_id}' in parents and trashed = false"
        result = self._request(
            "GET",
            f"{_DRIVE_API}/files",
            params={
                "q": query,
                "spaces": "drive",
                "pageSize": 1000,
                "pageToken": page_token,
                "includeItemsFromAllDrives": "true",
                "supportsAllDrives": "true",
                "fields": (
                    "nextPageToken,files(id,name,mimeType,size,modifiedTime,parents,"
                    "webViewLink,trashed)"
                ),
            },
        )
        if not isinstance(result, dict):
            raise DesignAssetError("Google Drive list response was invalid")
        return result

    def download(self, file_id: str) -> bytes:
        return self._request(
            "GET",
            f"{_DRIVE_API}/files/{quote(file_id, safe='')}",
            params={"alt": "media", "supportsAllDrives": "true"},
            expect_json=False,
        )

    def upload(
        self,
        *,
        folder_id: str,
        name: str,
        mime_type: str,
        content: bytes,
    ) -> dict[str, Any]:
        boundary = f"knowb-{uuid.uuid4().hex}"
        metadata = json.dumps(
            {"name": name, "parents": [folder_id], "mimeType": mime_type},
            separators=(",", ":"),
        ).encode("utf-8")
        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                metadata,
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                f"Content-Type: {mime_type}\r\n\r\n".encode(),
                content,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        result = self._request(
            "POST",
            f"https://www.googleapis.com/upload/drive/v3/files",
            params={
                "uploadType": "multipart",
                "supportsAllDrives": "true",
                "fields": "id,name,mimeType,size,modifiedTime,parents,webViewLink",
            },
            body=body,
            content_type=f"multipart/related; boundary={boundary}",
        )
        if not isinstance(result, dict) or not result.get("id"):
            raise DesignAssetError("Google Drive upload response did not include a file id")
        return result

    def delete(self, file_id: str) -> None:
        self._request(
            "DELETE",
            f"{_DRIVE_API}/files/{quote(file_id, safe='')}",
            params={"supportsAllDrives": "true"},
        )


class DesignAssetOperations:
    """Identity-gated read access and confirmed uploads for one private Drive folder."""

    def __init__(self, config: DesignAssetConfig, index: LocalIndex) -> None:
        self.config = config
        self.index = index
        self.oauth: GoogleOAuth | None = None
        self.drive = _GoogleDriveClient(self._oauth)

    def _oauth(self) -> GoogleOAuth:
        if self.oauth is None:
            self.oauth = GoogleOAuth()
        return self.oauth

    def _enabled(self) -> None:
        if not self.config.enabled:
            raise DesignAssetError(
                "Private design assets are disabled; configure design_assets locally first"
            )

    @staticmethod
    def _github_identity(allowed_logins: tuple[str, ...]) -> str:
        if shutil.which("gh") is None:
            raise DesignAssetError("GitHub CLI (gh) is required for design-asset identity checks")
        child_environment = os.environ.copy()
        for name in (
            "KNOWB_GOOGLE_OAUTH_CLIENT_ID",
            "KNOWB_GOOGLE_OAUTH_CLIENT_SECRET",
            "KNOWB_GOOGLE_OAUTH_CLIENT_FILE",
            "KNOWB_GOOGLE_OAUTH_SCOPES",
        ):
            child_environment.pop(name, None)
        try:
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
                env=child_environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DesignAssetError(f"Cannot verify GitHub identity: {exc}") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise DesignAssetError(f"Cannot verify GitHub identity: {detail[:500]}")
        login = result.stdout.strip().casefold()
        if not login or login not in allowed_logins:
            raise DesignAssetError(
                "Authenticated GitHub login is not allowlisted for design assets"
            )
        return login

    def _google_identity(self) -> str:
        info = self.drive.userinfo()
        email = str(info.get("email", "")).strip().casefold()
        verified = info.get("email_verified", info.get("verified_email", False))
        if not email or email != self.config.allowed_google_email or verified is not True:
            raise DesignAssetError(
                "Authenticated Google account is not the configured verified design-asset account"
            )
        return email

    def authenticate(self) -> dict[str, Any]:
        """Run browser consent, store the refresh grant, and verify the Google account."""

        self._enabled()
        try:
            result = self._oauth().authenticate()
            email = self._google_identity()
        except OAuthError as exc:
            raise DesignAssetError(str(exc)) from exc
        return {
            **result,
            "google_email": email,
            "email_verified": True,
        }

    def _private_permissions(self, file_id: str) -> dict[str, Any]:
        permissions = self.drive.permissions(file_id)
        broad = [
            {
                "type": permission.get("type"),
                "role": permission.get("role"),
                "domain": permission.get("domain"),
            }
            for permission in permissions
            if permission.get("type") in {"anyone", "domain", "group"}
        ]
        if broad:
            raise DesignAssetError(
                "Drive asset is not private to individual Google accounts; "
                f"broad permissions found: {broad}"
            )
        unsupported = [
            permission.get("type")
            for permission in permissions
            if permission.get("type") not in {"user", None}
        ]
        if unsupported:
            raise DesignAssetError("Drive asset has unsupported permission types")
        return {
            "private": True,
            "permission_types": sorted(
                {permission.get("type") for permission in permissions if permission.get("type")}
            ),
        }

    def _verified_context(self) -> dict[str, Any]:
        self._enabled()
        github_login = self._github_identity(self.config.allowed_github_logins)
        google_email = self._google_identity()
        folder = self.drive.file(self.config.google_drive_folder_id)
        if folder.get("mimeType") != _FOLDER_MIME or folder.get("trashed"):
            raise DesignAssetError("Configured Google Drive id is not an active folder")
        privacy = self._private_permissions(self.config.google_drive_folder_id)
        return {
            "github_login": github_login,
            "google_email": google_email,
            "folder": {
                "id": folder.get("id"),
                "name": folder.get("name"),
                "mimeType": folder.get("mimeType"),
            },
            "folder_acl": privacy,
        }

    def verify(self) -> dict[str, Any]:
        """Verify both identities and the configured folder's non-public ACL."""

        context = self._verified_context()
        return {
            "status": "verified",
            "identities": {
                "github_login": context["github_login"],
                "google_email": context["google_email"],
            },
            "folder": context["folder"],
            "folder_acl": context["folder_acl"],
            "public_access": False,
            "note": "File-level ACLs are rechecked before every read and upload.",
        }

    def _walk_assets(
        self,
        folder_id: str,
        prefix: str = "",
        seen: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        seen = seen or set()
        if folder_id in seen:
            raise DesignAssetError("Drive folder graph contains a cycle")
        seen.add(folder_id)
        assets: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            page = self.drive.children(folder_id, page_token)
            for item in page.get("files", []):
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                relative_path = f"{prefix}/{item.get('name', item['id'])}".lstrip("/")
                if item.get("mimeType") == _FOLDER_MIME:
                    assets.extend(self._walk_assets(item["id"], relative_path, seen))
                else:
                    self._private_permissions(item["id"])
                    assets.append(
                        {
                            "id": item["id"],
                            "name": item.get("name"),
                            "path": relative_path,
                            "mimeType": item.get("mimeType"),
                            "size": (
                                int(item["size"])
                                if str(item.get("size", "")).isdigit()
                                else None
                            ),
                            "modifiedTime": item.get("modifiedTime"),
                            "webViewLink": item.get("webViewLink"),
                            "private": True,
                        }
                    )
                if len(assets) > _MAX_TREE_ITEMS:
                    raise DesignAssetError("Design-asset folder exceeds the safe item limit")
            page_token = page.get("nextPageToken")
            if not page_token:
                break
        return assets

    def list_assets(self, *, limit: int = 100) -> dict[str, Any]:
        context = self._verified_context()
        assets = self._walk_assets(self.config.google_drive_folder_id)
        bounded_limit = max(1, min(int(limit), 200))
        return {
            "status": "verified",
            "identities": {
                "github_login": context["github_login"],
                "google_email": context["google_email"],
            },
            "folder": context["folder"],
            "assets": assets[:bounded_limit],
            "total": len(assets),
            "truncated": len(assets) > bounded_limit,
        }

    def _asset(self, file_id: str) -> dict[str, Any]:
        valid_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        if not file_id or any(character not in valid_characters for character in file_id):
            raise DesignAssetError("Invalid Google Drive file id")
        assets = self._walk_assets(self.config.google_drive_folder_id)
        for asset in assets:
            if asset["id"] == file_id:
                return asset
        raise DesignAssetError("File is not inside the configured private design-asset folder")

    def read_asset(self, file_id: str) -> dict[str, Any]:
        context = self._verified_context()
        asset = self._asset(file_id)
        if str(asset.get("mimeType", "")).startswith("application/vnd.google-apps."):
            raise DesignAssetError(
                "Google-native documents must be exported before reading as assets"
            )
        if asset.get("size") is not None and int(asset["size"]) > self.config.max_file_bytes:
            raise DesignAssetError("Design asset exceeds the configured read size limit")
        self._private_permissions(file_id)
        content = self.drive.download(file_id)
        if len(content) > self.config.max_file_bytes:
            raise DesignAssetError("Design asset exceeds the configured read size limit")
        return {
            "status": "verified",
            "identities": {
                "github_login": context["github_login"],
                "google_email": context["google_email"],
            },
            "asset": asset,
            "mimeType": asset.get("mimeType") or "application/octet-stream",
            "bytes": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }

    def _local_upload(self, local_path: str, display_name: str | None = None) -> dict[str, Any]:
        raw_path = Path(local_path).expanduser()
        if raw_path.is_symlink():
            raise DesignAssetError("Upload source must be a real local file")
        path = raw_path.resolve()
        if not path.is_file():
            raise DesignAssetError("Upload source must be a real local file")
        if not any(path.is_relative_to(root) for root in self.config.allowed_upload_roots):
            raise DesignAssetError("Upload source is outside allowed_upload_roots")
        name = display_name.strip() if display_name else path.name
        if (
            not name
            or name in {".", ".."}
            or Path(name).name != name
            or "/" in name
            or "\\" in name
        ):
            raise DesignAssetError("Upload name must be a single safe filename")
        extension = Path(name).suffix.casefold()
        if extension not in self.config.allowed_extensions:
            raise DesignAssetError(f"Upload extension is not allowed: {extension or '(none)'}")
        size = path.stat().st_size
        if size > self.config.max_file_bytes:
            raise DesignAssetError("Upload exceeds the configured file size limit")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        mime_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return {
            "path": str(path),
            "name": name,
            "bytes": size,
            "sha256": digest,
            "mimeType": mime_type,
        }

    def propose_upload(
        self,
        *,
        local_path: str,
        display_name: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        context = self._verified_context()
        source = self._local_upload(local_path, display_name)
        payload = {
            "source": source,
            "folder_id": self.config.google_drive_folder_id,
        }
        preview = {
            "operation": "upload one design asset to the verified private Google Drive folder",
            "source": {key: value for key, value in source.items() if key != "path"},
            "destination_folder": context["folder"],
            "identities": {
                "github_login": context["github_login"],
                "google_email": context["google_email"],
            },
            "requires_confirmation": True,
            "public_sharing": "forbidden",
        }
        return self.index.create_pending_action(
            kind="design_asset_upload",
            payload=payload,
            preview=preview,
            idempotency_key=idempotency_key,
        )

    def confirm(self, token: str) -> dict[str, Any]:
        existing = self.index.get_pending_action(token)
        if existing is None:
            raise DesignAssetError("Unknown confirmation token")
        if existing["kind"] != "design_asset_upload":
            raise DesignAssetError(
                f"Confirmation token is for {existing['kind']}, not design_asset_upload"
            )
        pending, claimed = self.index.claim_pending_action(token)
        if pending is None:
            raise DesignAssetError("Unknown confirmation token")
        if pending["status"] == "completed":
            return {
                "status": "completed",
                "idempotent_replay": True,
                "result": pending["result"],
            }
        if pending["expired"] and pending["status"] == "pending":
            result = {"error": "Confirmation token expired"}
            audit_id = self.index.finish_pending_action(token, status="expired", result=result)
            raise DesignAssetError(f"Confirmation token expired (audit {audit_id})")
        if not claimed:
            raise DesignAssetError(f"Action cannot be confirmed from status {pending['status']}")
        try:
            result = self._execute(pending["kind"], pending["payload"])
        except Exception as exc:
            failure = {"error": str(exc)}
            audit_id = self.index.finish_pending_action(token, status="failed", result=failure)
            raise DesignAssetError(
                f"Confirmed design-asset action failed (audit {audit_id}): {exc}"
            ) from exc
        audit_id = self.index.finish_pending_action(token, status="completed", result=result)
        return {"status": "completed", "audit_id": audit_id, "result": result}

    def _execute(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if kind != "design_asset_upload":
            raise DesignAssetError(f"Unsupported design-asset action kind: {kind}")
        source = payload.get("source", {})
        verified = self._local_upload(source.get("path", ""), source.get("name"))
        if verified["sha256"] != source.get("sha256") or verified["bytes"] != source.get("bytes"):
            raise DesignAssetError("Upload source changed after proposal; create a new proposal")
        context = self._verified_context()
        content = Path(verified["path"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != verified["sha256"]:
            raise DesignAssetError("Upload source changed while it was being read")
        uploaded = self.drive.upload(
            folder_id=self.config.google_drive_folder_id,
            name=verified["name"],
            mime_type=verified["mimeType"],
            content=content,
        )
        try:
            privacy = self._private_permissions(uploaded["id"])
        except Exception:
            try:
                self.drive.delete(uploaded["id"])
            except DesignAssetError as cleanup_error:
                raise DesignAssetError(
                    "Uploaded file failed the private ACL check and cleanup failed: "
                    f"{cleanup_error}"
                ) from cleanup_error
            raise
        return {
            "file": uploaded,
            "private_acl": privacy,
            "folder": context["folder"],
            "identities": {
                "github_login": context["github_login"],
                "google_email": context["google_email"],
            },
        }
