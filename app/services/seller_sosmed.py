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

    async def create_sosmed_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publikasikan atau jadwalkan postingan sosial media seller."""
        url = f"{self.base_url}/api/v1/sosmed/posts"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                res = await client.post(url, headers=self._headers(), json=payload)
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
