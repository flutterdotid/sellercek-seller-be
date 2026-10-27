import asyncio
import json
import mimetypes
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
    file_path: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    media_urls: Optional[List[str]] = None,
    title: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    publish_now: bool = True
) -> str:
    """
    Publikasikan atau jadwalkan postingan konten baru ke media sosial seller.
    Mendukung upload media gambar/video langsung dari file lokal komputer/server ATAU via URL publik.
    Parameter:
      - account_id: ID akun sasaran postingan di SellerCek
      - caption: Teks status atau caption konten
      - file_path: (Opsional) Path ke file gambar/video lokal di komputer (misal: /path/to/promo.mp4 atau /path/to/foto.jpg)
      - file_paths: (Opsional) Daftar multiple file gambar/video lokal di komputer
      - media_urls: (Opsional) Daftar URL publik gambar atau video
      - title: (Opsional) Judul postingan (berguna untuk video YouTube / TikTok)
      - scheduled_at: (Opsional) Waktu penjadwalan format ISO (misal: 2026-10-28T15:00:00Z)
      - publish_now: Langsung publish (True) atau simpan sebagai draft (False)
    """
    local_files = []
    if file_path:
        local_files.append(file_path)
    if file_paths:
        for fp in file_paths:
            if fp and fp not in local_files:
                local_files.append(fp)

    svc = _get_service()

    if local_files:
        upload_files = []
        for fp in local_files:
            fp_expanded = os.path.expanduser(fp)
            if not os.path.isfile(fp_expanded):
                return json.dumps({
                    "success": False,
                    "error": f"File lokal tidak ditemukan: {fp}"
                }, indent=2, ensure_ascii=False)

            fname = os.path.basename(fp_expanded)
            c_type, _ = mimetypes.guess_type(fp_expanded)
            if not c_type:
                c_type = "video/mp4" if fname.lower().endswith(('.mp4', '.mov', '.webm', '.m4v')) else "image/jpeg"

            try:
                with open(fp_expanded, "rb") as f:
                    f_bytes = f.read()
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Gagal membaca file {fp}: {str(e)}"
                }, indent=2, ensure_ascii=False)

            upload_files.append(("files", (fname, f_bytes, c_type)))

        form_data = {
            "account_id": account_id,
            "caption": caption,
            "title": title or "",
            "scheduled_at": scheduled_at or ""
        }
        res = await svc.create_sosmed_post_multipart(form_data=form_data, files=upload_files)
        return json.dumps(res, indent=2, ensure_ascii=False)

    payload = {
        "account_id": account_id,
        "caption": caption,
        "media_urls": media_urls or [],
        "title": title or "",
        "scheduled_at": scheduled_at or "",
        "publish_now": publish_now
    }
    res = await svc.create_sosmed_post(payload)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sellercek_upload_media(file_path: str) -> str:
    """
    Upload langsung media gambar atau video dari file lokal (PC/Server) ke CDN / Cloudflare R2 SellerCek.
    Mendapatkan `media_url` publik yang siap dipasang pada postingan media sosial.
    Batas: 100 MB (Video) dan 25 MB (Gambar).
    Parameter:
      - file_path: Path lengkap ke file gambar atau video lokal (misal: /path/to/video.mp4 atau /path/to/gambar.jpg)
    """
    fp_expanded = os.path.expanduser(file_path)
    if not os.path.isfile(fp_expanded):
        return json.dumps({"success": False, "error": f"File lokal tidak ditemukan: {file_path}"}, indent=2, ensure_ascii=False)

    fname = os.path.basename(fp_expanded)
    c_type, _ = mimetypes.guess_type(fp_expanded)
    if not c_type:
        c_type = "video/mp4" if fname.lower().endswith(('.mp4', '.mov', '.webm', '.m4v')) else "image/jpeg"

    try:
        with open(fp_expanded, "rb") as f:
            f_bytes = f.read()
    except Exception as e:
        return json.dumps({"success": False, "error": f"Gagal membaca file: {str(e)}"}, indent=2, ensure_ascii=False)

    svc = _get_service()
    res = await svc.upload_media_file(file_bytes=f_bytes, filename=fname, content_type=c_type)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def sosmed_create_post(
    account_id: str,
    caption: str,
    file_path: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    media_urls: Optional[List[str]] = None,
    title: Optional[str] = None,
    scheduled_at: Optional[str] = None,
    publish_now: bool = True
) -> str:
    """Alias untuk sellercek_create_post (Mendukung file_path lokal atau media_urls)."""
    return await sellercek_create_post(
        account_id=account_id,
        caption=caption,
        file_path=file_path,
        file_paths=file_paths,
        media_urls=media_urls,
        title=title,
        scheduled_at=scheduled_at,
        publish_now=publish_now
    )

@mcp.tool()
async def sosmed_upload_media(file_path: str) -> str:
    """Alias untuk sellercek_upload_media."""
    return await sellercek_upload_media(file_path=file_path)

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
