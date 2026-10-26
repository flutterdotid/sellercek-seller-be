from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SellerAuthContext(BaseModel):
    seller_id: str
    email: Optional[str] = None
    role: str = "seller"

class SosmedAccountItem(BaseModel):
    account_id: str
    platform: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str = "connected"
    ai_chatbot_dm_enabled: bool = False
    ai_chatbot_comment_enabled: bool = False
    ai_rag_enabled: bool = False

class UpdateAiBotRequest(BaseModel):
    account_id: str
    system_prompt: Optional[str] = None
    knowledge_base: Optional[str] = None
    ai_chatbot_dm_enabled: Optional[bool] = None
    ai_chatbot_comment_enabled: Optional[bool] = None
    ai_rag_enabled: Optional[bool] = None

class CreatePostRequest(BaseModel):
    account_id: str
    caption: str
    media_urls: Optional[List[str]] = None
    publish_now: bool = True
    scheduled_at: Optional[str] = None

class SendDirectMessageRequest(BaseModel):
    account_id: str
    recipient_id: str
    message: str

class RagSearchRequest(BaseModel):
    account_id: str
    query: str
    top_k: int = 3

class RagSearchResult(BaseModel):
    chunk_text: str
    similarity: float
    document_name: Optional[str] = None
