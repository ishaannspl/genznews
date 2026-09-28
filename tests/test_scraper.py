from unittest.mock import Mock, patch

import pytest
import requests

from app.scraper import ArticleExtractionError, InvalidURLError, scrape_article


ARTICLE_TEXT = (
    "A major city announced a new public transit project today. "
    "Officials said construction will begin next year and the project will "
    "connect several neighborhoods with faster service. "
) * 3


def test_invalid_url_is_rejected():
    with pytest.raises(InvalidURLError, match="http"):
        scrape_article("not-a-url")


@patch("app.scraper.trafilatura.extract_metadata")
@patch("app.scraper.trafilatura.extract")
@patch("app.scraper.requests.get")
def test_scraper_returns_clean_structured_article(
    mock_get, mock_extract, mock_metadata
):
    response = Mock()
    response.text = "<html><body>mock article</body></html>"
    mock_get.return_value = response
    mock_extract.return_value = f"\n\n{ARTICLE_TEXT}\n\n"
    mock_metadata.return_value = Mock(
        title="Transit project announced",
        author="Reporter",
        date="2026-09-25",
    )

    article = scrape_article("https://example.com/news/transit")

    assert article["domain"] == "example.com"
    assert article["title"] == "Transit project announced"
    assert article["author"] == "Reporter"
    assert article["published_at"] == "2026-09-25"
    assert article["content"].startswith("A major city")
    mock_get.assert_called_once()
    assert mock_get.call_args.kwargs["headers"]["User-Agent"]


@patch("app.scraper.requests.get")
def test_scraper_http_failure_is_reported(mock_get):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError(
        response=Mock(status_code=404)
    )
    mock_get.return_value = response

    with pytest.raises(Exception, match="404"):
        scrape_article("https://example.com/missing")


@patch("app.scraper.trafilatura.extract")
@patch("app.scraper.requests.get")
def test_scraper_rejects_short_extraction(mock_get, mock_extract):
    response = Mock()
    response.text = "<html></html>"
    mock_get.return_value = response
    mock_extract.return_value = "Too short"

    with pytest.raises(ArticleExtractionError, match="too little"):
        scrape_article("https://example.com/empty")
