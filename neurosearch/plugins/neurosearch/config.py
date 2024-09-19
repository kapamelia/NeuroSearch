from nonebot import get_driver

class Config:
    @staticmethod
    def get_dashscope_api_key():
        return get_driver().config.dashscope_api_key

    @staticmethod
    def get_weaviate_host():
        return get_driver().config.weaviate_host
