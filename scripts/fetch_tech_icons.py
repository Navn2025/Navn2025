"""Vendor real Devicon and Simple Icons brand marks with source attribution."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "profile" / "icons"
VERSION = "v2.17.0"
BASE = f"https://raw.githubusercontent.com/devicons/devicon/{VERSION}"
SIMPLE_REVISION = "90646e4bf7f3b89df6c37e65baf3e7bc759a517c"
SIMPLE_BASE = f"https://raw.githubusercontent.com/simple-icons/simple-icons/{SIMPLE_REVISION}"
TECH = [("python", "Python"), ("javascript", "JavaScript"), ("typescript", "TypeScript"),
        ("java", "Java"), ("react", "React"), ("nextjs", "Next.js"),
        ("nodejs", "Node.js"), ("express", "Express"), ("fastapi", "FastAPI"),
        ("postgresql", "PostgreSQL"), ("mysql", "MySQL"), ("redis", "Redis"),
        ("mongodb", "MongoDB"), ("docker", "Docker"), ("git", "Git"),
        ("github", "GitHub"), ("linkedin", "LinkedIn"), ("linux", "Linux"), ("tailwindcss", "Tailwind CSS")]
AI = [("langchain","LangChain"),("langgraph","LangGraph"),("modelcontextprotocol","MCP"),
      ("huggingface","Hugging Face"),("ollama","Ollama"),("googlegemini","Gemini"),
      ("scikitlearn","scikit-learn"),("numpy","NumPy"),("pandas","Pandas"),("opencv","OpenCV")]


def download(item):
    slug, label = item
    url = f"{BASE}/icons/{slug}/{slug}-original.svg"
    with urlopen(Request(url, headers={"User-Agent": "Navn2025-profile-art"}), timeout=30) as response:
        (ICONS / f"{slug}.svg").write_bytes(response.read())
    return {"slug": slug, "label": label, "source": url}


def main():
    ICONS.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        manifest = list(pool.map(download, TECH))
    for slug,label,filename in [("aws","AWS","amazonwebservices/amazonwebservices-original-wordmark.svg"),
                                ("githubactions","GitHub Actions","githubactions/githubactions-original.svg")]:
        url = f"{BASE}/icons/{filename}"
        with urlopen(url,timeout=30) as response:
            (ICONS/f"{slug}.svg").write_bytes(response.read())
        manifest.append({"slug":slug,"label":label,"source":url})
    with urlopen(f"{SIMPLE_BASE}/data/simple-icons.json",timeout=30) as response:
        metadata = json.load(response)
    items = metadata.get("icons",[]) if isinstance(metadata,dict) else metadata
    title_lookup = {item["title"].lower():item for item in items}
    titles = {"modelcontextprotocol":"Model Context Protocol","googlegemini":"Google Gemini","pandas":"pandas"}
    for slug,label in [*AI,("leetcode","LeetCode")]:
        title = titles.get(slug,label)
        brand = title_lookup[title.lower()]
        url = f"{SIMPLE_BASE}/icons/{slug}.svg"
        with urlopen(url,timeout=30) as response:
            (ICONS/f"{slug}.svg").write_bytes(response.read())
        manifest.append({"slug":slug,"label":label,"source":url,"brand_source":brand["source"],
                         "color":"#"+brand["hex"],"library":"Simple Icons"})
    (ICONS / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    with urlopen(f"{BASE}/LICENSE", timeout=30) as response:
        (ICONS / "LICENSE").write_bytes(response.read())
    with urlopen(f"{SIMPLE_BASE}/LICENSE.md",timeout=30) as response:
        (ICONS / "SIMPLE-ICONS-LICENSE.md").write_bytes(response.read())
    print(f"Vendored {len(manifest)} genuine brand SVGs with pinned sources and licenses.")


if __name__ == "__main__":
    main()
