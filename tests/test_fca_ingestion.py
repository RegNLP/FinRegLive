from backend.ingestion.fca import extract_fca_item_urls, is_fca_item_path


def test_is_fca_item_path_accepts_news_items() -> None:
    assert is_fca_item_path(
        "/news/press-releases/fca-consults-targeted-changes-listing-rules"
    )


def test_is_fca_item_path_rejects_news_category_pages() -> None:
    assert not is_fca_item_path("/news/press-releases/press-releases")
    assert not is_fca_item_path("/news/news-stories/media-library")
    assert not is_fca_item_path("/news")


def test_is_fca_item_path_accepts_publication_items() -> None:
    assert is_fca_item_path("/publications/consultation-papers/cp26-21-example")


def test_is_fca_item_path_rejects_publication_search_pages() -> None:
    assert not is_fca_item_path("/publications/search-results")


def test_extract_fca_item_urls_keeps_unique_item_urls() -> None:
    html = """
    <a href="/news">News</a>
    <a href="/news/press-releases/press-releases">Press releases</a>
    <a href="/news/press-releases/example-update">Example update</a>
    <a href="https://www.fca.org.uk/news/press-releases/example-update">Duplicate</a>
    <a href="/publications/search-results">Search</a>
    <a href="/publications/consultation-papers/cp26-21-example">CP26/21</a>
    <a href="https://example.com/news/press-releases/outside">Outside</a>
    """

    urls = extract_fca_item_urls(html, "https://www.fca.org.uk/news")

    assert urls == [
        "https://www.fca.org.uk/news/press-releases/example-update",
        "https://www.fca.org.uk/publications/consultation-papers/cp26-21-example",
    ]
