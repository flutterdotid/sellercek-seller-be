import asyncio
import json
import os
import sys
from contextvars import ContextVar
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from app.services.seller_sosmed import SellerCekSosmedService
from app.core.config import settings

# Inisialisasi FastMCP Server
from mcp.server.transport_security import TransportSecuritySettings
mcp = FastMCP(
    "SellerCek Social Media Automation MCP",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
)

# ContextVar untuk menyimpan API Key dari sesi SSE
current_api_key_ctx: ContextVar[Optional[str]] = ContextVar("current_api_key_ctx", default=None)

def _get_service() -> SellerCekSosmedService:
    api_key = current_api_key_ctx.get() or os.getenv("SELLERCEK_API_KEY", settings.DEFAULT_SELLER_API_KEY)
    token = os.getenv("SELLERCEK_TOKEN", None)
    return SellerCekSosmedService(auth_token=token, api_key=api_key)

@mcp.tool()
async def sellercek_list_accounts() -> str:
    """
    Dapatkan daftar semua akun media sosial yang terhubung ke dashboard SellerCek.
    Berguna untuk mengetahui platform apa saja (TikTok, Instagram, Facebook, Threads)
    dan status chatbot bot masing-masing akun.
    """
    svc = _get_service()
    accounts = await svc.list_connected_accounts()
    return json.dumps(accounts, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_get_account_detail(account_id: str) -> str:
    """
    Ambil detail pengaturan dan instruksi chatbot AI untuk akun sosial media tertentu.
    Parameter:
      - account_id: ID unik akun sosial media di SellerCek.
    """
    svc = _get_service()
    detail = await svc.get_account_detail(account_id)
    if not detail:
        return json.dumps({"error": f"Akun dengan ID {account_id} tidak ditemukan."}, indent=2)
    return json.dumps(detail, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_update_ai_bot(
    account_id: str,
    system_prompt: Optional[str] = None,
    knowledge_base: Optional[str] = None,
    ai_chatbot_dm_enabled: Optional[bool] = None,
    ai_chatbot_comment_enabled: Optional[bool] = None,
    ai_rag_enabled: Optional[bool] = None
) -> str:
    """
    Ubah persona, system prompt, knowledge base, dan toggle automasi bot AI untuk akun sosial media.
    Parameter:
      - account_id: ID akun sosial media
      - system_prompt: Instruksi persona chatbot
      - knowledge_base: Ringkasan teks pengetahuan produk/SOP
      - ai_chatbot_dm_enabled: Aktifkan auto-reply Direct Message (DM)
      - ai_chatbot_comment_enabled: Aktifkan auto-reply komentar postingan
      - ai_rag_enabled: Aktifkan pencarian semantik dokumen RAG (Knowledge Base Dokumen)
    """
    svc = _get_service()
    payload = {}
    if system_prompt is not None:
        payload["system_prompt"] = system_prompt
    if knowledge_base is not None:
        payload["knowledge_base"] = knowledge_base
    if ai_chatbot_dm_enabled is not None:
        payload["ai_chatbot_dm_enabled"] = ai_chatbot_dm_enabled
    if ai_chatbot_comment_enabled is not None:
        payload["ai_chatbot_comment_enabled"] = ai_chatbot_comment_enabled
    if ai_rag_enabled is not None:
        payload["ai_rag_enabled"] = ai_rag_enabled

    res = await svc.update_ai_configuration(account_id, payload)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_list_posts(account_id: Optional[str] = None, page: int = 1, limit: int = 50) -> str:
    """
    Melihat daftar postingan sosial media (terjadwal atau terpublikasi).
    Parameter:
      - account_id: (Opsional) Filter berdasarkan akun tertentu.
      - page: Nomor halaman (default: 1)
      - limit: Jumlah data per halaman (default: 50)
    """
    svc = _get_service()
    res = await svc.list_sosmed_posts(account_id=account_id, page=page, limit=limit)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_create_post(
    account_id: str,
    caption: str,
    media_urls: Optional[List[str]] = None,
    publish_now: bool = True
) -> str:
    """
    Publikasikan atau jadwalkan postingan konten baru ke media sosial seller.
    Parameter:
      - account_id: ID akun sasaran postingan
      - caption: Teks status atau caption konten
      - media_urls: Daftar URL gambar atau video yang ingin diposting
      - publish_now: Langsung publish (True) atau simpan sebagai draft (False)
    """
    svc = _get_service()
    payload = {
        "account_id": account_id,
        "caption": caption,
        "media_urls": media_urls or [],
        "publish_now": publish_now
    }
    res = await svc.create_sosmed_post(payload)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_send_direct_message(account_id: str, recipient_id: str, message: str) -> str:
    """
    Kirim pesan balasan langsung (Direct Message) ke follower/konsumen di platform sosial media.
    Parameter:
      - account_id: ID akun sosmed seller
      - recipient_id: ID follower / user sosmed tujuan
      - message: Isi pesan teks yang dikirimkan
    """
    svc = _get_service()
    res = await svc.send_direct_message(account_id, recipient_id, message)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_list_chats(account_id: Optional[str] = None) -> str:
    """
    Melihat daftar chat dan Direct Messages (DM) masuk dari customer media sosial.
    Parameter:
      - account_id: (Opsional) Filter berdasarkan akun tertentu.
    """
    svc = _get_service()
    res = await svc.list_chats(account_id=account_id)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_get_chat_messages(chat_id: str) -> str:
    """
    Melihat riwayat percakapan pesan di dalam room chat DM tertentu.
    Parameter:
      - chat_id: ID room percakapan / chat.
    """
    svc = _get_service()
    res = await svc.get_chat_messages(chat_id=chat_id)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_reply_chat(chat_id: str, message: str) -> str:
    """
    Kirim pesan balasan ke percakapan chat / DM customer.
    Parameter:
      - chat_id: ID room percakapan chat.
      - message: Teks pesan balasan.
    """
    svc = _get_service()
    res = await svc.reply_chat(chat_id=chat_id, message=message)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_list_comments(account_id: Optional[str] = None) -> str:
    """
    Melihat komentar-komentar terbaru customer pada postingan media sosial seller.
    Parameter:
      - account_id: (Opsional) Filter berdasarkan akun tertentu.
    """
    svc = _get_service()
    res = await svc.list_comments(account_id=account_id)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_reply_comment(comment_id: str, message: str) -> str:
    """
    Balas komentar customer pada postingan media sosial.
    Parameter:
      - comment_id: ID komentar yang ingin dibalas.
      - message: Teks balasan komentar.
    """
    svc = _get_service()
    res = await svc.reply_comment(comment_id=comment_id, message=message)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_get_quota_status() -> str:
    """
    Cek sisa limit kuota akun sosial media yang terhubung, sisa token AI, dan status paket langganan.
    """
    svc = _get_service()
    quota = await svc.get_seller_quota()
    return json.dumps(quota, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Menjalankan MCP server melalui STDIO (standar untuk Claude Desktop, Hermes, Cursor)
    mcp.run(transport="stdio")
