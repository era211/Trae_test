"""Web crawler for Xinjiang Daily and similar news sources."""
import re
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class NewsCrawler:
    """Crawler for news websites like Xinjiang Daily."""

    def __init__(self, base_url: str, source_name: str = "新疆日报", delay: float = 1.0):
        self.base_url = base_url
        self.source_name = source_name
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.visited_urls = set()
        self.extracted_sentences: List[Dict] = []

    def _delay(self):
        """Add delay between requests to be polite."""
        time.sleep(self.delay + random.uniform(0, 0.5))

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object."""
        if url in self.visited_urls:
            return None
        self.visited_urls.add(url)

        try:
            self._delay()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_article_urls(self, page_url: str) -> List[str]:
        """Extract article URLs from a list page."""
        soup = self._get_page(page_url)
        if not soup:
            return []

        article_urls = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(page_url, href)

            if self._is_article_url(full_url):
                article_urls.append(full_url)

        return list(set(article_urls))

    def _is_article_url(self, url: str) -> bool:
        """Check if URL looks like an article page."""
        parsed = urlparse(url)

        if not parsed.netloc:
            return False

        article_patterns = [
            r"/article/",
            r"/news/",
            r"/content/",
            r"/detail/",
            r"/\d{4}/\d{2,4}/",
            r"\d{8,}",
        ]

        for pattern in article_patterns:
            if re.search(pattern, parsed.path):
                return True

        return False

    def extract_article_content(self, url: str) -> Optional[Dict]:
        """Extract title, content, and metadata from an article page."""
        soup = self._get_page(url)
        if not soup:
            return None

        title = self._extract_title(soup)
        content = self._extract_main_content(soup)
        publish_time = self._extract_publish_time(soup)
        category = self._extract_category(soup)

        if not content or len(content.strip()) < 50:
            return None

        return {
            "url": url,
            "title": title,
            "content": content,
            "publish_time": publish_time,
            "category": category,
            "source": self.source_name,
            "crawled_at": datetime.utcnow().isoformat(),
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        title_selectors = [
            "h1",
            ".title",
            ".article-title",
            ".news-title",
            "[class*='title']",
            "title",
        ]

        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                return elem.text.strip()

        return ""

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        content_selectors = [
            ".content",
            ".article-content",
            ".news-content",
            "#content",
            "[class*='content']",
            "article",
            ".detail",
            ".text",
        ]

        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                paragraphs = elem.find_all("p")
                if paragraphs:
                    content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
                    if len(content) > 100:
                        return content

                text = elem.text.strip()
                if len(text) > 100:
                    return text

        all_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in all_text.split("\n") if line.strip()]
        if lines:
            return "\n".join(lines[3:15]) if len(lines) > 3 else ""

        return ""

    def _extract_publish_time(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish time from article."""
        time_patterns = [
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"\d{4}-\d{2}-\d{2}",
            r"\d{4}/\d{2}/\d{2}",
        ]

        time_selectors = [
            ".time",
            ".publish-time",
            ".article-time",
            "[class*='time']",
            "[class*='date']",
        ]

        for selector in time_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.text
                for pattern in time_patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group()

        all_text = soup.get_text()
        for pattern in time_patterns:
            match = re.search(pattern, all_text)
            if match:
                return match.group()

        return None

    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article category/section."""
        category_selectors = [
            ".category",
            ".section",
            ".column",
            "[class*='category']",
            "[class*='section']",
        ]

        for selector in category_selectors:
            elem = soup.select_one(selector)
            if elem and elem.text.strip():
                return elem.text.strip()

        breadcrumb = soup.select_one(".breadcrumb, .nav, [class*='crumb']")
        if breadcrumb:
            links = breadcrumb.find_all("a")
            if len(links) >= 2:
                return links[-2].text.strip()

        return None

    def extract_sentences_from_article(self, article: Dict) -> List[Dict]:
        """Extract individual sentences from article content."""
        sentences = self._split_into_sentences(article["content"])

        results = []
        for i, sentence in enumerate(sentences):
            if len(sentence) >= 10 and len(sentence) <= 500:
                results.append({
                    "content": sentence,
                    "source": article["source"],
                    "source_url": article["url"],
                    "metadata": {
                        "article_title": article["title"],
                        "article_category": article["category"],
                        "publish_time": article["publish_time"],
                        "sentence_index": i,
                        "total_sentences": len(sentences),
                    }
                })

        return results

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split Chinese text into sentences."""
        sentence_endings = r"[。！？!?\n]+"
        sentences = re.split(sentence_endings, text)

        cleaned_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if sent:
                sent = re.sub(r"\s+", " ", sent)
                if len(sent) >= 5:
                    cleaned_sentences.append(sent)

        return cleaned_sentences

    def crawl_list_pages(self, list_urls: List[str], max_pages: int = 10) -> List[str]:
        """Crawl multiple list pages and extract article URLs."""
        all_article_urls = []

        for list_url in list_urls:
            print(f"Crawling list page: {list_url}")
            urls = self.extract_article_urls(list_url)
            all_article_urls.extend(urls)
            print(f"Found {len(urls)} article URLs from this page")

            if len(all_article_urls) >= max_pages * 20:
                break

        return list(set(all_article_urls))

    def crawl_articles(self, article_urls: List[str], max_articles: int = 100) -> List[Dict]:
        """Crawl articles and extract content."""
        articles = []

        for i, url in enumerate(article_urls[:max_articles]):
            print(f"Crawling article {i+1}/{min(len(article_urls), max_articles)}: {url}")
            article = self.extract_article_content(url)
            if article:
                articles.append(article)

        return articles

    def run_crawl(self, list_urls: List[str], max_articles: int = 100) -> Dict:
        """Run complete crawl process."""
        result = {
            "list_pages_crawled": len(list_urls),
            "article_urls_found": 0,
            "articles_crawled": 0,
            "sentences_extracted": 0,
            "articles": [],
            "sentences": [],
        }

        print("Step 1: Extracting article URLs from list pages...")
        article_urls = self.crawl_list_pages(list_urls)
        result["article_urls_found"] = len(article_urls)
        print(f"Total article URLs found: {len(article_urls)}")

        if not article_urls:
            print("No article URLs found.")
            return result

        print("\nStep 2: Crawling articles...")
        articles = self.crawl_articles(article_urls, max_articles)
        result["articles_crawled"] = len(articles)
        result["articles"] = articles
        print(f"Total articles crawled: {len(articles)}")

        print("\nStep 3: Extracting sentences from articles...")
        all_sentences = []
        for article in articles:
            sentences = self.extract_sentences_from_article(article)
            all_sentences.extend(sentences)

        result["sentences_extracted"] = len(all_sentences)
        result["sentences"] = all_sentences
        self.extracted_sentences = all_sentences
        print(f"Total sentences extracted: {len(all_sentences)}")

        return result


def crawl_xinjiang_daily(max_articles: int = 100) -> Dict:
    """Convenience function to crawl Xinjiang Daily."""
    base_url = "https://www.xjdaily.com.cn/"
    crawler = NewsCrawler(base_url, source_name="新疆日报", delay=1.5)

    list_pages = [
        "https://www.xjdaily.com.cn/",
        "https://www.xjdaily.com.cn/news/",
        "https://www.xjdaily.com.cn/politics/",
        "https://www.xjdaily.com.cn/economy/",
        "https://www.xjdaily.com.cn/culture/",
        "https://www.xjdaily.com.cn/society/",
    ]

    return crawler.run_crawl(list_pages, max_articles)


if __name__ == "__main__":
    result = crawl_xinjiang_daily(max_articles=20)
    print(f"\n=== Crawl Summary ===")
    print(f"Articles crawled: {result['articles_crawled']}")
    print(f"Sentences extracted: {result['sentences_extracted']}")

    if result["sentences"]:
        print("\nSample sentences:")
        for i, sent in enumerate(result["sentences"][:5]):
            print(f"{i+1}. {sent['content'][:80]}...")
