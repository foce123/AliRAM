
import re
from typing import Dict

from loguru import logger
import tomllib
import random
import string

from WechatAPI import WechatAPIClient
from utils.decorators import on_at_message, on_text_message
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
    version = "1.0.3"

    # 分析命令的正则表达式
    COMMAND_PATTERN = r'^(aliaccount)\s*(query|create|delete|update)\s*(.+)$'

    def __init__(self):
        super().__init__()
        self.name = "AliRAM"
        self.description = "阿里云RAM账号管理插件"
        self.version = "1.0.3"
        self.author = "柏煊"
        
        # 添加logger
        self.logger = logger  # 从loguru导入的loggerl
        
        with open("plugins/AliRAM/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)
            logger.info("插件配置文件加载成功")
        config = plugin_config["AliAccount"]
        self.enable = config["enable"]
        self.id = config["id"]
        self.ak = config["ak"]
        self.sk = config["sk"]
        self.admins = config["admins"]
    
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
            res = client.get_user_with_options(get_user_request, runtime).to_map()
            if res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
    
    def create(self, name, dname) -> bool:
        client = self.create_client()
        create_user_request = ims_20190815_models.CreateUserRequest(
            user_principal_name=name,
            display_name=dname
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.create_user_with_options(create_user_request, runtime).to_map()
            if res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
    
    def delete(self, name) -> bool:
        client = self.create_client()
        delete_user_request = ims_20190815_models.DeleteUserRequest(
            user_principal_name=name
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.delete_user_with_options(delete_user_request, runtime).to_map()
            if  res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
    
    def modify(self, name, dname) -> bool:
        pass
    
    def activename(self, name, password) -> bool:
        client = self.create_client()
        create_login_profile_request = ims_20190815_models.CreateLoginProfileRequest(
            user_principal_name=name,
            password=password,
            password_reset_required=True
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            res = client.create_login_profile_with_options(create_login_profile_request, runtime).to_map()
            if res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"激活用户失败: {e}")
    
    def updatepassword(self, name, password) -> bool:
        client = self.create_client()
        update_login_profile_request = ims_20190815_models.UpdateLoginProfileRequest(
            user_principal_name=name,
            password=password,
            password_reset_required=True
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.update_login_profile_with_options(update_login_profile_request, runtime).to_map()
            if res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"更新用户密码失败: {e}")
    
    def updateuser(self, name, sname, dname) -> bool:
        client = self.create_client()
        update_user_request = ims_20190815_models.UpdateUserRequest(
            user_principal_name=name,
            new_user_principal_name=sname,
            new_display_name=dname
        )
        runtime = util_models.RuntimeOptions()
        try:
            res = client.update_user_with_options(update_user_request, runtime).to_map()
            if res["status_code"] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
    
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
            if ' ' in oname and optname != "update":
                oname = oname.split(' ')[0]
            elif ' ' in oname and optname == "update":
                sname = oname.split(' ')[0]
                oname = oname.split(' ')[1]
                if sname.strip() == "user":
                    lname = oname.split(' ')[2]
            if cname == "aliaccount" and message["SenderWxid"] in self.admins:
                if optname == "query":
                    logger.info("查询用户")
                    aname = self.topinyin(oname) + '@' + self.id +'.onaliyun.com'
                    if self.query(aname):
                        await bot.send_text_message(chat_id, str(aname) + "该用户已存在")
                        logger.info(str(aname) + "该用户已存在")
                    else:
                        await bot.send_text_message(chat_id, str(aname) +"该用户不存在")
                        logger.info(str(aname) +"该用户不存在")
                elif optname == "create":
                    logger.info("创建用户")
                    aname = self.topinyin(oname) + '@' + self.id +'.onaliyun.com'
                    if self.query(aname):
                        logger.info("该用户已存在")
                        await bot.send_text_message(chat_id, str(aname) + "该用户已存在,不创建")
                    else:
                        logger.info("该用户不存在，创建用户")
                        if self.create(aname, oname):
                            await bot.send_text_message(chat_id, "创建用户成功:  " + str(oname) + "  " + str(aname))
                            logger.info("创建用户成功:  " + str(oname) + "  " + str(aname))
                            password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
                            if self.activename(aname, password):
                                await bot.send_text_message(chat_id, "登录名称:" + str(aname) + "\n" + "新密码:" + str(password))
                            else:
                                logger.info("用户启用失败:  " + str(oname) + "  " + str(aname))
                        else:
                            logger.info("创建用户失败:  " + str(oname) + "  " + str(aname))
                            await bot.send_text_message(chat_id, "创建用户失败")
                elif optname == "delete":
                    logger.info("删除用户")
                    aname = self.topinyin(oname) + '@' + self.id +'.onaliyun.com'
                    if self.query(aname):
                        logger.info("该用户存在，开始删除用户")
                        if self.delete(aname):
                            await bot.send_text_message(chat_id, "删除用户成功:  " + str(oname) + "  " + str(aname))
                elif optname == "update":
                    logger.info("更新操作")
                    aname = self.topinyin(oname) + '@' + self.id +'.onaliyun.com'
                    if sname == "password":
                        logger.info("更新密码")
                        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
                        if self.query(aname):
                            logger.info("该用户存在，开始更新该用户密码")
                            await bot.send_text_message(chat_id, "开始更新" + str(oname) + "用户密码")
                            if self.updatepassword(aname, password):
                                await bot.send_text_message(chat_id, "登录名称:" + str(aname) + "\n" + "新密码:" + str(password))
                        else:
                            logger.info("该用户不存在，无法更新该用户密码")
                    elif sname == "user":
                        logger.info("更新用户信息")
                        aname = self.topinyin(oname) + '@' + self.id +'.onaliyun.com'
                        if self.query(aname):
                            logger.info("该用户存在，开始更新该用户信息")
                            await bot.send_text_message(chat_id, "开始更新" + str(oname) + "用户信息")
                            laname = self.topinyin(lname)+ '@' + self.id +'.onaliyun.com'
                            if self.updateuser(aname, laname, lname):
                                await bot.send_text_message(chat_id, "更新用户信息成功")
                                password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
                                if self.updatepassword(laname, password):
                                    await bot.send_text_message(chat_id, "登录名称:" + str(laname) + "\n" + "新密码:" + str(password))
            else:
                logger.info("权限不足")
                await bot.send_text_message(chat_id, "你没有权限使用此命令")
            
        return True  # 不是该插件的指令，允许其他插件处理
