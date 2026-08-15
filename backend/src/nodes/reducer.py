import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import llm
from src.schemas.state import State
from src.schemas.models import GlobalImagePlan
from src.prompts.system_prompts import DECIDE_IMAGES_SYSTEM
from src.tools.image_gen import gemini_generate_image_bytes

def merge_content(state: State) -> dict:
    print(f"\n🧩 [Reducer] Merging all drafted sections into a single document...",flush=True)
    plan = state["plan"]
    ordered_sections = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    merged_md = f"# {plan.system_title}\n\n" + "\n\n".join(ordered_sections).strip() + "\n"
    return {"merged_md": merged_md}

# def decide_images(state: State) -> dict:
#     print(f"🎨 [Designer] Planning where architecture diagrams should go...",flush=True)
#     planner = llm.with_structured_output(GlobalImagePlan)
#     image_plan = planner.invoke([
#         SystemMessage(content=DECIDE_IMAGES_SYSTEM),
#         HumanMessage(content=f"System Title: {state['plan'].system_title}\nTopic: {state['topic']}\nDocument:\n{state['merged_md']}"),
#     ])
#     return {
#         "md_with_placeholders": image_plan.md_with_placeholders,
#         "image_specs": [img.model_dump() for img in image_plan.images],
#     }

def decide_images(state: State) -> dict:
    print(f"🎨 [Designer] Skipping image generation due to API quotas. (Will use Mermaid.js later!)", flush=True)
    return {
        "md_with_placeholders": state["merged_md"],
        "image_specs": [], # Empty list means it skips the Artist node!
    }
def generate_and_place_images(state: State) -> dict:
    print(f"🖼️ [Artist] Generating technical diagrams using Gemini...",flush=True)
    plan = state["plan"]
    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    if not image_specs:
        filename = f"{_safe_slug(plan.system_title)}.md"
        Path(filename).write_text(md, encoding="utf-8")
        return {"final": md}

    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    for spec in image_specs:
        out_path = images_dir / spec["filename"]
        if not out_path.exists():
            try:
                img_bytes = gemini_generate_image_bytes(spec["prompt"])
                out_path.write_bytes(img_bytes)
            except Exception as e:
                md = md.replace(spec["placeholder"], f"> **[DIAGRAM GENERATION FAILED]** {e}\n")
                continue

        img_md = f"![{spec['alt']}](images/{spec['filename']})\n*{spec['caption']}*"
        md = md.replace(spec["placeholder"], img_md)

    filename = f"{_safe_slug(plan.system_title)}.md"
    Path(filename).write_text(md, encoding="utf-8")
    return {"final": md}

def _safe_slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9 _-]+", "", title.strip().lower())
    return re.sub(r"\s+", "_", s).strip("_") or "system_doc"