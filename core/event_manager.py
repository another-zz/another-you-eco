"""
Event Manager - 事件管理系统（修复版）
冷却时间 + 概率表 + 防重复
"""

import random
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
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
    duration: int  # 持续秒数
    effects: Dict
    
    def __str__(self) -> str:
        return f"{self.emoji} {self.name} - {self.description}"

@dataclass
class EventCooldown:
    """事件冷却记录"""
    event_id: str
    last_trigger_time: float
    cooldown_seconds: float
    
    def is_ready(self, current_time: float) -> bool:
        """检查冷却是否结束"""
        return current_time - self.last_trigger_time >= self.cooldown_seconds
        
    def get_remaining(self, current_time: float) -> float:
        """获取剩余冷却时间"""
        remaining = self.cooldown_seconds - (current_time - self.last_trigger_time)
        return max(0, remaining)


class ProbabilityTable:
    """概率表 - 基于条件的事件触发概率"""
    
    def __init__(self):
        self.tables = {
            'storm': {
                Season.SPRING: 0.05,
                Season.SUMMER: 0.10,
                Season.AUTUMN: 0.15,
                Season.WINTER: 0.25,
            },
            'merchant': 0.03,  # 每天3%
            'meteor': 0.10,    # 夜晚10%
            'harvest_festival': 0.15,  # 每季末15%
            'disease': 0.05,   # 人口密集时5%
            'resource_boom': 0.08,  # 资源丰收8%
        }
        
    def get_probability(self, event_type: str, season: Season = None, 
                       is_night: bool = False, population_density: float = 0) -> float:
        """获取事件触发概率"""
        base_prob = self.tables.get(event_type, 0)
        
        if isinstance(base_prob, dict):
            return base_prob.get(season, 0)
            
        # 流星雨只在夜晚
        if event_type == 'meteor' and not is_night:
            return 0
            
        # 疾病传播受人口密度影响
        if event_type == 'disease':
            return base_prob * population_density
            
        return base_prob


