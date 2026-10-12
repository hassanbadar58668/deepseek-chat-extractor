import re
from collections import Counter
from .parser import get_messages


PATH_RE = re.compile(
    r"\b[\w\-./]+\.(?:py|js|ts|jsx|tsx|json|yaml|yml|md|txt|toml|ini|cfg|env|sh|sql|html|css|xml|go|rs|java|c|cpp|h|rb|php)\b"
)
TREE_RE = re.compile(r"[├└│]")


def extract_paths(data: dict) -> list[str]:
    paths = set()
    for m in get_messages(data):
        for f in m.get("fragments", []):
            c = f.get("content") or ""
            for match in PATH_RE.findall(c):
                if not match.startswith("http"):
                    paths.add(match)
    return sorted(paths)


def extract_tree(data: dict) -> list[str]:
    lines = []
    for m in get_messages(data):
        for f in m.get("fragments", []):
            c = f.get("content") or ""
            for line in c.splitlines():
                if TREE_RE.search(line):
                    lines.append(line.rstrip())
    return lines


def extract_keywords(data: dict, top: int = 30) -> list[tuple[str, int]]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "have", "are",
        "was", "were", "you", "your", "can", "will", "not", "but", "all",
        "one", "two", "use", "get", "set", "when", "how", "what", "why",
        "من", "في", "على", "إلى", "عن", "أن", "هو", "هي", "ما", "لا", "مع",
        "كل", "بس", "ده", "دي", "إن", "لو", "كان", "هذا", "هذه", "اللي",
    }
    words = Counter()
    for m in get_messages(data):
        for f in m.get("fragments", []):
            c = f.get("content") or ""
            c = re.sub(r"```.*?```", "", c, flags=re.DOTALL)
            for w in re.findall(r"[\w\u0600-\u06FF]+", c.lower()):
                if len(w) > 2 and w not in stop and not w.isdigit():
                    words[w] += 1
    return words.most_common(top)


def search_in_messages(data: dict, keyword: str) -> list[tuple[int, str, str]]:
    kw = keyword.lower()
    hits = []
    for i, m in enumerate(get_messages(data)):
        role = m.get("role", "?")
        for f in m.get("fragments", []):
            c = f.get("content") or ""
            if kw in c.lower():
                pos = c.lower().find(kw)
                snippet = c[max(0, pos - 80):pos + len(kw) + 80]
                hits.append((i, role, snippet.replace("\n", " ")))
    return hits
