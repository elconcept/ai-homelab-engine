#!/usr/bin/env python3
"""Register Bearer-authenticated MCP servers on Cloudflare and attach to ai-admin-tools.

Public source. Secret values are supplied only at runtime via GitHub Actions Secrets.
Requires a Cloudflare API token with the 'MCP Portals Write' permission.
"""
import json
import os
import sys
from urllib import error, request

ACCOUNT_ID = "bf80f99520a901c0a5d2099e268b4524"
PORTAL_ID = "saos-chatgpt-pilot"
API_ROOT = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/access/ai-controls/mcp"

TOKEN = os.environ.get("CF_API_TOKEN", "")
if not TOKEN:
    sys.exit("Missing CF_API_TOKEN GitHub Actions Secret (MCP Portals Write permission).")

def api(method, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        API_ROOT + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=35) as resp:
            result = json.load(resp)
    except error.HTTPError as exc:
        # Never print response bodies: some providers include sensitive details.
        raise RuntimeError(f"Cloudflare {method} {path} returned HTTP {exc.code}") from None
    if not result.get("success"):
        codes = [str(e.get("code", "?")) for e in result.get("errors", [])]
        raise RuntimeError(f"Cloudflare {method} {path} rejected request; error codes: {','.join(codes)}")
    return result["result"]

# These are static, well-defined endpoints. No user-provided arbitrary URLs.
SPECS = [
    ("mcp-azure", "Azure MCP via DS1821", "https://mcp-bridges.xlap.pl/azure/mcp", "MCP_BRIDGE_API_KEY"),
    ("mcp-gcp-ws", "GCP Workspace via DS1821", "https://mcp-bridges.xlap.pl/gcp-ws/mcp", "MCP_BRIDGE_API_KEY"),
    ("mcp-gcp-personal", "GCP Personal via DS1821", "https://mcp-bridges.xlap.pl/gcp-personal/mcp", "MCP_BRIDGE_API_KEY"),
    ("mcp-commander-ds1821", "Desktop Commander DS1821+", "https://mcp-bridges.xlap.pl/commander/mcp", "MCP_BRIDGE_API_KEY"),
    ("mcp-huggingface", "Hugging Face Official MCP", "https://huggingface.co/mcp", "HF_TOKEN"),
    ("mcp-github", "GitHub Official MCP", "https://api.githubcopilot.com/mcp/", "HOMELAB_GH_PAT"),
    ("mcp-render", "Render Official MCP", "https://mcp.render.com/mcp", "RENDER_API_KEY"),
    ("mcp-tavily", "Tavily Official MCP", "https://mcp.tavily.com/mcp/", "TAVILY_API_KEY"),
    ("mcp-resend", "Resend Official MCP", "https://mcp.resend.com/mcp", "RESEND_API_KEY"),
]

missing = sorted({key for _, _, _, key in SPECS if not os.environ.get(key)})
if missing:
    sys.exit("Missing Actions Secrets: " + ", ".join(missing))

registered = []
for server_id, name, url, key in SPECS:
    body = {
        "id": server_id,
        "name": name,
        "hostname": url,
        "auth_type": "bearer",
        "auth_credentials": os.environ[key],
        "secure_web_gateway": True,
    }
    try:
        existing = api("GET", "/servers/" + server_id)
    except RuntimeError as exc:
        if not str(exc).endswith("HTTP 404"):
            raise
        existing = None
    if existing:
        body.pop("id")
        api("PUT", "/servers/" + server_id, body)
        operation = "updated"
    else:
        api("POST", "/servers", body)
        operation = "created"
    registered.append(server_id)
    print(f"{server_id}: {operation}")

portal = api("GET", "/portals/" + PORTAL_ID)
preserved = []
for entry in portal.get("servers", []):
    # The read response contains both user overrides and read-only metadata;
    # write back only the documented editable fields.
    node = {"server_id": entry["server_id"]}
    for key in ("on_behalf", "default_disabled"):
        if key in entry:
            node[key] = entry[key]
    for field in ("updated_tools", "updated_prompts"):
        if entry.get(field):
            node[field] = [
                {k: item[k] for k in ("name", "alias", "description", "enabled") if k in item}
                for item in entry[field]
            ]
    preserved.append(node)

seen = {node["server_id"] for node in preserved}
for server_id in registered:
    if server_id not in seen:
        preserved.append({"server_id": server_id, "on_behalf": False, "default_disabled": False})

api("PUT", "/portals/" + PORTAL_ID, {
    "name": portal["name"],
    "hostname": portal["hostname"],
    "description": portal.get("description") or "",
    "code_mode": portal.get("code_mode") or "enforced",
    "secure_web_gateway": portal.get("secure_web_gateway", True),
    "servers": preserved,
})
confirmed = api("GET", "/portals/" + PORTAL_ID)
attached = {item["server_id"] for item in confirmed.get("servers", [])}
print("Portal:", PORTAL_ID, "total servers:", len(attached))
print("Registered and attached:", ", ".join(x for x in registered if x in attached))
if any(x not in attached for x in registered):
    sys.exit("At least one MCP server was not attached. Review portal configuration.")
