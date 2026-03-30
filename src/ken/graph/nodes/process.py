import logging
import os
import tempfile

from langchain_core.runnables import RunnableConfig

from ken.graph.context import NodeContext, build_choice
from ken.graph.state import AgentState
from ken.processing.archive import extract_file
from ken.processing.tabular import generate_preview, list_sheets, read_and_clean, save_clean

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in text).strip("_")[:80]


def process_node(state: AgentState, config: RunnableConfig) -> dict:
    """Clean tabular data and generate previews."""
    ctx = NodeContext(state, config)

    if state.get("error"):
        return {}

    files = state.get("downloaded_files", [])
    if not files:
        return {"error": "No files to process.", "status": "error"}

    ctx.update_status(":gear: Processing data...")

    user_choice = state.get("user_choice")
    processed = []

    for file_info in files:
        file_path = file_info["local_path"]
        original_name = file_info["original_name"]

        # Extract from ZIP if needed
        if file_path.lower().endswith(".zip") and user_choice and user_choice != "all":
            tmp = tempfile.mkdtemp(prefix="ken_extract_")
            file_path = extract_file(file_path, user_choice, tmp)
            original_name = os.path.basename(user_choice)

        # Multi-sheet Excel — ask user which sheet (only if we haven't already)
        sheets = list_sheets(file_path)
        if len(sheets) > 1 and state.get("choice_context") != "sheets":
            items = [(s, f"*{s}*") for s in sheets]
            return build_choice("sheets", f":page_facing_up: `{original_name}` has {len(sheets)} sheets:", items)

        # Determine target sheet(s)
        if state.get("choice_context") == "sheets" and user_choice:
            target_sheets = sheets if user_choice == "all" else [user_choice]
        else:
            target_sheets = [sheets[0]] if sheets else [None]

        # Build output directory from paper URL
        page_url = state.get("page_url", "unknown")
        paper_slug = _slugify(page_url.split("/")[-1] if "/" in page_url else page_url)
        output_dir = os.path.join(ctx.settings.storage_path, paper_slug)

        for sheet in target_sheets:
            try:
                df, metadata = read_and_clean(file_path, sheet_name=sheet)
            except Exception as e:
                logger.exception("Failed to process %s sheet=%s", file_path, sheet)
                processed.append({"filename": original_name, "error": str(e)})
                continue

            base_name = os.path.splitext(original_name)[0]
            sheet_suffix = f"_{_slugify(sheet)}" if sheet else ""
            output_name = f"{base_name}{sheet_suffix}_cleaned.csv"
            output_path = os.path.join(output_dir, output_name)

            save_clean(df, output_path)
            processed.append({
                "path": output_path,
                "filename": output_name,
                "preview_text": generate_preview(df),
                "row_count": metadata["row_count"],
                "col_count": metadata["col_count"],
            })

    return {"processed_files": processed, "status": "processed"}
