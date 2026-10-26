from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.schemas.sosmed import (
    UpdateAiBotRequest,
    CreatePostRequest,
    SendDirectMessageRequest,
    RagSearchRequest
)
from app.services.seller_sosmed import SellerCekSosmedService

router = APIRouter(prefix="/sosmed", tags=["Seller Sosmed"])

def get_sosmed_service(
    authorization: Optional[str] = Header(None),
    x_seller_api_key: Optional[str] = Header(None)
) -> SellerCekSosmedService:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "").strip()
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

@router.post("/posts")
async def create_post(req: CreatePostRequest, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Publikasikan atau jadwalkan postingan ke media sosial."""
    res = await svc.create_sosmed_post(req.model_dump())
    return res

@router.post("/send-dm")
async def send_dm(req: SendDirectMessageRequest, svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Kirim direct message ke customer / follower melalui bot akun seller."""
    res = await svc.send_direct_message(req.account_id, req.recipient_id, req.message)
    return res

@router.get("/quota")
async def get_quota(svc: SellerCekSosmedService = Depends(get_sosmed_service)):
    """Cek sisa kuota postingan, akun, dan token AI langganan."""
    quota = await svc.get_seller_quota()
    return {"success": True, "quota": quota}
