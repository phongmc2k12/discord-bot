"""
Config Loader - Đọc và quản lý file config.json
"""

import json
import os
from pathlib import Path

class Config:
    """Class quản lý config"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            # Mặc định đọc từ src/data/config.json
            self.config_path = Path(__file__).parent.parent / 'data' / 'config.json'
        else:
            self.config_path = Path(config_path)
        
        self.config_data = {}
        self.load()
    
    def load(self):
        """Load config từ file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            print(f"✅ Đã load config từ {self.config_path}")
        except FileNotFoundError:
            print(f"⚠️ Không tìm thấy config tại {self.config_path}")
            print(f"📝 Tạo config mặc định...")
            self.config_data = self.get_default_config()
            self.save()
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi đọc config: {e}")
            self.config_data = self.get_default_config()
            self.save()
        except Exception as e:
            print(f"❌ Lỗi load config: {e}")
            self.config_data = self.get_default_config()
    
    def save(self):
        """Lưu config ra file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Đã lưu config tại {self.config_path}")
        except Exception as e:
            print(f"❌ Lỗi lưu config: {e}")
    
    def get(self, key, default=None):
        """Lấy giá trị: config.get('bot.prefix')"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key, value):
        """Set giá trị: config.set('bot.prefix', '?')"""
        keys = key.split('.')
        data = self.config_data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
        self.save()
    
    def get_default_config(self):
        """Config mặc định"""
        return {
            "bot": {
                "name": "Phong Bot",
                "version": "2.0.0",
                "prefix": "!",
                "status": "online",
                "activity": "!help để xem lệnh",
                "activity_type": "playing"
            },
            "features": {
                "welcome_message": True,
                "goodbye_message": True,
                "level_system": False,
                "economy": True,
                "auto_moderation": True,
                "music": True,
                "antispam": True,
                "fun": True,
                "admin": True,
                "basic": True
            },
            "welcome": {
                "enabled": True,
                "channel_id": None,
                "message": "Chào mừng {user_mention} đến với {server}! Bạn là thành viên thứ {member_count}",
                "title": "👋 Chào mừng thành viên mới!",
                "image_url": None,
                "thumbnail_url": None,
                "color": "#57F287"
            },
            "goodbye": {
                "enabled": True,
                "channel_id": None,
                "message": "Tạm biệt {user}! Hy vọng gặp lại bạn!",
                "title": "😢 Tạm biệt!",
                "image_url": None,
                "thumbnail_url": None,
                "color": "#ED4245"
            },
            "antispam": {
                "enabled": True,
                "max_messages": 7,
                "time_window": 10,
                "mute_levels": [300, 3600, 10800, 36000, 86400, 259200]
            },
            "music": {
                "enabled": True,
                "default_volume": 50,
                "max_queue_size": 100,
                "ffmpeg_path": "C:\\ffmpeg\\bin\\ffmpeg.exe",
                "download_dir": "downloads",
                "cache_dir": "cache/audio"
            },
            "moderation": {
                "auto_mute_after_warns": 3,
                "mute_role_name": "Muted",
                "log_channel_id": None
            },
            "messages": {
                "welcome": "Chào mừng {user} đến với server!",
                "goodbye": "{user} đã rời server!"
            },
            "colors": {
                "primary": "#7289DA",
                "success": "#57F287",
                "error": "#ED4245",
                "warning": "#FEE75C",
                "info": "#00B0F4"
            },
            "channels": {
                "welcome_channel": None,
                "goodbye_channel": None,
                "log_channel": None,
                "mod_log_channel": None
            },
            "roles": {
                "mute_role": "Muted",
                "admin_role": "Admin",
                "moderator_role": "Moderator"
            },
            "database": {
                "type": "sqlite",
                "path": "database/bot.db"
            },
            "economy": {
                "enabled": True,
                "starting_balance": 1000,
                "daily_reward_min": 500,
                "daily_reward_max": 2000,
                "work_cooldown_hours": 1,
                "gamble_win_rate": 0.4,
                "bet_win_rate": 0.5,
                "slots_jackpot_multiplier": 10,
                "slots_pair_multiplier": 3
            }
        }