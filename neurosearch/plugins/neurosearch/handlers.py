from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageSegment,
    Message,
)
from nonebot.params import CommandArg
from typing import Union
import asyncio
import hashlib
from nonebot.log import logger

from .conversational_rag_chain import conversational_rag_chain
from .tools import CrawlSitemap, fetch_article_content, convert_article_to_documents
from .weaviate_client import WeaviateClient, WeaviateStoreClient

search = on_command("search", priority=5)


@search.handle()
async def search_handler(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    args: Message = CommandArg(),
):
    if not args:
        await search.finish("请输入要搜索的关键词~")
    keyword = args.extract_plain_text()
    result = await conversational_rag_chain.ainvoke({"input": keyword}, config={
        "configurable": {"session_id": event.user_id}
    })
    
    response = [MessageSegment.reply(event.message_id), result["answer"], "\n"]
    url_set = []

    for document in result["context"]:
        if document.metadata["url"] + "\n" not in url_set:
            url_set.append(document.metadata["url"] + "\n")

    await search.finish(response + url_set)
        
    

submit = on_command("submit", priority=5)

collection = WeaviateClient().get_collection("article_vector_index")
store_client = WeaviateStoreClient()

@submit.handle()
async def submit_handler(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    args: Message = CommandArg(),
):
    if not args:
        await submit.finish("请输入要索引的sitemap地址~")
    sitemap_url = args.extract_plain_text()
    
    async def process_url(url, semaphore):
        async with semaphore:
            id = hashlib.md5(f"{url['loc']}-0".encode()).hexdigest()
            result = await asyncio.to_thread(collection.query.fetch_object_by_id, uuid=id)
            if result:
                return 0  # 已存在，不需要处理
            
            article = await fetch_article_content(url["loc"])
            if article["metadata"]["probability"] < 0.5:
                return 0  # 文章的概率过低，跳过
            
            documents, ids = await convert_article_to_documents(article=article)
            await store_client.weaviate_vector_store.aadd_documents(documents, ids=ids)
            logger.info(f"索引了文章{article['url']}，分为了{len(documents)}个文档，可能性为{article['metadata']['probability']}")
            return 1  # 索引成功

    try:
        urls = await CrawlSitemap.crawl_sitemaps(sitemap_url)
        semaphore = asyncio.Semaphore(10)  # 限制并发任务数为10
        tasks = [process_url(url, semaphore) for url in urls]
        
        results = await asyncio.gather(*tasks)
        counter = sum(results)  # 统计成功索引的文章数量
        
    except Exception as e:
        await submit.finish(f"索引失败，错误信息：{type(e).__name__}: {str(e)}，共索引了{counter}篇文章")
    
    await submit.finish(f"索引完成，共索引了{counter}篇文章")