from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from app.schemas.sosmed import (
    UpdateAiBotRequest,
    CreatePostRequest,
    SendDirectMessageRequest,
    SendReplyChatRequest,
    SendReplyCommentRequest,
    RagSearchRequest
)
from app.services.seller_sosmed import SellerCekSosmedService

router = APIRouter(prefix="/api/v1/sosmed", tags=["Seller Sosmed"])

def get_sosmed_service(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_seller_api_key: Optional[str] = Header(None)
) -> SellerCekSosmedService:
    token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_val = authorization.replace("Bearer ", "").strip()
        if bearer_val.startswith("sk_live_"):
            x_seller_api_key = bearer_val
        else:
            token = bearer_val
    elif not x_seller_api_key:
        x_seller_api_key = request.headers.get("X-Seller-API-Key") or request.headers.get("x-seller-api-key")

    if not token and not x_seller_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: X-Seller-API-Key or Bearer token required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return SellerCekSosmedService(auth_token=token, api_key=x_seller_api_key)

@router.get("/accounts")
async def list_accounts(svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Mengambil daftar semua akun media sosial yang terhubung."""
    accounts = await svc.list_connected_accounts()
    return {"success": True, "accounts": accounts}

@router.get("/accounts/{account_id}")
async def get_account(account_id: str, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Mengambil detail profil akun dan konfigurasi chatbot AI."""
    detail = await svc.get_account_detail(account_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Akun sosial media tidak ditemukan.")
    return {"success": True, "data": detail}

@router.post("/accounts/ai-config")
async def update_ai_config(req: UpdateAiBotRequest, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Konfigurasi system prompt, instruksi knowledge, dan bot toggle akun."""
    res = await svc.update_ai_configuration(req.account_id, req.model_dump(exclude_unset=True))
    return res

@router.post("/accounts/rag-search")
async def search_rag(req: RagSearchRequest, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Pencarian semantik pada dokumen knowledge base RAG akun sosmed."""
    results = await svc.search_rag_knowledge(req.account_id, req.query, req.top_k)
    return {"success": True, "results": results}

@router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """
    Upload langsung media gambar/video via API Key ke Cloudflare R2 / Server SellerCek.
    Mendapatkan `media_url` publik yang siap dipasang pada `media_urls` endpoint `/posts`.
    Batas: 100 MB (Video) dan 25 MB (Gambar).
    """
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    res = await svc.upload_media_file(file_bytes=file_bytes, filename=file.filename or "media_upload", content_type=content_type)
    return res

@router.post("/posts")
async def create_post(
    request: Request,
    account_id: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    scheduled_at: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """
    Publikasikan atau jadwalkan postingan ke media sosial.
    Bisa langsung upload file (multipart/form-data) atau pakai JSON media_urls.
    """
    content_type = request.headers.get("content-type") or ""
    if "application/json" in content_type.lower():
        try:
            req_json = await request.json()
        except Exception:
            req_json = {}
        return await svc.create_sosmed_post(req_json)

    # Multipart / form-data
    form_data = {
        "account_id": account_id or "",
        "caption": caption or "",
        "title": title or "",
        "scheduled_at": scheduled_at or "",
        "type": type or ""
    }
    upload_list = []
    if file and file.filename:
        upload_list.append(("files", (file.filename, await file.read(), file.content_type or "application/octet-stream")))
    if files:
        for f in files:
            if f and f.filename:
                upload_list.append(("files", (f.filename, await f.read(), f.content_type or "application/octet-stream")))

    return await svc.create_sosmed_post_multipart(form_data=form_data, files=upload_list)

@router.post("/send-dm")
async def send_dm(req: SendDirectMessageRequest, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Kirim direct message ke customer / follower melalui bot akun seller."""
    res = await svc.send_direct_message(req.account_id, req.recipient_id, req.message)
    return res

@router.get("/chats")
async def list_chats(
    account_id: Optional[str] = Query(None, description="Filter berdasarkan ID akun sosmed"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """Melihat daftar chat / pesan masuk (Direct Message) pelanggan."""
    return await svc.list_chats(account_id=account_id, page=page, limit=limit)

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """Melihat riwayat percakapan / pesan di dalam room chat tertentu."""
    return await svc.get_chat_messages(chat_id=chat_id, page=page, limit=limit)

@router.post("/chats/{chat_id}/reply")
async def reply_chat(
    chat_id: str,
    req: SendReplyChatRequest,
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """Membalas chat / DM pelanggan."""
    return await svc.reply_chat(chat_id=chat_id, message=req.message)

@router.get("/comments")
async def list_comments(
    account_id: Optional[str] = Query(None, description="Filter berdasarkan ID akun sosmed"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """Melihat daftar komentar pada postingan media sosial seller."""
    return await svc.list_comments(account_id=account_id, page=page, limit=limit)

@router.post("/comments/{comment_id}/reply")
async def reply_comment(
    comment_id: str,
    req: SendReplyCommentRequest,
    svc: SellerCekSosmedService = Depends(get_sosmed_service)
):
    """Membalas komentar customer pada postingan."""
    return await svc.reply_comment(comment_id=comment_id, message=req.message)

@router.get("/quota")
async def get_quota(svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Cek sisa kuota postingan, akun, dan token AI langganan."""
    quota = await svc.get_seller_quota()
    return {"success": True, "quota": quota}
