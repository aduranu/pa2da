import logging
import mimetypes
import os
import tempfile

import httpx
from langchain_core.runnables import RunnableConfig

from ken.graph.context import NodeContext, build_choice
from ken.graph.state import AgentState
from ken.processing.archive import extract_file, list_zip_contents

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _resolve_filename(resp: httpx.Response, url: str, label: str) -> str:
    content_disp = resp.headers.get("content-disposition", "")
    if "filename=" in content_disp:
        return content_disp.split("filename=")[-1].strip('" ')
    return os.path.basename(url.split("?")[0]) or f"{label}.dat"


def download_node(state: AgentState, config: RunnableConfig) -> dict:
    """Download supplementary files. Handle ZIPs by listing contents."""
    ctx = NodeContext(state, config)

    if state.get("error"):
        return {}

    links = state.get("supplementary_links", [])
    if not links:
        return {"error": "No links to download.", "status": "error"}

    labels = ", ".join(l.get("label", "file") for l in links)
    ctx.update_status(f":arrow_down: Downloading {labels}...")

    downloaded = []
    tmp_dir = tempfile.mkdtemp(prefix="ken_")

    for link in links:
        url = link["url"]
        label = link.get("label", "unknown")

        try:
            resp = httpx.get(
                url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=120
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                return {"error": f"Download blocked (403) for {label}. May be behind a paywall.", "status": "error"}
            return {"error": f"Download failed for {label}: {e}", "status": "error"}
        except Exception as e:
            return {"error": f"Download failed for {label}: {e}", "status": "error"}

        filename = _resolve_filename(resp, url, label)
        local_path = os.path.join(tmp_dir, filename)
        with open(local_path, "wb") as f:
            f.write(resp.content)

        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        logger.info("Downloaded %s -> %s (%s)", url, local_path, mime_type)
        downloaded.append({"local_path": local_path, "original_name": filename, "mime_type": mime_type})

    # Handle ZIPs
    expanded = []
    for f in downloaded:
        if not f["local_path"].lower().endswith(".zip"):
            expanded.append(f)
            continue

        contents = list_zip_contents(f["local_path"])
        if not contents:
            return {"error": f"ZIP {f['original_name']} contains no tabular files.", "status": "error"}

        if len(contents) == 1:
            extracted = extract_file(f["local_path"], contents[0]["name"], tmp_dir)
            mime = mimetypes.guess_type(contents[0]["name"])[0] or "application/octet-stream"
            expanded.append({"local_path": extracted, "original_name": contents[0]["name"], "mime_type": mime})
            continue

        # Multiple files — ask user to choose
        items = []
        for entry in contents:
            size = _format_size(entry["size_bytes"])
            items.append((entry["name"], f"`{entry['name']}` ({size})"))

        return {
            "downloaded_files": downloaded,
            "status": "downloaded_zip",
            **build_choice("files", f":package: ZIP `{f['original_name']}` contains {len(contents)} files:", items),
        }

    return {"downloaded_files": expanded, "needs_user_choice": False, "status": "downloaded"}
