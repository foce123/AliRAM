
import re
from typing import Dict

from loguru import logger
import tomllib

from WechatAPI import WechatAPIClient
from utils.decorators import on_at_message
from utils.plugin_base import PluginBase

from xpinyin import Pinyin
from alibabacloud_ims20190815.client import Client as Ims20190815Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ims20190815 import models as ims_20190815_models
from alibabacloud_tea_util import models as util_models


class AliRAM(PluginBase):
    """
    一个用于查询、创建、删除等管理阿里云 RAM 用户信息的插件，
    将分析结果返回到微信。
    """

    description = "RAM用户管理"
    author = "柏煊"
    version = "1.0.0"

    # 分析命令的正则表达式
    COMMAND_PATTERN = r'^(aliaccount)\s*(query|create|delete|modify)\s*(.+)$'

    def __init__(self):
        super().__init__()
        self.name = "AliRAM"
        self.description = "阿里云RAM账号管理插件"
        self.version = "1.0.0"
        self.author = "柏煊"
        
        # 添加logger
        self.logger = logger  # 从loguru导入的loggerl
        
        with open("plugins/AliRAM/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)
            logger.info("插件配置文件加载成功")
        config = plugin_config["AliAccount"]
        self.enable = config["enable"]
        self.ak = config["ak"]
        self.sk = config["sk"]
    
    def topinyin(self, name):
        """
        将汉字转换为拼音
        """
        p = Pinyin()
        ostring = p.get_pinyin(name)
        fname = ostring.replace('-', '')
        return fname

    def create_client(self) -> Ims20190815Client:
        config = open_api_models.Config(
            access_key_id=self.ak,
            access_key_secret=self.sk
        )
        config.endpoint = f'ims.aliyuncs.com'
        return Ims20190815Client(config)

    def query(self, name) -> bool:
        client = self.create_client()
        get_user_request = ims_20190815_models.GetUserRequest(
            user_principal_name=name
        )
        runtime = util_models.RuntimeOptions()
        try:
            client.get_user_with_options(get_user_request, runtime)
            return True
        except:
            return False
    
    def create(self, name, dname) -> bool:
        client = self.create_client()
        create_user_request = ims_20190815_models.CreateUserRequest(
            user_principal_name=name,
            display_name=dname
        )
        runtime = util_models.RuntimeOptions()
        try:
            client.create_user_with_options(create_user_request, runtime)
            return True
        except:
            return False
    
    @on_text_message
    async def handle_text_message(self) -> bool:
        """处理文本消息，检查是否包含指令，并解析命令。"""
        return True  # 不是该插件的指令，允许其他插件处理
    
    @on_at_message
    async def handle_at_message(self, bot: WechatAPIClient, message: Dict) -> bool:
        """处理@消息，检查是否包含指令，并解析命令。"""
        if not self.enable:
            return True  # 插件未启用，允许其他插件处理
            
        chat_id = message["FromWxid"]
        content = message["Content"]
        
        # 移除@标记和特殊字符，仅保留实际文本内容
        # 注意：这里可能需要根据实际的@消息格式进行调整
        content = re.sub(r'@\S+\s+', '', content).strip()
        logger.info(content)
        
        # 检查是否为正确指令
        match = re.match(self.COMMAND_PATTERN, content)
        if match:
            cname, optname, oname = match.groups()
            if ' ' in oname and optname != "modify":
                oname = oname.split(' ')[0]
            if cname == "aliaccount":
                if optname == "query":
                    logger.info("查询用户")
                    aname = self.topinyin(oname) + '@1459359830040602.onaliyun.com'
                    if self.query(aname):
                        await bot.send_text_message(chat_id, str(aname) + "该用户已存在")
                        logger.info(str(aname) + "该用户已存在")
                    else:
                        await bot.send_text_message(chat_id, str(aname) +"该用户不存在")
                        logger.info(str(aname) +"该用户不存在")
                elif optname == "create":
                    logger.info("创建用户")
                    aname = self.topinyin(oname) + '@1459359830040602.onaliyun.com'
                    if self.query(aname):
                        logger.info("该用户已存在")
                        await bot.send_text_message(chat_id, str(aname) + "该用户已存在,不创建")
                    else:
                        logger.info("该用户不存在，创建用户")
                        self.create(aname, oname)
                        await bot.send_text_message(chat_id, "创建用户成功:  " + str(oname) + "  " + str(aname))
            
        return True  # 不是该插件的指令，允许其他插件处理

