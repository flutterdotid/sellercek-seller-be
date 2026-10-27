import json
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

class SellerCekSosmedService:
    """
    Service gateway yang menghubungkan request seller ke core backend SellerCek
    atau database replika, memastikan kontrol izin dan kuota seller.
    """
    def __init__(self, auth_token: Optional[str] = None, api_key: Optional[str] = None):
        self.auth_token = auth_token
        self.api_key = api_key or settings.DEFAULT_SELLER_API_KEY
        self.base_url = settings.SELLERCEK_CORE_API_URL.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-Seller-API-Key"] = self.api_key
        return headers

    async def list_connected_accounts(self) -> List[Dict[str, Any]]:
        """Mengambil semua akun sosmed milik seller yang sedang terhubung."""
        url = f"{self.base_url}/api/v1/sosmed/accounts"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 200:
                    data = res.json()
                    return data.get("accounts", [])
            except Exception as e:
                pass
        return []

    async def get_account_detail(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Mengambil detail konfigurasi akun sosmed dan AI bot seller."""
        url = f"{self.base_url}/api/v1/sosmed/accounts/{account_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        return None

    async def update_ai_configuration(self, account_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Memperbarui prompt, aturan knowledge, dan toggle automasi bot sosmed."""
        url = f"{self.base_url}/api/v1/sosmed/accounts/{account_id}/ai-config"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json=payload)
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def search_rag_knowledge(self, account_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Melakukan pencarian relevansi semantik dokumen pengetahuan seller."""
        url = f"{self.base_url}/api/v1/sosmed/accounts/{account_id}/rag-search"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json={"query": query, "top_k": top_k})
                if res.status_code == 200:
                    return res.json().get("results", [])
            except Exception:
                pass
        return []

    async def upload_media_file(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Upload file gambar/video ke Cloudflare R2 via Core API."""
        url = f"{self.base_url}/api/v1/sosmed/media/upload"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-Seller-API-Key"] = self.api_key

        files = {"file": (filename, file_bytes, content_type)}
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(url, headers=headers, files=files)
                if res.status_code >= 400:
                    try:
                        err_json = res.json()
                        return {"success": False, "status_code": res.status_code, "error": err_json.get("detail", str(err_json))}
                    except Exception:
                        return {"success": False, "status_code": res.status_code, "error": res.text}
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def list_sosmed_posts(self, account_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Ambil daftar postingan sosial media seller."""
        url = f"{self.base_url}/api/v1/sosmed/posts"
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if account_id:
            params["account_id"] = account_id
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                res = await client.get(url, headers=self._headers(), params=params)
                if res.status_code >= 400:
                    try:
                        err_json = res.json()
                        return {"success": False, "status_code": res.status_code, "error": err_json.get("detail", str(err_json))}
                    except Exception:
                        return {"success": False, "status_code": res.status_code, "error": res.text}
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e), "posts": []}

    async def create_sosmed_post_multipart(
        self,
        form_data: Dict[str, Any],
        files: List[Any]
    ) -> Dict[str, Any]:
        """Kirim postingan bersama file multipart langsung ke Core API."""
        url = f"{self.base_url}/api/v1/sosmed/posts"
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-Seller-API-Key"] = self.api_key

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(url, headers=headers, data=form_data, files=files)
                if res.status_code >= 400:
                    try:
                        err_json = res.json()
                        return {"success": False, "status_code": res.status_code, "error": err_json.get("detail", str(err_json))}
                    except Exception:
                        return {"success": False, "status_code": res.status_code, "error": res.text}
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def create_sosmed_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publikasikan atau jadwalkan postingan sosial media seller."""
        url = f"{self.base_url}/api/v1/sosmed/posts"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json=payload)
                if res.status_code >= 400:
                    try:
                        err_json = res.json()
                        return {"success": False, "status_code": res.status_code, "error": err_json.get("detail", str(err_json))}
                    except Exception:
                        return {"success": False, "status_code": res.status_code, "error": res.text}
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def send_direct_message(self, account_id: str, recipient_id: str, message: str) -> Dict[str, Any]:
        """Kirim direct message (DM) ke pengguna sosial media melalui bot seller."""
        url = f"{self.base_url}/api/v1/sosmed/accounts/{account_id}/send-dm"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json={"recipient_id": recipient_id, "message": message})
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def list_chats(self, account_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Melihat daftar chat / DM masuk dari akun sosial media seller."""
        url = f"{self.base_url}/api/v1/sosmed/chats"
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if account_id:
            params["account_id"] = account_id
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=self._headers(), params=params)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                return {"success": False, "error": str(e), "chats": []}
        return {"success": False, "chats": []}

    async def get_chat_messages(self, chat_id: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Melihat riwayat percakapan suatu chat DM."""
        url = f"{self.base_url}/api/v1/sosmed/chats/{chat_id}/messages"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=self._headers(), params={"page": page, "limit": limit})
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                return {"success": False, "error": str(e), "messages": []}
        return {"success": False, "messages": []}

    async def reply_chat(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Kirim balasan chat / DM ke pelanggan."""
        url = f"{self.base_url}/api/v1/sosmed/chats/{chat_id}/reply"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json={"message": message})
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def list_comments(self, account_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Melihat daftar komentar pada postingan media sosial seller."""
        url = f"{self.base_url}/api/v1/sosmed/comments"
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if account_id:
            params["account_id"] = account_id
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(url, headers=self._headers(), params=params)
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                return {"success": False, "error": str(e), "comments": []}
        return {"success": False, "comments": []}

    async def reply_comment(self, comment_id: str, message: str) -> Dict[str, Any]:
        """Balas komentar customer di media sosial."""
        url = f"{self.base_url}/api/v1/sosmed/comments/{comment_id}/reply"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json={"message": message})
                return res.json()
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def get_seller_quota(self) -> Dict[str, Any]:
        """Ambil sisa kuota akun, token AI bot, dan status langganan seller."""
        url = f"{self.base_url}/api/v1/sosmed/quota"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.get(url, headers=self._headers())
                if res.status_code == 200:
                    return res.json()
            except Exception as e:
                pass
        return {"account_limit": 1, "active_accounts": 1, "status": "active"}
