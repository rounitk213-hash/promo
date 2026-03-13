import asyncio
import os
import json
import random
import re
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError
from telethon.tl.types import User, Chat, Channel
import logging
import sys
import io
import nest_asyncio

# Windows specific fixes
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
nest_asyncio.apply()   # Fixed: added parentheses

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('userbot_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= CONFIGURATION =============
BOT_TOKEN = "8694998735:AAHoFfT4U4u1eqJXnuMOMRgGHl97EP9k8YI"
API_ID = 22091901
API_HASH = "54b0cd5fb47a40265b197f1a110b20b8"
ORIGINAL_ADMIN_IDS = [8104158848, 8514746265, 5393060599]  # Cannot be removed

# Folders
SESSIONS_DIR = "phone_sessions"
BACKUPS_DIR = "backups"
DATA_FILE = "userbot_data.json"

# Default settings
DEFAULT_BROADCAST_INTERVAL = 25
DEFAULT_DELAY_BETWEEN_MSGS = 1
# =========================================

# Sexy chat lines for tag auto-reply
SEXY_CHAT_LINES = [
    "**Hey there, gorgeous!**",
    "**You're looking absolutely stunning today!**",
    "**What's cooking, cutie?**",
    "**Feeling lucky today?**",
    "**You've got that special something...**",
    "**Ready to spark some magic?**",
    "**Looking for some fun? I'm here!**",
    "**Your vibe is unmatched!**",
    "**Ready to turn up the heat?**",
    "**You're the highlight of my day!**",
    "**Got plans? Let's make some!**",
    "**You're driving me crazy in the best way!**",
    "**Time to shine bright like you do!**",
    "**Ready to create some unforgettable moments?**",
    "**You're my favorite distraction!**",
    "**Let's write our story together!**",
    "**You're absolutely mesmerizing!**",
    "**Ready to explore new horizons?**",
    "**You bring out the best in me!**",
    "**Time to make some magic happen!**",
    "**You're the missing piece I was looking for!**",
    "**Ready to set the world on fire?**",
    "**You're simply irresistible!**",
    "**Time to make some sparks fly!**",
    "**You're my kind of trouble!**",
    "**Ready to dance through life?**",
    "**You're a masterpiece!**",
    "**Time to make some dreams come true!**",
    "**You're the star of my show!**",
    "**Ready to create some beautiful chaos?**",
    "**You're my happy place!**",
    "**Time to make some unforgettable memories!**",
    "**You're absolutely radiant!**",
    "**Ready to turn up the charm?**",
    "**You're the melody in my song!**",
    "**Time to make some beautiful noise!**",
    "**You're my daily dose of sunshine!**",
    "**Ready to paint the town red?**",
    "**You're my favorite kind of surprise!**",
    "**Time to make some beautiful waves!**",
    "**You're my heart's desire!**",
    "**Ready to make some beautiful music together?**",
    "**You're my sweetest temptation!**",
    "**Time to make some beautiful magic!**",
    "**You're my perfect match!**",
    "**Ready to make some beautiful dreams reality?**",
    "**You're my favorite obsession!**",
    "**Time to make some beautiful art!**",
    "**You're my precious gem!**",
    "**Ready to make some beautiful memories?**",
    "**You're my heartthrob!**",
    "**Time to make some beautiful moments!**",
    "**You're my favorite addiction!**",
    "**Ready to make some beautiful changes?**",
    "**You're my beautiful disaster!**",
    "**Time to make some beautiful connections!**",
    "**You're my favorite escape!**",
    "**Ready to make some beautiful impacts!**",
    "**You're my heart's delight!**",
    "**Time to make some beautiful transformations!**",
    "**You're my sweetest fantasy!**",
    "**Ready to make some beautiful breakthroughs!**",
    "**You're my favorite inspiration!**",
    "**Time to make some beautiful innovations!**",
    "**You're my heart's joy!**",
    "**Ready to make some beautiful adventures!**",
    "**You're my favorite dream!**",
    "**Time to make some beautiful discoveries!**",
    "**You're my heart's rhythm!**",
    "**some beautiful harmonies!**",
    "**You're my favorite vision!**",
    "**Ready to make some beautiful futures!**",
    "**You're my heart's symphony!**",
    "**Ready to make some beautiful realities!**",
    "**You're my favorite paradise!**",
    "**Time to make some beautiful wonders!**",
    "**You're my heart's paradise!**",
    "**Ready to make some beautiful miracles!**",
    "**You're my favorite galaxy!**",
    "**Time to make some beautiful stars!**",
    "**You're my heart's universe!**",
    "**Ready to make some beautiful cosmos!**",
    "**You're my favorite infinity!**",
    "**Time to make some beautiful eternities!**",
    "**You're my heart's eternity!**",
    "**Ready to make some beautiful forever!**",
    "**You're my favorite always!**",
    "**Time to make some beautiful forevermore!**",
    "**You're my heart's forever!**",
    "**Ready to make some beautiful eternity!**",
    "**You're my favorite timeless!**",
    "**Time to make some beautiful immortality!**",
    "**You're my heart's immortality!**",
    "**Ready to make some beautiful legacy!**",
    "**You're my favorite legend!**",
    "**Time to make some beautiful mythology!**",
    "**You're my heart's mythology!**",
    "**Ready to make some beautiful epicness!**",
    "**You're my favorite saga!**",
    "**Time to make some beautiful chronicle!**",
    "**You're my heart's chronicle!**",
    "**Ready to make some beautiful**",    
    "**You're my favorite epic!**"
]

class UserBotManager:
    def __init__(self):
        self.bots = {}
        self.bot_tasks = {}
        self.pending_approvals = {}  # Track pending approval requests
        self.approved_users = set()  # Track approved users
        self.global_settings = {
            'default_interval': DEFAULT_BROADCAST_INTERVAL,
            'max_bots': 10,
            'auto_restart': False,
            'language': 'en',
            'log_channel': '',  # Channel for broadcasting logs
            'gpt_api_key': '',  # GPT API key for AI responses
            'admin_ids': ORIGINAL_ADMIN_IDS.copy()  # Mutable list of admins
        }
        self.settings = self.load_settings()
        self.ensure_directories()
        self.current_menu = {}
        self.login_states = {}  # Track login states for each user
        
    def ensure_directories(self):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        
    def load_settings(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'global_settings' not in data:
                        data['global_settings'] = self.global_settings
                    if 'approved_users' in data:
                        self.approved_users = set(data['approved_users'])
                    return data
            except:
                return {'global_settings': self.global_settings}
        return {'global_settings': self.global_settings}
    
    def save_settings(self):
        data = {
            'global_settings': self.global_settings,
            'approved_users': list(self.approved_users),
            **self.settings
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_bot_settings(self, session_name):
        if session_name not in self.settings:
            self.settings[session_name] = {
                'broadcast_message': '',
                'welcome_message': '',
                'new_name': '',
                'broadcast_interval': self.global_settings['default_interval'],
                'auto_welcome': False,
                'auto_spam': False,
                'vc_join': False,
                'tag_reply': True,
                'custom_tag_messages': [],
                'gpt_enabled': False,
                'gpt_model': 'gpt-3.5-turbo',
                'last_broadcast': None,
                'total_broadcasts': 0,
                'groups': [],
                'total_members': 0,
                'status': 'stopped',
                'vc_groups': [],  # Track groups with active voice chats
                'scheduled_broadcasts': [],  # Cron-based scheduled broadcasts
                'keywords': {},  # Keyword auto-replies
                'auto_forward': {},  # Forward rules
                'auto_react': {},  # Reaction settings
                'join_leave_notify': False,  # Join/leave notifications
                'moderation_rules': {},  # Bad words and actions
                'ai_chat': False,  # AI-powered replies
                'broadcast_rotation': [],  # Multiple broadcast messages
                'current_broadcast_index': 0,  # Current index in rotation
                'auto_profile_pic': {},  # Auto profile picture settings
                'custom_commands': {},  # Custom slash commands
                'templates': {},  # Message templates
                'user_notes': {},  # User notes
                'api_integrations': {},  # External API integrations
                'raid_mode': {}  # Raid mode settings
            }
        return self.settings[session_name]
    
    async def add_bot(self, session_file):
        session_name = os.path.basename(session_file).replace('.session', '')
        
        try:
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.start()
            me = await client.get_me()
            
            bot = UserBot(session_name, client, me, self)
            self.bots[session_name] = bot
            
            settings = self.get_bot_settings(session_name)
            bot.settings = settings
            
            logger.info(f"✅ Bot added: {session_name} - {me.first_name}")
            return bot
            
        except Exception as e:
            logger.error(f"❌ Failed to add bot {session_name}: {str(e)}")
            return None
    
    async def remove_bot(self, session_name):
        if session_name in self.bots:
            if session_name in self.bot_tasks:
                self.bot_tasks[session_name].cancel()
                try:
                    await self.bot_tasks[session_name]
                except:
                    pass
            
            await self.bots[session_name].client.disconnect()
            del self.bots[session_name]
            
            if session_name in self.bot_tasks:
                del self.bot_tasks[session_name]
            
            if session_name in self.settings:
                self.settings[session_name]['status'] = 'stopped'
                self.save_settings()
            
            logger.info(f"🔴 Bot removed: {session_name}")
            return True
        return False
    
    async def start_bot_services(self, session_name):
        if session_name in self.bot_tasks:
            self.bot_tasks[session_name].cancel()
            try:
                await self.bot_tasks[session_name]
            except:
                pass
        
        if session_name in self.bots:
            bot = self.bots[session_name]
            bot.running = True
            bot.welcomed_users = set()  # Reset welcomed users on start
            task = asyncio.create_task(bot.run_services())
            self.bot_tasks[session_name] = task
            
            self.settings[session_name]['status'] = 'running'
            self.save_settings()
            logger.info(f"▶️ Bot {session_name} started")
    
    async def stop_bot_services(self, session_name):
        if session_name in self.bot_tasks:
            self.bot_tasks[session_name].cancel()
            try:
                await self.bot_tasks[session_name]
            except:
                pass
            del self.bot_tasks[session_name]
        
        if session_name in self.bots:
            self.bots[session_name].running = False
        
        if session_name in self.settings:
            self.settings[session_name]['status'] = 'stopped'
            self.save_settings()
        logger.info(f"⏹️ Bot {session_name} stopped")
    
    def get_all_sessions(self):
        return [f.replace('.session', '') for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    
    def is_admin(self, user_id):
        return user_id in self.global_settings['admin_ids']
    
    def is_approved(self, user_id):
        return user_id in self.approved_users or self.is_admin(user_id)

class UserBot:
    def __init__(self, name, client, me, manager):
        self.name = name
        self.client = client
        self.me = me
        self.manager = manager
        self.settings = {}
        self.running = False
        self.groups_cache = []
        self.users_cache = []
        self.dialogs_cache_time = None
        self.welcome_handler = None
        self.tag_handler = None
        self.vc_handler = None
        self.welcomed_users = set()  # Track users who already got welcome message
        self.used_lines = {}  # Track used lines per user to avoid repetition
        self.tag_cooldown = {}  # Cooldown for tag responses
        
    async def run_services(self):
        logger.info(f"🚀 Starting services for {self.name}")
        self.running = True
        
        # Register welcome handler
        if self.settings.get('auto_welcome', False):
            await self.register_welcome_handler()
        
        # Register tag handler
        if self.settings.get('tag_reply', True):
            await self.register_tag_handler()
        
        # Register VC join handler
        if self.settings.get('vc_join', False):
            await self.register_vc_handler()
        
        broadcast_count = 0
        while self.running:
            try:
                broadcast_count += 1
                
                # Broadcast if enabled
                if self.settings.get('auto_spam', False):
                    logger.info(f"📢 {self.name} - Broadcast #{broadcast_count}")
                    await self.broadcast_to_groups()
                
                # Wait for next broadcast
                interval = self.settings.get('broadcast_interval', DEFAULT_BROADCAST_INTERVAL)
                
                for i in range(interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
            except FloodWaitError as e:
                logger.warning(f"⏳ {self.name} - Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"❌ {self.name} - Error: {str(e)}")
                await asyncio.sleep(5)
        
        logger.info(f"⏹️ {self.name} - Services stopped")
    
    async def register_welcome_handler(self):
        """Register welcome message handler - only sends once per user"""
        
        @self.client.on(events.NewMessage(incoming=True))
        async def welcome_handler(event):
            try:
                if not self.running or not self.settings.get('auto_welcome', False):
                    return
                
                # Sirf private messages
                if not event.is_private or event.out:
                    return
                
                welcome_msg = self.settings.get('welcome_message', '')
                if not welcome_msg:
                    return
                
                sender = await event.get_sender()
                if getattr(sender, 'bot', False):
                    return
                
                user_id = sender.id
                
                # Check if already welcomed
                if user_id in self.welcomed_users:
                    logger.info(f"⏭️ {self.name} - User {user_id} already welcomed, skipping")
                    return  # Pehle hi welcome bhej chuke hain
                
                logger.info(f"👋 {self.name} - First message from {user_id}, sending welcome")
                
                # Small delay to avoid looking like bot
                await asyncio.sleep(2)
                
                # Send welcome message
                await event.reply(welcome_msg)
                
                # Mark as welcomed
                self.welcomed_users.add(user_id)
                logger.info(f"✅ {self.name} - Welcome sent to {user_id}")
                
            except FloodWaitError as e:
                logger.warning(f"⏳ {self.name} - Welcome flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"❌ {self.name} - Welcome error: {str(e)}")
        
        self.welcome_handler = welcome_handler
        logger.info(f"✅ {self.name} - Welcome handler registered (one-time per user)")
    
    async def register_tag_handler(self):
        """Register tag reply handler - sends random line when tagged"""
        
        @self.client.on(events.NewMessage(incoming=True))
        async def tag_handler(event):
            try:
                if not self.running or not self.settings.get('tag_reply', True):
                    return
                
                # Check if bot is mentioned in the message
                if event.message.mentioned:
                    sender = await event.get_sender()
                    if getattr(sender, 'bot', False):
                        return
                    
                    user_id = sender.id
                    current_time = datetime.now().timestamp()
                    
                    # Check cooldown (5 seconds between responses to same user)
                    if user_id in self.tag_cooldown:
                        if current_time - self.tag_cooldown[user_id] < 5:
                            return
                    self.tag_cooldown[user_id] = current_time
                
                    # Get custom messages if available, otherwise use default lines
                    custom_msgs = self.settings.get('custom_tag_messages', [])
                    all_lines = custom_msgs if custom_msgs else SEXY_CHAT_LINES
                    
                    # Select a random line
                    import random
                    line = random.choice(all_lines)
                    
                    # Check if user has already received this line recently
                    if user_id not in self.used_lines:
                        self.used_lines[user_id] = []
                    
                    # Try to find an unused line
                    available_lines = [l for l in all_lines if l not in self.used_lines[user_id]]
                    if not available_lines:
                        # Reset if all lines used
                        self.used_lines[user_id] = []
                        available_lines = all_lines
                    
                    selected_line = random.choice(available_lines)
                    self.used_lines[user_id].append(selected_line)
                    
                    # Send the selected line
                    await event.reply(selected_line)
                    logger.info(f"💬 {self.name} - Tag reply sent to {user_id}")
                
            except FloodWaitError as e:
                logger.warning(f"⏳ {self.name} - Tag flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logger.error(f"❌ {self.name} - Tag handler error: {str(e)}")
        
        self.tag_handler = tag_handler
        logger.info(f"✅ {self.name} - Tag handler registered")
    
    async def register_vc_handler(self):
        """Join voice chats automatically"""
        
        @self.client.on(events.NewMessage(incoming=True))
        async def vc_handler(event):
            try:
                if not self.running or not self.settings.get('vc_join', False):
                    return
                
                # This is a simplified implementation
                # In real scenario, you'd need to check for voice chat events
                # For now, we'll just log when VC might be active
                if hasattr(event.chat, 'title'):
                    logger.info(f"🔊 {self.name} - VC activity detected in {event.chat.title}")
                
            except Exception as e:
                logger.error(f"❌ {self.name} - VC handler error: {str(e)}")
        
        self.vc_handler = vc_handler
        logger.info(f"✅ {self.name} - VC handler registered")
    
    async def get_all_dialogs(self, force_refresh=False):
        if self.dialogs_cache_time and not force_refresh:
            if datetime.now() - self.dialogs_cache_time < timedelta(minutes=5):
                return self.groups_cache, self.users_cache
        
        groups = []
        users = []
        
        try:
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                
                if isinstance(entity, (Chat, Channel)):
                    groups.append({
                        'id': entity.id,
                        'title': getattr(entity, 'title', 'Unknown'),
                        'username': getattr(entity, 'username', None)
                    })
                
                elif isinstance(entity, User) and not entity.bot and not entity.self:
                    users.append({
                        'id': entity.id,
                        'first_name': getattr(entity, 'first_name', 'Unknown'),
                        'username': getattr(entity, 'username', None)
                    })
            
            self.groups_cache = groups
            self.users_cache = users
            self.dialogs_cache_time = datetime.now()
            
            self.settings['groups'] = groups
            self.settings['total_members'] = len(users)
            self.manager.save_settings()
            
            logger.info(f"📊 {self.name} - Found {len(groups)} groups, {len(users)} users")
            
        except Exception as e:
            logger.error(f"❌ {self.name} - Error getting dialogs: {str(e)}")
        
        return groups, users
    
    async def broadcast_to_groups(self):
        message = self.settings.get('broadcast_message', '')
        
        # If broadcast rotation is enabled, use the next message in rotation
        if self.settings.get('broadcast_rotation'):
            rotation_messages = self.settings['broadcast_rotation']
            current_index = self.settings.get('current_broadcast_index', 0)
            if rotation_messages:
                message = rotation_messages[current_index % len(rotation_messages)]
                self.settings['current_broadcast_index'] = (current_index + 1) % len(rotation_messages)
        
        if not message:
            logger.warning(f"⚠️ {self.name} - No broadcast message")
            return
        
        groups, _ = await self.get_all_dialogs()
        if not groups:
            logger.warning(f"⚠️ {self.name} - No groups to broadcast")
            return
        
        logger.info(f"📢 {self.name} - Broadcasting to {len(groups)} groups")
        success = 0
        failed = 0
        
        for i, group in enumerate(groups, 1):
            if not self.running:
                break
            
            try:
                await self.client.send_message(group['id'], message)
                success += 1
                logger.info(f"✅ {self.name} - Sent to {i}/{len(groups)}: {group['title']}")
                
                # Log to channel if set
                if self.manager.global_settings.get('log_channel'):
                    try:
                        await self.client.send_message(
                            self.manager.global_settings['log_channel'],
                            f"Broadcast to {group['title']} ({group['id']})"
                        )
                    except Exception as e:
                        logger.error(f"❌ {self.name} - Log channel error: {str(e)}")
                
                if i < len(groups):
                    await asyncio.sleep(DEFAULT_DELAY_BETWEEN_MSGS)
                    
            except FloodWaitError as e:
                logger.warning(f"⏳ {self.name} - Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
                failed += 1
            except Exception as e:
                logger.error(f"❌ {self.name} - Failed to {group['title']}: {str(e)}")
                failed += 1
        
        self.settings['last_broadcast'] = datetime.now().isoformat()
        self.settings['total_broadcasts'] = self.settings.get('total_broadcasts', 0) + 1
        self.manager.save_settings()
        
        logger.info(f"📊 {self.name} - Broadcast complete: {success} success, {failed} failed")
        return success, failed
    
    async def change_name(self, new_name):
        try:
            parts = new_name.strip().split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
            
            await self.client(UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name
            ))
            
            self.settings['new_name'] = new_name
            self.manager.save_settings()
            return True, "Name changed successfully!"
        except Exception as e:
            return False, f"Error: {str(e)}"

# ============= TELEGRAM BOT =============
bot = TelegramClient('manager_bot', API_ID, API_HASH)
manager = UserBotManager()

def is_admin(user_id):
    return user_id in manager.global_settings['admin_ids']

def is_approved(user_id):
    return user_id in manager.approved_users or is_admin(user_id)

# ============= MAIN MENU =============
async def main_menu(event, edit=False):
    text = """
🤖 **UserBot Manager**

🔹 **Add Bot via Phone** - Login with phone number
🔹 **My Bots** - Manage existing bots
🔹 **Settings** - Configure global settings
🔹 **Backup/Restore** - Backup or restore data
🔹 **Status** - View overall statistics

Select an option below:
"""
    buttons = [
        [Button.inline("📱 Add Bot via Phone", b"add_phone_bot")],
        [Button.inline("🤖 My Bots", b"my_bots")],
        [Button.inline("⚙️ Settings", b"settings")],
        [Button.inline("💾 Backup/Restore", b"backup_restore")],
        [Button.inline("📊 Status", b"status")]
    ]
    
    if edit:
        await event.edit(text, buttons=buttons)
    else:
        await event.reply(text, buttons=buttons)

# ============= BACKUP RESTORE MENU =============
async def backup_restore_menu(event):
    text = """
💾 **Backup & Restore**

• **Create Backup** - Export all data and sessions
• **Restore Backup** - Import from backup file

Select an option:
"""
    buttons = [
        [Button.inline("📤 Create Backup", b"create_backup")],
        [Button.inline("📥 Restore Backup", b"restore_backup")],
        [Button.inline("🔙 Back to Menu", b"back_to_menu")]
    ]
    
    await event.edit(text, buttons=buttons)

# ============= SETTINGS MENU =============
async def settings_menu(event):
    text = f"""
⚙️ **Global Settings**

• Default Interval: `{manager.global_settings['default_interval']}s`
• Max Bots: `{manager.global_settings['max_bots']}`
• Auto Restart: `{'✅' if manager.global_settings['auto_restart'] else '❌'}`
• Language: `{manager.global_settings['language']}`
• Log Channel: `{manager.global_settings.get('log_channel', 'Not set')}`
• GPT API Key: `{'Set' if manager.global_settings.get('gpt_api_key') else 'Not set'}`

Select an option:
"""
    buttons = [
        [Button.inline("⏱️ Set Default Interval", b"set_default_interval")],
        [Button.inline("📊 Set Max Bots", b"set_max_bots")],
        [Button.inline("🔄 Toggle Auto Restart", b"toggle_auto_restart")],
        [Button.inline("🌐 Set Language", b"set_language")],
        [Button.inline("📢 Set Log Channel", b"set_log_channel")],
        [Button.inline("🤖 Set GPT API", b"set_gpt_api")],
        [Button.inline("👥 Manage Admins", b"manage_admins")],
        [Button.inline("🔙 Back to Menu", b"back_to_menu")]
    ]
    
    await event.edit(text, buttons=buttons)

# ============= ADMIN MANAGEMENT MENU =============
async def admin_management_menu(event):
    admin_list = manager.global_settings['admin_ids']
    text = f"""
👥 **Manage Admins**

Current Admins: {len(admin_list)}

Select an option:
"""
    buttons = [
        [Button.inline("➕ Add Admin", b"add_admin")],
        [Button.inline("➖ Remove Admin", b"remove_admin")],
        [Button.inline("📋 List Admins", b"list_admins")],
        [Button.inline("🔙 Back to Settings", b"settings")]
    ]
    
    await event.edit(text, buttons=buttons)

# ============= START COMMAND =============
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not is_approved(event.sender_id):
        # Request approval
        await event.reply("🔒 **Access Pending**\n\nYour request for access is pending approval by an admin.")
        
        # Notify all original admins
        for admin_id in ORIGINAL_ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"⚠️ **New User Request**\n\n"
                    f"User: {event.sender_id}\n"
                    f"Name: {event.sender.first_name if event.sender else 'Unknown'}\n\n"
                    f"Approve or reject this user?",
                    buttons=[
                        [Button.inline("✅ Approve", f"approve_user_{event.sender_id}".encode())],
                        [Button.inline("❌ Reject", f"reject_user_{event.sender_id}".encode())]
                    ]
                )
            except:
                pass  # Admin might not be reachable
        return
    
    await main_menu(event)

# ============= APPROVAL SYSTEM =============
@bot.on(events.CallbackQuery(pattern=b'approve_user_'))
async def approve_user(event):
    if not is_admin(event.sender_id):
        await event.answer("❌ Unauthorized!")
        return
    
    # Extract user ID from callback data
    user_id = int(event.data.decode().replace('approve_user_', ''))
    
    # Add user to approved list
    manager.approved_users.add(user_id)
    manager.save_settings()
    
    # Notify user
    try:
        await bot.send_message(user_id, "✅ **Access Granted**\n\nYou have been approved. You can now use the bot.")
    except:
        pass
    
    await event.edit("✅ User approved and notified!")
    await event.answer("User approved!")

@bot.on(events.CallbackQuery(pattern=b'reject_user_'))
async def reject_user(event):
    if not is_admin(event.sender_id):
        await event.answer("❌ Unauthorized!")
        return
    
    # Extract user ID from callback data
    user_id = int(event.data.decode().replace('reject_user_', ''))
    
    # Notify user
    try:
        await bot.send_message(user_id, "❌ **Access Denied**\n\nYour request has been rejected by an admin.")
    except:
        pass
    
    await event.edit("❌ User rejected and notified!")
    await event.answer("User rejected!")

# ============= PHONE LOGIN SYSTEM =============
@bot.on(events.CallbackQuery(data=b'add_phone_bot'))
async def add_phone_bot_callback(event):
    if not is_approved(event.sender_id):
        await event.answer("❌ Access denied!")
        return
    
    await event.edit(
        "**📱 Enter your phone number**\n\nPlease provide your phone number in international format (e.g. +919876543210):",
        buttons=[Button.inline("🔙 Back to Menu", b"back_to_menu")]
    )
    manager.login_states[event.sender_id] = {'step': 'phone'}

# ============= PHONE LOGIN HANDLERS =============
@bot.on(events.NewMessage)
async def handle_phone_login(event):
    if not is_approved(event.sender_id):
        return
    
    if event.sender_id not in manager.login_states:
        return
    
    login_state = manager.login_states[event.sender_id]
    
    # Handle phone number input
    if login_state.get('step') == 'phone':
        phone_number = event.text.strip()
        
        # Validate phone number format
        if not phone_number.startswith('+') or not phone_number[1:].isdigit():
            await event.reply("**❌ Invalid phone number format!**\n\nPlease enter in international format (e.g. +919876543210)")
            return
        
        # Create client and send OTP
        try:
            client = TelegramClient(os.path.join(SESSIONS_DIR, f"{phone_number.replace('+', '')}.session"), API_ID, API_HASH)
            await client.connect()
            
            # Send OTP
            sent_code = await client.send_code_request(phone_number)
            
            # Store login info
            login_state.update({
                'step': 'code',
                'phone': phone_number,
                'client': client,
                'sent_code': sent_code
            })
            
            await event.reply("**✅ OTP sent!**\n\nEnter the 5-digit code you received (separate digits with spaces, e.g. 1 2 3 4 5):")
            
        except Exception as e:
            await event.reply(f"**❌ Error sending OTP:** {str(e)}\n\nTry again later.")
            manager.login_states.pop(event.sender_id, None)
    
    # Handle OTP code input
    elif login_state.get('step') == 'code':
        code_text = event.text.strip()
        
        # Parse OTP code (space-separated digits)
        try:
            code_parts = code_text.split()
            if len(code_parts) != 5 or not all(p.isdigit() for p in code_parts):
                await event.reply("**❌ Invalid code format!**\n\nPlease enter 5 digits separated by spaces (e.g. 1 2 3 4 5)")
                return
            
            # Reconstruct full code
            code = ''.join(code_parts)
            
            # Sign in with code
            try:
                await login_state['client'].sign_in(login_state['phone'], code)
                # If successful, proceed
                # Successfully signed in
                session_name = login_state['phone'].replace('+', '')
                await login_state['client'].disconnect()
                
                # Add to manager
                session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
                bot_instance = await manager.add_bot(session_path)
                
                if bot_instance:
                    await event.reply(
                        f"**✅ Account added successfully!**\n\n"
                        f"**Name:** {bot_instance.me.first_name}\n"
                        f"**Username:** @{bot_instance.me.username if bot_instance.me.username else 'N/A'}\n"
                        f"**Phone:** {login_state['phone']}",
                        buttons=[[Button.inline("🔙 Back to Menu", b"back_to_menu")]]
                    )
                else:
                    await event.reply("**❌ Failed to add account!**\n\nTry again later.")
                
                # Clean up
                manager.login_states.pop(event.sender_id, None)
                    
            except SessionPasswordNeededError:
                # 2FA password required
                login_state['step'] = 'password'
                await event.reply("**🔒 2FA Password Required!**\n\nEnter your two-factor authentication password:")
                
            except PhoneCodeInvalidError:
                await event.reply("**❌ Invalid OTP code!**\n\nPlease restart the process.")
                manager.login_states.pop(event.sender_id, None)
                
            except Exception as e:
                await event.reply(f"**❌ Login error:** {str(e)}\n\nTry again later.")
                manager.login_states.pop(event.sender_id, None)
                
        except Exception as e:
            await event.reply(f"**❌ Invalid input:** {str(e)}\n\nPlease enter 5 digits separated by spaces (e.g. 1 2 3 4 5)")
    
    # Handle password input
    elif login_state.get('step') == 'password':
        password = event.text.strip()
        
        try:
            # Complete sign-in with password
            await login_state['client'].sign_in(password=password)
            
            # Successfully signed in
            session_name = login_state['phone'].replace('+', '')
            await login_state['client'].disconnect()
            
            # Add to manager
            session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
            bot_instance = await manager.add_bot(session_path)
            
            if bot_instance:
                await event.reply(
                    f"**✅ Account added successfully!**\n\n"
                    f"**Name:** {bot_instance.me.first_name}\n"
                    f"**Username:** @{bot_instance.me.username if bot_instance.me.username else 'N/A'}\n"
                    f"**Phone:** {login_state['phone']}",
                    buttons=[[Button.inline("🔙 Back to Menu", b"back_to_menu")]]
                )
            else:
                await event.reply("**❌ Failed to add account!**\n\nTry again later.")
            
            # Clean up
            manager.login_states.pop(event.sender_id, None)
            
        except Exception as e:
            await event.reply(f"**❌ Password error:** {str(e)}\n\nTry again later.")
            manager.login_states.pop(event.sender_id, None)

# ============= MAIN CALLBACK HANDLER =============
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if not is_approved(event.sender_id):
        await event.answer("❌ Access denied!")
        return
    
    data = event.data
    
    if data == b'back_to_menu':
        await main_menu(event, edit=True)
        return
    
    if data == b'status':
        await show_status(event)
        return
    
    if data == b'my_bots':
        await my_bots(event)
        return
    
    if data == b'settings':
        await settings_menu(event)
        return
    
    if data == b'manage_admins':
        await admin_management_menu(event)
        return
    
    if data == b'add_admin':
        await event.edit(
            "➕ **Add Admin**\n\nSend the user ID of the person you want to make admin:",
            buttons=[Button.inline("🔙 Cancel", b"manage_admins")]
        )
        manager.current_menu[event.sender_id] = 'waiting_add_admin'
        return
    
    if data == b'remove_admin':
        await event.edit(
            "➖ **Remove Admin**\n\nSend the user ID of the admin you want to remove:",
            buttons=[Button.inline("🔙 Cancel", b"manage_admins")]
        )
        manager.current_menu[event.sender_id] = 'waiting_remove_admin'
        return
    
    if data == b'list_admins':
        admin_list = manager.global_settings['admin_ids']
        text = "**📋 Current Admins:**\n\n"
        for admin_id in admin_list:
            text += f"• `{admin_id}`\n"
        text += "\nSelect an option:"
        buttons = [
            [Button.inline("🔙 Back to Admins", b"manage_admins")]
        ]
        await event.edit(text, buttons=buttons)
        return
    
    if data == b'set_default_interval':
        await event.edit(
            "⏱️ **Set Default Interval**\n\nSend interval in seconds (min 5):",
            buttons=[Button.inline("🔙 Cancel", b"settings")]
        )
        manager.current_menu[event.sender_id] = 'waiting_default_interval'
        return
    
    if data == b'set_max_bots':
        await event.edit(
            "📊 **Set Max Bots**\n\nSend maximum number of bots:",
            buttons=[Button.inline("🔙 Cancel", b"settings")]
        )
        manager.current_menu[event.sender_id] = 'waiting_max_bots'
        return
    
    if data == b'toggle_auto_restart':
        manager.global_settings['auto_restart'] = not manager.global_settings['auto_restart']
        manager.save_settings()
        await event.answer(f"✅ Auto Restart: {'ON' if manager.global_settings['auto_restart'] else 'OFF'}")
        await settings_menu(event)
        return
    
    if data == b'set_language':
        await event.edit(
            "🌐 **Set Language**\n\nSend language code (e.g. en, hi, es):",
            buttons=[Button.inline("🔙 Cancel", b"settings")]
        )
        manager.current_menu[event.sender_id] = 'waiting_language'
        return
    
    if data == b'set_log_channel':
        await event.edit(
            "📢 **Set Log Channel**\n\nSend channel username or ID:",
            buttons=[Button.inline("🔙 Cancel", b"settings")]
        )
        manager.current_menu[event.sender_id] = 'waiting_log_channel'
        return
    
    if data == b'set_gpt_api':
        await event.edit(
            "🤖 **Set GPT API Key**\n\nSend your OpenAI API key:",
            buttons=[Button.inline("🔙 Cancel", b"settings")]
        )
        manager.current_menu[event.sender_id] = 'waiting_gpt_api'
        return
    
    if data == b'backup_restore':
        await backup_restore_menu(event)
        return
    
    if data == b'create_backup':
        await create_backup(event)
        return
    
    if data == b'restore_backup':
        await event.edit(
            "📥 **Restore Backup**\n\nPlease send the backup ZIP file:",
            buttons=[Button.inline("🔙 Cancel", b"backup_restore")]
        )
        manager.current_menu[event.sender_id] = 'waiting_backup_file'
        return
    
    data_str = data.decode('utf-8')
    
    if data_str.startswith('bot_'):
        session_name = data_str.replace('bot_', '')
        await bot_details(event, session_name)
        return
    
    if data_str.startswith('activate_'):
        session_name = data_str.replace('activate_', '')
        await activate_bot(event, session_name)
        return
    
    if data_str.startswith('start_'):
        session_name = data_str.replace('start_', '')
        await start_bot(event, session_name)
        return
    
    if data_str.startswith('stop_'):
        session_name = data_str.replace('stop_', '')
        await stop_bot(event, session_name)
        return
    
    if data_str.startswith('togglespam_'):
        session_name = data_str.replace('togglespam_', '')
        await toggle_spam(event, session_name)
        return
    
    if data_str.startswith('togglewelcome_'):
        session_name = data_str.replace('togglewelcome_', '')
        await toggle_welcome(event, session_name)
        return
    
    if data_str.startswith('togglevcjoin_'):
        session_name = data_str.replace('togglevcjoin_', '')
        await toggle_vc_join(event, session_name)
        return
    
    if data_str.startswith('toggletag_'):
        session_name = data_str.replace('toggletag_', '')
        await toggle_tag_reply(event, session_name)
        return
    
    if data_str.startswith('setmsg_'):
        session_name = data_str.replace('setmsg_', '')
        await setmsg_prompt(event, session_name)
        return
    
    if data_str.startswith('setwelcome_'):
        session_name = data_str.replace('setwelcome_', '')
        await setwelcome_prompt(event, session_name)
        return
    
    if data_str.startswith('setname_'):
        session_name = data_str.replace('setname_', '')
        await setname_prompt(event, session_name)
        return
    
    if data_str.startswith('setinterval_'):
        session_name = data_str.replace('setinterval_', '')
        await setinterval_prompt(event, session_name)
        return
    
    if data_str.startswith('setcustomtags_'):
        session_name = data_str.replace('setcustomtags_', '')
        await set_custom_tags_prompt(event, session_name)
        return
    
    if data_str.startswith('setgpt_'):
        session_name = data_str.replace('setgpt_', '')
        await set_gpt_prompt(event, session_name)
        return
    
    if data_str.startswith('refresh_'):
        session_name = data_str.replace('refresh_', '')
        await refresh_stats(event, session_name)
        return
    
    if data_str.startswith('delete_'):
        session_name = data_str.replace('delete_', '')
        await delete_bot(event, session_name)
        return
    
    if data_str.startswith('confirm_delete_'):
        session_name = data_str.replace('confirm_delete_', '')
        await confirm_delete(event, session_name)
        return

# ============= HANDLE INPUTS =============
@bot.on(events.NewMessage)
async def handle_input(event):
    if not is_approved(event.sender_id):
        return
    
    if event.sender_id not in manager.current_menu:
        return
    
    state = manager.current_menu[event.sender_id]
    
    # Handle admin management
    if state == 'waiting_add_admin':
        try:
            user_id = int(event.text)
            if user_id not in manager.global_settings['admin_ids']:
                manager.global_settings['admin_ids'].append(user_id)
                manager.save_settings()
                await event.reply(f"✅ User `{user_id}` added as admin!",
                                buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
            else:
                await event.reply(f"⚠️ User `{user_id}` is already an admin!",
                                buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
        except ValueError:
            await event.reply("❌ Please send a valid user ID!",
                            buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_remove_admin':
        try:
            user_id = int(event.text)
            if user_id in manager.global_settings['admin_ids'] and user_id not in ORIGINAL_ADMIN_IDS:
                manager.global_settings['admin_ids'].remove(user_id)
                manager.save_settings()
                await event.reply(f"✅ User `{user_id}` removed from admins!",
                                buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
            elif user_id in ORIGINAL_ADMIN_IDS:
                await event.reply(f"❌ Cannot remove original admin `{user_id}`!",
                                buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
            else:
                await event.reply(f"⚠️ User `{user_id}` is not an admin!",
                                buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
        except ValueError:
            await event.reply("❌ Please send a valid user ID!",
                            buttons=[Button.inline("🔙 Back to Admins", b"manage_admins")])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    # Handle other inputs
    if state == 'waiting_default_interval':
        try:
            interval = int(event.text)
            if interval < 5:
                await event.reply("⚠️ Minimum interval is 5 seconds!")
            else:
                manager.global_settings['default_interval'] = interval
                manager.save_settings()
                await event.reply(f"✅ Default interval set to {interval}s",
                                buttons=[Button.inline("🔙 Back to Settings", b"settings")])
        except ValueError:
            await event.reply("❌ Please send a valid number!")
        
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_max_bots':
        try:
            max_bots = int(event.text)
            if max_bots < 1:
                await event.reply("⚠️ Minimum is 1 bot!")
            else:
                manager.global_settings['max_bots'] = max_bots
                manager.save_settings()
                await event.reply(f"✅ Max bots set to {max_bots}",
                                buttons=[Button.inline("🔙 Back to Settings", b"settings")])
        except ValueError:
            await event.reply("❌ Please send a valid number!")
        
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_language':
        lang = event.text.strip().lower()
        manager.global_settings['language'] = lang
        manager.save_settings()
        await event.reply(f"✅ Language set to {lang}",
                        buttons=[Button.inline("🔙 Back to Settings", b"settings")])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_log_channel':
        manager.global_settings['log_channel'] = event.text
        manager.save_settings()
        await event.reply(f"✅ Log channel set to {event.text}",
                        buttons=[Button.inline("🔙 Back to Settings", b"settings")])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_gpt_api':
        manager.global_settings['gpt_api_key'] = event.text
        manager.save_settings()
        await event.reply("✅ GPT API key set!",
                        buttons=[Button.inline("🔙 Back to Settings", b"settings")])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state == 'waiting_backup_file':
        if event.document and event.document.mime_type == 'application/zip':
            # Save the backup file temporarily
            file_path = await event.download_media(file=BACKUPS_DIR)
            await event.reply("⏳ **Restoring backup...**")
            
            try:
                # Extract the backup
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall('.')
                
                # Load settings
                manager.settings = manager.load_settings()
                
                await event.reply("✅ **Backup restored successfully!**",
                                buttons=[[Button.inline("🔙 Back to Menu", b"back_to_menu")]])
            except Exception as e:
                await event.reply(f"❌ **Failed to restore backup:** {str(e)}",
                                buttons=[[Button.inline("🔙 Back to Menu", b"back_to_menu")]])
            
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            await event.reply("❌ Please send a valid ZIP file!",
                            buttons=[[Button.inline("🔙 Back to Backup", b"backup_restore")]])
        
        manager.current_menu.pop(event.sender_id, None)
        return
    
    # Bot message handlers
    if state.startswith('waiting_msg_'):
        session_name = state.replace('waiting_msg_', '')
        if session_name in manager.bots:
            manager.bots[session_name].settings['broadcast_message'] = event.text
            manager.save_settings()
            await event.reply("✅ Broadcast message saved!",
                            buttons=[Button.inline("🔙 Back to Bot", f"bot_{session_name}".encode())])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state.startswith('waiting_welcome_'):
        session_name = state.replace('waiting_welcome_', '')
        if session_name in manager.bots:
            manager.bots[session_name].settings['welcome_message'] = event.text
            manager.save_settings()
            await event.reply("✅ Welcome message saved!",
                            buttons=[Button.inline("🔙 Back to Bot", f"bot_{session_name}".encode())])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state.startswith('waiting_name_'):
        session_name = state.replace('waiting_name_', '')
        if session_name in manager.bots:
            success, result = await manager.bots[session_name].change_name(event.text)
            await event.reply(f"{'✅' if success else '❌'} {result}",
                            buttons=[Button.inline("🔙 Back to Bot", f"bot_{session_name}".encode())])
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state.startswith('waiting_interval_'):
        session_name = state.replace('waiting_interval_', '')
        try:
            interval = int(event.text)
            if interval < 5:
                await event.reply("⚠️ Minimum interval is 5 seconds!")
            else:
                if session_name in manager.bots:
                    manager.bots[session_name].settings['broadcast_interval'] = interval
                    manager.save_settings()
                    await event.reply(f"✅ Interval set to {interval}s",
                                    buttons=[Button.inline("🔙 Back to Bot", f"bot_{session_name}".encode())])
        except ValueError:
            await event.reply("❌ Please send a valid number!")
        manager.current_menu.pop(event.sender_id, None)
        return
    
    if state.startswith('waiting_custom_tags_'):
        session_name = state.replace('waiting_custom_tags_', '')
        if session_name in manager.bots:
            # Split by newlines to get multiple messages
            custom_messages = [msg.strip() for msg in event.text.split('\n') if msg.strip()]
            manager.bots[session_name].settings['custom_tag_messages'] = custom_messages
            manager.save_settings()
            await event.reply(f"✅ Custom tag messages set! ({len(custom_messages)} messages)",
                            buttons=[Button.inline("🔙 Back to Bot", f"bot_{session_name}".encode())])
        manager.current_menu.pop(event.sender_id, None)
        return

# ============= BACKUP FUNCTIONS =============
async def create_backup(event):
    await event.edit("⏳ **Creating backup...**")
    
    # Create a temporary directory for the backup
    temp_dir = tempfile.mkdtemp()
    
    # Copy all session files and data file to temp directory
    for item in os.listdir('.'):
        if item.endswith('.session') or item == DATA_FILE:
            shutil.copy(item, temp_dir)
    
    # Create backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)
    
    # Create ZIP archive
    with zipfile.ZipFile(backup_path, 'w') as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, temp_dir))
    
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    
    # Send the backup file
    try:
        await event.edit("✅ **Backup created!**\n\nSending file...")
        await event.reply(
            f"📦 **Backup File**\n\nBackup created successfully: `{backup_filename}`",
            file=backup_path
        )
    except Exception as e:
        await event.edit(f"❌ **Failed to send backup:** {str(e)}")

# ============= MY BOTS =============
async def my_bots(event):
    uploaded = manager.get_all_sessions()
    active = list(manager.bots.keys())
    
    if not uploaded:
        await event.edit("📂 **No Sessions Found**\n\nAdd a phone number first.",
                        buttons=[Button.inline("🔙 Back to Menu", b"back_to_menu")])
        return
    
    buttons = []
    row = []
    
    for session in uploaded:
        status = "🟢" if session in active else "🔴"
        row.append(Button.inline(f"{status} {session}", f"bot_{session}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([Button.inline("🔙 Back to Menu", b"back_to_menu")])
    
    await event.edit(
        f"🤖 **My Bots**\n\nTotal: {len(uploaded)} | Active: {len(active)}",
        buttons=buttons
    )

# ============= BOT DETAILS =============
async def bot_details(event, session_name):
    if session_name not in manager.bots:
        await event.edit(
            f"⚠️ **Bot {session_name} is not active**\n\nActivate it?",
            buttons=[
                [Button.inline("✅ Activate", f"activate_{session_name}".encode())],
                [Button.inline("🗑️ Delete", f"delete_{session_name}".encode())],
                [Button.inline("🔙 Back", b"my_bots")]
            ]
        )
        return
    
    bot = manager.bots[session_name]
    settings = bot.settings
    
    text = f"""
🤖 **Bot: {session_name}**

📊 **Statistics:**
• Status: {'🟢 Running' if settings.get('status') == 'running' else '🔴 Stopped'}
• Groups: {len(settings.get('groups', []))}
• DMs: {settings.get('total_members', 0)}
• Broadcasts: {settings.get('total_broadcasts', 0)}
• Welcomed Users: {len(bot.welcomed_users) if hasattr(bot, 'welcomed_users') else 0}

⚙️ **Settings:**
• Auto Spam: {'✅ ON' if settings.get('auto_spam') else '❌ OFF'}
• Auto Welcome: {'✅ ON' if settings.get('auto_welcome') else '❌ OFF'}
• VC Join: {'✅ ON' if settings.get('vc_join') else '❌ OFF'}
• Tag Reply: {'✅ ON' if settings.get('tag_reply') else '❌ OFF'}
• GPT Enabled: {'✅ ON' if settings.get('gpt_enabled') else '❌ OFF'}
• Interval: {settings.get('broadcast_interval', 25)}s

📝 **Messages:**
• Broadcast: {settings.get('broadcast_message', 'Not set')[:30]}...
• Welcome: {settings.get('welcome_message', 'Not set')[:30]}...
"""
    
    buttons = [
        [
            Button.inline("▶️ Start", f"start_{session_name}".encode()),
            Button.inline("⏹️ Stop", f"stop_{session_name}".encode())
        ],
        [
            Button.inline("📢 Set Msg", f"setmsg_{session_name}".encode()),
            Button.inline("👋 Set Welcome", f"setwelcome_{session_name}".encode())
        ],
        [
            Button.inline("✏️ Change Name", f"setname_{session_name}".encode()),
            Button.inline("⏱️ Set Interval", f"setinterval_{session_name}".encode())
        ],
        [
            Button.inline("🔊 VC Join", f"togglevcjoin_{session_name}".encode()),
            Button.inline("💬 Tag Reply", f"toggletag_{session_name}".encode())
        ],
        [
            Button.inline("🔄 Toggle Spam", f"togglespam_{session_name}".encode()),
            Button.inline("👋 Toggle Welcome", f"togglewelcome_{session_name}".encode())
        ],
        [
            Button.inline("📝 Set Tags", f"setcustomtags_{session_name}".encode()),
            Button.inline("🤖 GPT Mode", f"setgpt_{session_name}".encode())
        ],
        [
            Button.inline("📊 Refresh", f"refresh_{session_name}".encode()),
            Button.inline("🗑️ Remove", f"delete_{session_name}".encode())
        ],
        [Button.inline("🔙 Back to Bots", b"my_bots")]
    ]
    
    await event.edit(text, buttons=buttons)

# ============= BOT ACTIONS =============
async def activate_bot(event, session_name):
    file_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    
    if os.path.exists(file_path):
        await event.edit("⏳ **Activating bot...**")
        bot_instance = await manager.add_bot(file_path)
        
        if bot_instance:
            await event.answer("✅ Bot activated!")
            await bot_details(event, session_name)
        else:
            await event.edit("❌ Failed to activate bot!",
                           buttons=[Button.inline("🔙 Back to Bots", b"my_bots")])
    else:
        await event.edit("❌ Session file not found!",
                        buttons=[Button.inline("🔙 Back to Bots", b"my_bots")])

async def start_bot(event, session_name):
    if session_name in manager.bots:
        await manager.start_bot_services(session_name)
        await event.answer("✅ Bot started!")
        await bot_details(event, session_name)

async def stop_bot(event, session_name):
    if session_name in manager.bots:
        await manager.stop_bot_services(session_name)
        await event.answer("⏹️ Bot stopped!")
        await bot_details(event, session_name)

async def toggle_spam(event, session_name):
    if session_name in manager.bots:
        bot = manager.bots[session_name]
        bot.settings['auto_spam'] = not bot.settings.get('auto_spam', False)
        manager.save_settings()
        await event.answer(f"🔄 Auto Spam: {'ON' if bot.settings['auto_spam'] else 'OFF'}")
        await bot_details(event, session_name)

async def toggle_welcome(event, session_name):
    if session_name in manager.bots:
        bot = manager.bots[session_name]
        bot.settings['auto_welcome'] = not bot.settings.get('auto_welcome', False)
        
        if bot.settings['auto_welcome']:
            await bot.register_welcome_handler()
        else:
            bot.welcomed_users.clear()  # Clear welcomed users when turning off
        
        manager.save_settings()
        await event.answer(f"👋 Auto Welcome: {'ON' if bot.settings['auto_welcome'] else 'OFF'}")
        await bot_details(event, session_name)

async def toggle_vc_join(event, session_name):
    if session_name in manager.bots:
        bot = manager.bots[session_name]
        bot.settings['vc_join'] = not bot.settings.get('vc_join', False)
        
        if bot.settings['vc_join']:
            await bot.register_vc_handler()
        
        manager.save_settings()
        await event.answer(f"🔊 VC Join: {'ON' if bot.settings['vc_join'] else 'OFF'}")
        await bot_details(event, session_name)

async def toggle_tag_reply(event, session_name):
    if session_name in manager.bots:
        bot = manager.bots[session_name]
        bot.settings['tag_reply'] = not bot.settings.get('tag_reply', True)
        
        if bot.settings['tag_reply']:
            await bot.register_tag_handler()
        
        manager.save_settings()
        await event.answer(f"💬 Tag Reply: {'ON' if bot.settings['tag_reply'] else 'OFF'}")
        await bot_details(event, session_name)

async def setmsg_prompt(event, session_name):
    await event.edit(f"📝 **Set Broadcast Message**\n\nSend the message:",
                    buttons=[Button.inline("🔙 Cancel", f"bot_{session_name}".encode())])
    manager.current_menu[event.sender_id] = f'waiting_msg_{session_name}'

async def setwelcome_prompt(event, session_name):
    await event.edit(f"👋 **Set Welcome Message**\n\nSend the message:",
                    buttons=[Button.inline("🔙 Cancel", f"bot_{session_name}".encode())])
    manager.current_menu[event.sender_id] = f'waiting_welcome_{session_name}'

async def setname_prompt(event, session_name):
    await event.edit(f"✏️ **Change Name**\n\nSend new name (First Last):",
                    buttons=[Button.inline("🔙 Cancel", f"bot_{session_name}".encode())])
    manager.current_menu[event.sender_id] = f'waiting_name_{session_name}'

async def setinterval_prompt(event, session_name):
    await event.edit(f"⏱️ **Set Interval**\n\nSend interval in seconds:",
                    buttons=[Button.inline("🔙 Cancel", f"bot_{session_name}".encode())])
    manager.current_menu[event.sender_id] = f'waiting_interval_{session_name}'

async def set_custom_tags_prompt(event, session_name):
    await event.edit(
        f"📝 **Set Custom Tag Messages**\n\nSend one or more messages (each on new line):",
        buttons=[Button.inline("🔙 Cancel", f"bot_{session_name}".encode())]
    )
    manager.current_menu[event.sender_id] = f'waiting_custom_tags_{session_name}'

async def set_gpt_prompt(event, session_name):
    if not manager.global_settings.get('gpt_api_key'):
        await event.answer("⚠️ Please set GPT API key in global settings first!")
        return
    
    if session_name in manager.bots:
        bot = manager.bots[session_name]
        bot.settings['gpt_enabled'] = not bot.settings.get('gpt_enabled', False)
        manager.save_settings()
        await event.answer(f"🤖 GPT Mode: {'ON' if bot.settings['gpt_enabled'] else 'OFF'}")
        await bot_details(event, session_name)

async def refresh_stats(event, session_name):
    if session_name in manager.bots:
        await event.edit("⏳ **Refreshing statistics...**")
        await manager.bots[session_name].get_all_dialogs(force_refresh=True)
        await event.answer("✅ Stats refreshed!")
        await bot_details(event, session_name)

async def delete_bot(event, session_name):
    await event.edit(
        f"⚠️ **Delete {session_name}?**",
        buttons=[
            [
                Button.inline("✅ Yes", f"confirm_delete_{session_name}".encode()),
                Button.inline("❌ No", f"bot_{session_name}".encode())
            ]
        ]
    )

async def confirm_delete(event, session_name):
    if session_name in manager.bots:
        await manager.remove_bot(session_name)
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    await event.edit(f"✅ **Bot {session_name} deleted!**",
                    buttons=[Button.inline("🔙 Back to Bots", b"my_bots")])

# ============= STATUS =============
async def show_status(event):
    uploaded = manager.get_all_sessions()
    active = list(manager.bots.keys())
    running = [s for s in active if manager.settings.get(s, {}).get('status') == 'running']
    
    total_groups = 0
    total_members = 0
    total_welcomed = 0
    
    for session in active:
        settings = manager.settings.get(session, {})
        total_groups += len(settings.get('groups', []))
        total_members += settings.get('total_members', 0)
        if hasattr(manager.bots[session], 'welcomed_users'):
            total_welcomed += len(manager.bots[session].welcomed_users)
    
    text = f"""
📊 **Global Status**

**Sessions:** {len(uploaded)} total | {len(active)} active | {len(running)} running
**Coverage:** {total_groups} groups | {total_members} users
**Welcome:** {total_welcomed} users welcomed

**Active Bots:**
"""
    
    for session in active[:10]:
        status = "🟢" if session in running else "🔴"
        text += f"\n{status} {session}"
    
    buttons = [[Button.inline("🔄 Refresh", b"status"), Button.inline("🔙 Back", b"back_to_menu")]]
    await event.edit(text, buttons=buttons)

# ============= START =============
async def main():
    print("""
    ╔════════════════════════════════════╗
    ║    USERBOT MANAGER - FINAL v6.0    ║
    ║    Complete Feature Set Integrated  ║
    ╚════════════════════════════════════╝
    """)
    
    await bot.start(bot_token=BOT_TOKEN)
    logger.info("🚀 Bot started!")
    
    # Auto-start any bots that were running
    for session_name in manager.bots:
        if manager.settings.get(session_name, {}).get('status') == 'running':
            logger.info(f"🔄 Auto-starting {session_name}")
            await manager.start_bot_services(session_name)
    
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
