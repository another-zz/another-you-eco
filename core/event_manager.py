"""
Event Manager - 事件管理系统（修复版）
冷却时间 + 概率表 + 防重复
"""

import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class Season(Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

@dataclass
class WorldEvent:
    """世界事件"""
    id: str
    name: str
    description: str
    emoji: str
    event_type: str
    duration: int
    effects: Dict
    
    def __str__(self):
        return f"{self.emoji} {self.name} - {self.description}"

@dataclass
class EventCooldown:
    """事件冷却记录"""
    event_id: str
    last_trigger_time: float
    cooldown_seconds: float
    
    def is_ready(self, current_time: float) -> bool:
        return current_time - self.last_trigger_time >= self.cooldown_seconds


class EventManager:
    """事件管理器（修复版）"""
    
    EVENT_DEFINITIONS = {
        'storm': {
            'name': '暴风雨',
            'description': '恶劣天气，移动变慢',
            'emoji': '⛈️',
            'duration': (300, 600),
            'cooldown': (28800, 43200),
            'season_prob': {Season.SPRING: 0.05, Season.SUMMER: 0.10, 
                          Season.AUTUMN: 0.15, Season.WINTER: 0.25},
        },
        'merchant': {
            'name': '商人来访',
            'description': '神秘商人带来稀有资源',
            'emoji': '🏪',
            'duration': (600, 900),
            'cooldown': (259200, 432000),
            'daily_prob': 0.03,
        },
        'meteor': {
            'name': '流星雨',
            'description': '夜晚出现流星雨',
            'emoji': '☄️',
            'duration': (180, 300),
            'cooldown': (604800, 1209600),
            'night_prob': 0.10,
        },
        'harvest_festival': {
            'name': '丰收节',
            'description': '农作物产量翻倍',
            'emoji': '🎉',
            'duration': (1800, 3600),
            'cooldown': (2592000, 2592000),
            'season_end_prob': 0.15,
        },
    }
    
    def __init__(self):
        self.active_events: Dict[str, WorldEvent] = {}
        self.cooldowns: Dict[str, EventCooldown] = {}
        self.last_log_time: Dict[str, float] = {}
        self.log_cooldown = 60.0
        
        current_time = time.time()
        for event_id, definition in self.EVENT_DEFINITIONS.items():
            cooldown_range = definition['cooldown']
            initial_cooldown = random.uniform(*cooldown_range)
            self.cooldowns[event_id] = EventCooldown(
                event_id=event_id,
                last_trigger_time=current_time - initial_cooldown,
                cooldown_seconds=initial_cooldown
            )
            
    def update(self, dt: float, season: Season, hour: int, day: int, agent_count: int):
        """更新事件系统"""
        current_time = time.time()
        
        # 更新活跃事件
        expired = []
        for event_id, event in self.active_events.items():
            event.duration -= dt
            if event.duration <= 0:
                expired.append(event_id)
        for event_id in expired:
            del self.active_events[event_id]
            
        # 尝试触发新事件（每秒检查一次）
        if random.random() < 0.016:  # 约每秒1次
            self._try_trigger_event(current_time, season, hour, day, agent_count)
            
    def _try_trigger_event(self, current_time, season, hour, day, agent_count):
        """尝试触发事件"""
        is_night = hour < 6 or hour > 20
        is_season_end = day >= 25
        
        for event_id, definition in self.EVENT_DEFINITIONS.items():
            cooldown = self.cooldowns.get(event_id)
            if not cooldown or not cooldown.is_ready(current_time):
                continue
                
            # 计算概率
            prob = 0
            if 'season_prob' in definition:
                prob = definition['season_prob'].get(season, 0) / 3600  # 每小时概率
            elif 'daily_prob' in definition:
                prob = definition['daily_prob'] / 86400  # 每秒概率
            elif 'night_prob' in definition and is_night:
                prob = definition['night_prob'] / 3600
            elif 'season_end_prob' in definition and is_season_end:
                prob = definition['season_end_prob'] / 86400
                
            if random.random() < prob:
                self._trigger_event(event_id, definition, current_time)
                break  # 每次只触发一个事件
                
    def _trigger_event(self, event_id, definition, current_time):
        """触发事件"""
        duration = random.randint(*definition['duration'])
        event = WorldEvent(
            id=f"{event_id}_{int(current_time)}",
            name=definition['name'],
            description=definition['description'],
            emoji=definition['emoji'],
            event_type=event_id,
            duration=duration,
            effects={}
        )
        
        self.active_events[event_id] = event
        
        # 更新冷却
        cooldown_range = definition['cooldown']
        new_cooldown = random.uniform(*cooldown_range)
        self.cooldowns[event_id].last_trigger_time = current_time
        self.cooldowns[event_id].cooldown_seconds = new_cooldown
        
        # 记录日志（防刷屏）
        self._log_event(event, current_time)
        
    def _log_event(self, event, current_time):
        """记录事件日志"""
        last_log = self.last_log_time.get(event.event_type, 0)
        if current_time - last_log >= self.log_cooldown:
            print(f"🌟 {event}")
            self.last_log_time[event.event_type] = current_time
            
    def get_active_effects(self) -> Dict:
        """获取活跃事件效果"""
        combined = {}
        for event in self.active_events.values():
            for key, value in event.effects.items():
                if key in combined:
                    if isinstance(value, (int, float)):
                        combined[key] += value
                else:
                    combined[key] = value
        return combined
        
    def get_event_summary(self) -> str:
        """获取事件摘要"""
        if not self.active_events:
            return ""
        event = list(self.active_events.values())[0]
        return f"{event.emoji} {event.name}"
