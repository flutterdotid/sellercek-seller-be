# SellerCek Seller Backend & MCP Server (`sellercek-seller-be`)

Backend khusus seller dan **MCP (Model Context Protocol) Server** untuk ekosistem SellerCek:
- **REST API**: Khusus seller untuk automasi media sosial, bot AI, auto DM / comment, Knowledge Base (RAG), dan monitoring kuota akun.
- **MCP Server (SSE / STDIO)**: Memungkinkan AI Agent seperti **Claude Desktop / Claude Code, Hermes Agent, n8n, OpenClaw, LangChain, Flowise, Cursor** berinteraksi langsung dengan layanan sosmed seller menggunakan protokol MCP standar.

---

## 🚀 Fitur Utama

1. **REST API Seller**
   - Autentikasi via Seller JWT Token atau Seller API Key (`X-Seller-API-Key`).
   - Manajemen Akun Sosmed (TikTok, Instagram, Facebook, Threads).
   - Chatbot AI & RAG Configuration (Knowledge Base dokumen PDF/DOCX/TXT).
   - Auto DM & Auto Reply Comment.
   - Scheduler & Direct Posting konten media sosial.
   - Status & Kuota Paket Langganan.

2. **MCP (Model Context Protocol) Server**
   - Protokol: **Server-Sent Events (SSE)** via HTTP (`/mcp/sse`) & **STDIO** (`python -m app.mcp_server`).
   - Tools yang disediakan untuk AI Agent:
     - `sellercek_list_accounts`: Daftar akun sosmed yang terhubung beserta platform dan statusnya.
     - `sellercek_get_account_detail`: Ambil detail akun sosmed, prompt AI, dan status RAG.
     - `sellercek_update_ai_bot`: Konfigurasi system prompt, instruksi chatbot, dan toggle auto-DM / comment.
     - `sellercek_search_knowledge_rag`: Lakukan pencarian semantik semu/vektor pada knowledge base RAG akun.
     - `sellercek_create_post`: Jadwalkan atau publikasikan postingan teks/media ke akun sosmed seller.
     - `sellercek_send_direct_message`: Kirim balasan DM langsung ke follower/prospek melalui bot sosmed.
     - `sellercek_get_quota_status`: Cek sisa kuota posting, token AI, dan status paket langganan seller.

---

## 🛠️ Tech Stack
- **Framework**: FastAPI (Async Python 3.11+)
- **Protocols**: REST API, Model Context Protocol (MCP) JSON-RPC 2.0 / SSE
- **Database**: PostgreSQL (SQLAlchemy Async + asyncpg) / Dual-layer vector fallback
- **Authentication**: JWT & API Key
- **Architecture**: Modular Service-Oriented Architecture

---

## 📦 Menjalankan Layanan

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Jalankan FastAPI REST + MCP SSE Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
```
- REST Documentation: `http://localhost:8008/docs`
- MCP SSE Endpoint: `http://localhost:8008/mcp/sse`

---

## 🤖 Menghubungkan ke AI Agent

### A. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "sellercek": {
      "command": "/path/to/sellercek-seller-be/venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "env": {
        "SELLERCEK_API_KEY": "YOUR_SELLER_API_KEY",
        "SELLERCEK_API_URL": "https://api.sellercek.com"
      }
    }
  }
}
```

### B. Hermes Agent (`config.yaml`)
```yaml
mcp_servers:
  sellercek:
    command: python3
    args: ["-m", "app.mcp_server"]
    env:
      SELLERCEK_API_KEY: "YOUR_SELLER_API_KEY"
      SELLERCEK_API_URL: "https://api.sellercek.com"
```

### C. n8n / OpenClaw / Workflow Automation
Gunakan node HTTP Request atau MCP Tool Connector yang mengarah ke:
- `POST http://localhost:8008/api/v1/sosmed/...`
- Atau hubungkan via Server-Sent Events (SSE) `http://localhost:8008/mcp/sse` dengan header `X-Seller-API-Key: <token>`.

---

## 👥 Tim & Kontribusi
- Repo: `flutterdotid/sellercek-seller-be`
- Workflow: Branch `agent/<nama>`, merge ke `uat`, lalu `main`.
