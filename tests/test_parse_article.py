import json
from tools.parse_article import parse_file

def test_parse_article_basic():
    data = parse_file("tests/fixtures/sample_article.txt")

    assert "title" in data
    assert "author" in data
    assert "date" in data
    assert "body" in data

    assert data["title"] == "Sample Title"
    assert "This is the first paragraph" in data["body"]
