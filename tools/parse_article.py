import sys
import json

def parse_article(text: str):
    """Simple parser for demo purposes."""
    lines = text.strip().splitlines()
    title = lines[0].replace("Title:", "").strip()
    author = lines[1].replace("Author:", "").strip()
    date = lines[2].replace("Date:", "").strip()
    body = "\n".join(lines[4:]).strip()

    return {
        "title": title,
        "author": author,
        "date": date,
        "body": body
    }

def parse_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return parse_article(f.read())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_article.py <file>")
        sys.exit(1)

    output = parse_file(sys.argv[1])
    print(json.dumps(output, indent=2))
