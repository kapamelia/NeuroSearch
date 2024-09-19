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

from .conversational_rag_chain import conversational_rag_chain


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
    print(result)
    
    
        