class EventManager:
    """事件管理器（修复版）"""
    
    # 事件定义
    EVENT_DEFINITIONS = {
        'storm': {
            'name': '暴风雨',
            'description': '恶劣天气，移动变慢，建筑可能受损',
            'emoji': '⛈️',
            'duration': (300, 600),  # 5-10分钟
            'cooldown': (28800, 43200),  # 8-12小时
            'effects': {'speed_penalty': 0.5, 'energy_drain': 2.0},
        },
        'merchant': {
            'name': '商人来访',
            'description': '神秘商人带来稀有资源',
            'emoji': '🏪',
            'duration': (600, 900),  # 10-15分钟
            'cooldown': (259200, 432000),  # 3-5天
            'effects': {'trade_opportunity': True, 'rare_items': True},
        },
        'meteor': {
            'name': '流星雨',
            'description': '夜晚出现流星雨，带来稀有矿石',
            'emoji': '☄️',
            'duration': (180, 300),  # 3-5分钟
            'cooldown': (604800, 1209600),  # 7-14天
            'effects': {'rare_ores': True, 'mood_boost': 15},
        },
        'harvest_festival': {
            'name': '丰收节',
            'description': '农作物产量翻倍，所有AI心情变好',
            'emoji': '🎉',
            'duration': (1800, 3600),  # 30-60分钟
            'cooldown': (2592000, 2592000),  # 30天固定
            'effects': {'food_multiplier': 2, 'mood_boost': 25},
        },
        'disease': {
            'name': '疾病传播',
            'description': '某种疾病在AI中传播',
            'emoji': '🤒',
            'duration': (1200, 2400),  # 20-40分钟
            'cooldown': (86400, 172800),  # 1-2天
            'effects': {'health_penalty': 0.3, 'energy_drain': 1.5},
        },
        'resource_boom': {
            'name': '资源丰收',
            'description': '野外资源大量刷新',
            'emoji': '🌾',
            'duration': (600, 1200),  # 10-20分钟
            'cooldown': (43200, 86400),  # 12-24小时
            'effects': {'resource_multiplier': 2},
        },
    }
    
    def __init__(self):
        self.active_events: Dict[str, WorldEvent] = {}
        self.event_history: List[WorldEvent] = []
        self.cooldowns: Dict[str, EventCooldown] = {}
        self.probability_table = ProbabilityTable()
        
        # 日志去重
        self.last_log_time: Dict[str, float] = {}
        self.log_cooldown = 60.0  # 同类型日志最少间隔60秒
        
        # 初始化冷却记录
        current_time = time.time()
        for event_id, definition in self.EVENT_DEFINITIONS.items():
            cooldown_range = definition['cooldown']
            initial_cooldown = random.uniform(*cooldown_range)
            self.cooldowns[event_id] = EventCooldown(
                event_id=event_id,
                last_trigger_time=current_time - initial_cooldown,  # 初始随机冷却
                cooldown_seconds=initial_cooldown
            )
            
    def update(self, dt: float, season: Season, hour: int, agent_count: int):
        """更新事件系统"""
        current_time = time.time()
        
        # 更新活跃事件持续时间
        expired_events = []
        for event_id, event in self.active_events.items():
            event.duration -= dt
            if event.duration <= 0:
                expired_events.append(event_id)
                
        # 移除过期事件
        for event_id in expired_events:
            del self.active_events[event_id]
            
        # 尝试触发新事件（每10秒检查一次）
        if random.random() < 0.1:  # 10%概率每帧检查（约每秒1次）
            self._try_trigger_event(current_time, season, hour, agent_count)
            
    def _try_trigger_event(self, current_time: float, season: Season, 
                          hour: int, agent_count: int):
        """尝试触发事件"""
        is_night = hour < 6 or hour > 20
        population_density = min(1.0, agent_count / 50)  # 人口密度系数
        
        # 按优先级检查事件
        event_candidates = []
        
        for event_id, definition in self.EVENT_DEFINITIONS.items():
            # 检查冷却
            cooldown = self.cooldowns.get(event_id)
            if cooldown and not cooldown.is_ready(current_time):
                continue
                
            # 检查概率
            prob = self.probability_table.get_probability(
                event_id, season, is_night, population_density
            )
            
            if random.random() < prob / 60:  # 转换为每秒概率
                event_candidates.append((event_id, definition, prob))
                
        # 如果有候选事件，选择概率最高的触发
        if event_candidates:
            event_candidates.sort(key=lambda x: x[2], reverse=True)
            selected_id, selected_def, _ = event_candidates[0]
            self._trigger_event(selected_id, selected_def, current_time)
            
    def _trigger_event(self, event_id: str, definition: Dict, current_time: float):
        """触发事件"""
        # 创建事件
        duration = random.randint(*definition['duration'])
        event = WorldEvent(
            id=f"{event_id}_{int(current_time)}",
            name=definition['name'],
            description=definition['description'],
            emoji=definition['emoji'],
            event_type=event_id,
            duration=duration,
            effects=definition['effects'].copy()
        )
        
        # 添加到活跃事件
        self.active_events[event_id] = event
        self.event_history.append(event)
        
        # 更新冷却
        cooldown_range = definition['cooldown']
        new_cooldown = random.uniform(*cooldown_range)
        self.cooldowns[event_id].last_trigger_time = current_time
        self.cooldowns[event_id].cooldown_seconds = new_cooldown
        
        # 记录日志（带冷却）
        self._log_event(event, current_time)
        
    def _log_event(self, event: WorldEvent, current_time: float):
        """记录事件日志（防刷屏）"""
        last_log = self.last_log_time.get(event.event_type, 0)
        
        if current_time - last_log >= self.log_cooldown:
            print(f"🌟 {event}")
            self.last_log_time[event.event_type] = current_time
            
    def get_active_effects(self) -> Dict:
        """获取所有活跃事件的效果叠加"""
        combined = {}
        for event in self.active_events.values():
            for key, value in event.effects.items():
                if key in combined:
                    if isinstance(value, (int, float)):
                        combined[key] += value
                    else:
                        combined[key] = value
                else:
                    combined[key] = value
        return combined
        
    def get_event_summary(self) -> str:
        """获取事件摘要（用于HUD）"""
        if not self.active_events:
            return ""
        event = list(self.active_events.values())[0]
        return f"{event.emoji} {event.name}"
