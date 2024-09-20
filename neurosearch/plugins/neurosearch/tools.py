import httpx
from xml.etree import ElementTree as ET
from zyte_api import AsyncZyteAPI
from dateutil import parser
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import hashlib
from .config import Config


class CrawlSitemap:
    @staticmethod
    async def _fetch_sitemap(sitemap_url):
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            response = await client.get(sitemap_url)
            response.raise_for_status()  # 确保请求成功
            return response.text

    @staticmethod
    def _get_namespace(root):
        # 提取根元素的命名空间
        if "}" in root.tag:
            return {"ns": root.tag.split("}")[0].strip("{")}
        return {}

    @staticmethod
    def _parse_sitemap(sitemap_content):
        root = ET.fromstring(sitemap_content)
        namespace = CrawlSitemap._get_namespace(root)  # 动态获取命名空间

        sitemap_data = []
        sitemaps_to_follow = []

        # 检查是否是sitemap index类型
        if root.tag.endswith("sitemapindex"):
            for sitemap in root.findall("ns:sitemap", namespace):
                loc = sitemap.findtext("ns:loc", namespaces=namespace)
                if loc:
                    sitemaps_to_follow.append(loc)
        elif root.tag.endswith("urlset"):
            # 如果是urlset，则提取所有url
            for url in root.findall("ns:url", namespace):
                url_data = {
                    "loc": url.findtext("ns:loc", default="", namespaces=namespace),
                    "changefreq": url.findtext(
                        "ns:changefreq", default="", namespaces=namespace
                    ),
                    "lastmod": url.findtext(
                        "ns:lastmod", default="", namespaces=namespace
                    ),
                    "priority": url.findtext(
                        "ns:priority", default="", namespaces=namespace
                    ),
                }
                sitemap_data.append(url_data)

        return sitemap_data, sitemaps_to_follow

    @staticmethod
    async def crawl_sitemaps(sitemap_url, crawled_sitemaps=None):
        if crawled_sitemaps is None:
            crawled_sitemaps = set()

        # 防止重复爬取相同的sitemap
        if sitemap_url in crawled_sitemaps:
            return []

        crawled_sitemaps.add(sitemap_url)

        sitemap_content = await CrawlSitemap._fetch_sitemap(sitemap_url)
        sitemap_data, sitemaps_to_follow = CrawlSitemap._parse_sitemap(sitemap_content)

        for sitemap in sitemaps_to_follow:
            child_sitemap_data = await CrawlSitemap.crawl_sitemaps(
                sitemap, crawled_sitemaps
            )
            sitemap_data.extend(child_sitemap_data)

        return sitemap_data


async def fetch_article_content(url: str) -> dict:
    client = AsyncZyteAPI(api_key=Config.get_zyte_api_key())
    api_response = await client.get(
        {
            "url": url,
            "article": True,
            "articleOptions": {"extractFrom": "httpResponseBody"},
        }
    )
    article = api_response["article"]
    return article


async def convert_article_to_documents(
    article: dict,
) -> Tuple[List[Document], List[str]]:
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。"],
        chunk_size=1024,
        chunk_overlap=128,
        keep_separator=False,
    )
    article_body_chunks = text_splitter.split_text(article["articleBody"])
    documents = []
    ids = []

    for index, chunk in enumerate(article_body_chunks):
        ids.append(hashlib.md5(f"{article['url']}-{index}".encode()).hexdigest())
        document = Document(
            page_content=chunk,
            metadata={
                "headline": article.get("headline", ""),
                "articleBody": article.get("articleBody", ""),
                "description": article.get("description", ""),
                "authors": article.get("authors", [{}])[0].get("name", ""),
                "url": article.get("url", ""),
                "datePublished": (
                    parser.parse(article.get("datePublished", "")).timestamp()
                    if article.get("datePublished")
                    else 0
                ),
                "mainImage": article.get("mainImage", {}).get("url", ""),
                "probability": article.get("metadata", {}).get("probability", 0),
                "dateDownloaded": (
                    parser.parse(
                        article.get("metadata", {}).get("dateDownloaded", "")
                    ).timestamp()
                    if article.get("metadata", {}).get("dateDownloaded")
                    else 0
                ),
                "articleBodyHtml": article.get("articleBodyHtml", ""),
            },
        )
        documents.append(document)
    return documents, ids
