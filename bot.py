# -*- coding: utf-8 -*-
import asyncio
import sys
from khl import Bot, Message
from datetime import datetime
import json
import os
import logging
import traceback

# === 日志配置 ===
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KOOK_FINAL')

class FinalBot:
    def __init__(self):
        logger.info("初始化机器人...")
        try:
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            self.token = os.getenv("KOOK_BOT_TOKEN")  # 使用环境变量
            self.guild_id = '5740039039454104'
            self.role_hierarchy = [
                {'id': '51890997', 'req': 5,  'name': '活跃用户Lv.1'},
                {'id': '51891015', 'req': 15, 'name': '活跃用户Lv.2'},
                {'id': '51891022', 'req': 30, 'name': '活跃用户Lv.3'},
                {'id': '51891025', 'req': 50, 'name': '活跃用户Lv.4'},
                {'id': '51891032', 'req': 80, 'name': '活跃用户Lv.5'}
            ]
            self.data_file = 'activity_final.json'
            self.admin_id = "您的管理员用户ID"

            self.bot = Bot(token=self.token)
            self._register_handlers()

        except Exception as e:
            logger.critical(f"初始化失败: {repr(e)}")
            raise

    def _register_handlers(self):
        @self.bot.on_message()
        async def _on_message(msg: Message):
            try:
                if msg.author.bot:
                    return

                data = self._load_data()
                user_id = msg.author_id
                today = datetime.now().strftime('%Y-%m-%d')

                if 'daily' not in data:
                    data['daily'] = {}
                if today not in data['daily']:
                    data['daily'][today] = {}

                last_msg_time = data['daily'][today].get(f'{user_id}_time', 0)
                if datetime.now().timestamp() - last_msg_time < 60:
                    return

                data['daily'][today][user_id] = data['daily'][today].get(user_id, 0) + 1
                data['daily'][today][f'{user_id}_time'] = datetime.now().timestamp()
                daily_count = data['daily'][today][user_id]

                # 获取完整成员信息来读取角色
                guild = await self.bot.client.fetch_guild(self.guild_id)
                member = await guild.fetch_member(user_id)
                current_roles = [str(role) for role in member.roles]

                target_level = None
                for role in reversed(self.role_hierarchy):
                    if daily_count >= role['req']:
                        target_level = role
                        break

                if target_level:
                    for role in self.role_hierarchy:
                        if role['id'] in current_roles and role['id'] != target_level['id']:
                            try:
                                await guild.revoke_role(user_id, int(role['id']))
                                logger.info(f"移除用户 {user_id} 的冲突角色 {role['name']}")
                            except Exception as e:
                                logger.error(f"移除角色失败: {repr(e)}")

                    if target_level['id'] not in current_roles:
                        try:
                            await guild.grant_role(user_id, int(target_level['id']))
                            logger.info(f"✅ 用户 {user_id} 设置为 {target_level['name']}（发言 {daily_count} 次）")
                            await msg.reply(f"🎉 您当前等级：{target_level['name']}")
                        except Exception as e:
                            logger.error(f"授予角色失败: {repr(e)}")

                self._save_data(data)

            except Exception as e:
                logger.error(f"消息处理错误: {repr(e)}")
                await self._notify_admin(f"消息处理错误: {e}")

        @self.bot.command()
        async def fixroles(ctx: Message):
            try:
                if ctx.author.id != self.admin_id:
                    return

                guild = await self.bot.client.fetch_guild(self.guild_id)
                member = await self.bot.client.fetch_guild_member(self.guild_id, user_id)

                fixed = 0
                for member in members:
                    data = self._load_data()
                    today = datetime.now().strftime('%Y-%m-%d')
                    count = data.get('daily', {}).get(today, {}).get(member.id, 0)

                    target_role_id = None
                    for role in reversed(self.role_hierarchy):
                        if count >= role['req']:
                            target_role_id = role['id']
                            break

                    if target_role_id:
                        current_roles = [str(r) for r in member.roles]
                        for role in self.role_hierarchy:
                            if role['id'] in current_roles and role['id'] != target_role_id:
                                await guild.revoke_role(member.id, int(role['id']))
                                logger.info(f"修复移除 {member.username} 的 {role['name']}")
                        if target_role_id not in current_roles:
                            await guild.grant_role(member.id, int(target_role_id))
                            logger.info(f"修复授予 {member.username} 等级角色")
                        fixed += 1

                await ctx.reply(f"✅ 已修复 {fixed} 名用户的角色")
            except Exception as e:
                logger.error(f"修复角色失败: {repr(e)}")

    async def _notify_admin(self, msg: str):
        try:
            user = await self.bot.client.fetch_user(self.admin_id)
            await user.send(f"🤖 机器人告警:\n{msg}")
        except Exception as e:
            logger.error(f"通知失败: {repr(e)}")

    def _load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"数据加载失败: {repr(e)}")
            return {}

    def _save_data(self, data):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"数据保存失败: {repr(e)}")

async def main():
    try:
        bot = FinalBot()
        await bot.bot.start()
    except Exception as e:
        logger.critical(f"主程序崩溃: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    print("""
================================
 🚀 KOOK机器人-等级系统终极修复版
 修复内容：
 1. 严格单等级制度（每次只保留最高等级）
 2. 防刷消息计数（每分钟最多计1次）
 3. 新增 /fixroles 修复命令
================================
""")

    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序已终止")
    except Exception as e:
        print(f"致命错误: {repr(e)}")
