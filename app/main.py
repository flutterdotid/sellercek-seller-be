from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.mcp_server import mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[SellerCek-Seller-BE] Starting seller service on port {settings.PORT}...")
    yield
    print("[SellerCek-Seller-BE] Shutting down...")

app = FastAPI(
    title="SellerCek Seller Backend & MCP Server",
    description="API khusus Seller dan Model Context Protocol (MCP) Server untuk Social Media Automation & AI Agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Middleware untuk mencatat request agent.sellercek.com ke DB log_agent_api_requests
from app.core.logging_middleware import AgentApiRequestLoggingMiddleware
app.add_middleware(AgentApiRequestLoggingMiddleware)

# Hubungkan API V1
from app.api.v1 import api_v1_router
app.include_router(api_v1_router)

# Mount MCP via SSE untuk integrasi Web / Network Agents (n8n, OpenClaw, dll.)
try:
    mcp_app = mcp.sse_app(mount_path="/mcp")
    app.mount("/mcp", mcp_app)
except Exception as e:
    print(f"[SellerCek-Seller-BE] MCP SSE Mount Notice: {e}")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "sellercek-seller-be",
        "version": "1.0.0",
        "mcp_enabled": True
    }
