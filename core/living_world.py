"""
AnotherYou ECO v0.4 - 活的世界
时间 + 天气 + 记忆 + 事件 + 社会演化
"""

import pygame
import asyncio
import random
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import numpy as np

# ============ 时间系统 ============

class Season(Enum):
    SPRING = "spring"    # 春 - 生长
    SUMMER = "summer"    # 夏 - 炎热
    AUTUMN = "autumn"    # 秋 - 丰收
    WINTER = "winter"    # 冬 - 休眠

class Weather(Enum):
    SUNNY = "sunny"      # 晴
    CLOUDY = "cloudy"    # 多云
    RAINY = "rainy"      # 雨
    STORMY = "stormy"    # 暴风雨
    SNOWY = "snowy"      # 雪
    FOGGY = "foggy"      # 雾

@dataclass
class GameTime:
    """游戏时间系统"""
    tick: int = 0
    hour: int = 6        # 0-23
    day: int = 1         # 1-30
    season: Season = Season.SPRING
    year: int = 1
    
    # 时间比例: 1秒现实 = 10分钟游戏
    TICKS_PER_HOUR = 6   # 6 tick = 1小时
    HOURS_PER_DAY = 24
    DAYS_PER_SEASON = 30
    
    def advance(self, ticks: int = 1):
        """推进时间"""
        self.tick += ticks
        
        total_hours = self.tick // self.TICKS_PER_HOUR
        self.hour = total_hours % self.HOURS_PER_DAY
        
        total_days = total_hours // self.HOURS_PER_DAY
        self.day = (total_days % self.DAYS_PER_SEASON) + 1
        
        season_idx = (total_days // self.DAYS_PER_SEASON) % 4
        self.season = list(Season)[season_idx]
        
        self.year = total_days // (self.DAYS_PER_SEASON * 4) + 1
        
    def get_light_level(self) -> float:
        """获取光照强度 0-1"""
        if 6 <= self.hour < 18:  # 白天
            peak = 12
            dist = abs(self.hour - peak)
            return 0.3 + 0.7 * (1 - dist / 6)
        else:  # 夜晚
            return 0.1
            
    def get_season_color_tint(self) -> Tuple[int, int, int]:
        """获取季节颜色色调"""
        tints = {
            Season.SPRING: (200, 255, 200),  # 嫩绿
            Season.SUMMER: (255, 255, 200),  # 金黄
            Season.AUTUMN: (255, 200, 150),  # 橙红
            Season.WINTER: (220, 240, 255),  # 雪白
        }
        return tints.get(self.season, (255, 255, 255))
        
    def __str__(self) -> str:
        return f"Year {self.year} {self.season.value.title()} Day {self.day} {self.hour:02d}:00"


# ============ 天气系统 ============

@dataclass
class WeatherSystem:
    """天气系统"""
    current: Weather = Weather.SUNNY
    intensity: float = 0.5  # 0-1 强度
    duration: int = 0       # 剩余tick
    
    # 季节天气概率
    SEASON_WEATHER = {
        Season.SPRING: [(Weather.SUNNY, 0.4), (Weather.CLOUDY, 0.3), (Weather.RAINY, 0.25), (Weather.FOGGY, 0.05)],
        Season.SUMMER: [(Weather.SUNNY, 0.5), (Weather.CLOUDY, 0.2), (Weather.RAINY, 0.2), (Weather.STORMY, 0.1)],
        Season.AUTUMN: [(Weather.SUNNY, 0.3), (Weather.CLOUDY, 0.3), (Weather.RAINY, 0.3), (Weather.FOGGY, 0.1)],
        Season.WINTER: [(Weather.SUNNY, 0.2), (Weather.CLOUDY, 0.3), (Weather.SNOWY, 0.4), (Weather.FOGGY, 0.1)],
    }
    
    def update(self, season: Season):
        """更新天气"""
        self.duration -= 1
        
        if self.duration <= 0:
            # 切换天气
            self._change_weather(season)
            
    def _change_weather(self, season: Season):
        """根据季节改变天气"""
        options = self.SEASON_WEATHER.get(season, [(Weather.SUNNY, 1.0)])
        weights = [w for _, w in options]
        self.current = random.choices([w for w, _ in options], weights=weights)[0]
        self.intensity = random.uniform(0.3, 1.0)
        self.duration = random.randint(60, 180)  # 10-30分钟
        
    def get_visibility(self) -> float:
        """获取能见度"""
        base = 1.0
        if self.current == Weather.FOGGY:
            base = 0.3
        elif self.current == Weather.RAINY:
            base = 0.7
        elif self.current == Weather.STORMY:
            base = 0.5
        return base * (1 - self.intensity * 0.3)
        
    def get_movement_modifier(self) -> float:
        """移动速度修正"""
        if self.current == Weather.RAINY:
            return 0.9
        elif self.current == Weather.STORMY:
            return 0.7
        elif self.current == Weather.SNOWY:
            return 0.8
        return 1.0
        
    def __str__(self) -> str:
        icons = {
            Weather.SUNNY: "☀️",
            Weather.CLOUDY: "☁️",
            Weather.RAINY: "🌧️",
            Weather.STORMY: "⛈️",
            Weather.SNOWY: "❄️",
            Weather.FOGGY: "🌫️",
        }
        return f"{icons.get(self.current, '?')} {self.current.value.title()}"


# ============ 记忆系统（Stanford Smallville风格） ============

@dataclass
class Memory:
    """单个记忆"""
    timestamp: int
    content: str
    importance: float  # 0-10
    embeddings: Optional[List[float]] = None
    
@dataclass  
class MemoryStream:
    """记忆流 - 参考Stanford Smallville"""
    agent_id: str
    memories: List[Memory] = field(default_factory=list)
    
    # 记忆类型
    observations: List[Memory] = field(default_factory=list)  # 观察
    reflections: List[Memory] = field(default_factory=list)   # 反思
    plans: List[Memory] = field(default_factory=list)         # 计划
    
    def add_observation(self, content: str, importance: float = 5):
        """添加观察记忆"""
        memory = Memory(
            timestamp=len(self.memories),
            content=content,
            importance=importance
        )
        self.memories.append(memory)
        self.observations.append(memory)
        
        # 限制数量
        if len(self.observations) > 100:
            self.observations.pop(0)
            
    def add_reflection(self, content: str, importance: float = 7):
        """添加反思（高层次洞察）"""
        memory = Memory(
            timestamp=len(self.memories),
            content=content,
            importance=importance
        )
        self.memories.append(memory)
        self.reflections.append(memory)
        
    def retrieve_relevant(self, query: str, k: int = 5) -> List[Memory]:
        """检索相关记忆（简化版，实际应用向量相似度）"""
        # 按重要性 + 时间衰减排序
        scored = []
        for m in self.memories[-50:]:  # 最近50条
            # 时间衰减
            recency = 1.0 - (len(self.memories) - m.timestamp) / 100
            # 关键词匹配（简化）
            relevance = 0.5
            for word in query.lower().split():
                if word in m.content.lower():
                    relevance += 0.5
            score = m.importance * 0.3 + recency * 0.3 + relevance * 0.4
            scored.append((score, m))
            
        scored.sort(reverse=True)
        return [m for _, m in scored[:k]]
        
    def daily_reflection(self) -> str:
        """每日反思 - 总结今天的经历"""
        if len(self.observations) < 5:
            return ""
            
        # 分析今天的高重要性事件
        today_events = [m for m in self.observations[-20:] if m.importance >= 6]
        
        if not today_events:
            return ""
            
        # 生成反思（简化，实际用LLM）
        themes = {}
        for e in today_events:
            # 简单主题提取
            if "食物" in e.content or "吃" in e.content:
                themes["生存"] = themes.get("生存", 0) + 1
            if "朋友" in e.content or "聊天" in e.content:
                themes["社交"] = themes.get("社交", 0) + 1
            if "建" in e.content:
                themes["建设"] = themes.get("建设", 0) + 1
                
        if themes:
            main_theme = max(themes, key=themes.get)
            reflection = f"今天主要关注{main_theme}，这是当前最优先的需求"
            self.add_reflection(reflection, importance=8)
            return reflection
        return ""


# ============ 关系系统 ============

@dataclass
class Relationship:
    """两个AI之间的关系"""
    target_id: str
    friendship: float = 0      # -100 到 100，友谊
    trust: float = 0           # -100 到 100，信任
    intimacy: float = 0        # 0 到 100，亲密
    
    # 关系历史
    interactions: List[Dict] = field(default_factory=list)
    
    def update(self, event_type: str, impact: float):
        """更新关系"""
        if event_type == "help":
            self.friendship += impact
            self.trust += impact * 0.5
        elif event_type == "chat":
            self.friendship += impact * 0.3
            self.intimacy += impact * 0.2
        elif event_type == "betray":
            self.friendship -= impact * 2
            self.trust -= impact * 2
            
        # 限制范围
        self.friendship = max(-100, min(100, self.friendship))
        self.trust = max(-100, min(100, self.trust))
        self.intimacy = max(0, min(100, self.intimacy))
        
    def get_status(self) -> str:
        """获取关系状态"""
        if self.friendship > 50:
            return "挚友" if self.intimacy > 50 else "好友"
        elif self.friendship > 20:
            return "朋友"
        elif self.friendship > -20:
            return "熟人"
        elif self.friendship > -50:
            return "冷淡"
        else:
            return "敌对"


# ============ 事件系统（RimWorld风格） ============

@dataclass
class WorldEvent:
    """世界事件"""
    id: str
    name: str
    description: str
    event_type: str  # global, local, personal
    duration: int    # 持续tick
    effects: Dict    # 影响
    
@dataclass
class EventManager:
    """事件管理器"""
    active_events: List[WorldEvent] = field(default_factory=list)
    event_history: List[WorldEvent] = field(default_factory=list)
    
    # 事件池
    EVENT_POOL = [
        {
            "name": "丰收节",
            "description": "农作物产量翻倍，所有AI心情变好",
            "type": "global",
            "weight": 0.1,
            "seasons": [Season.AUTUMN],
            "effects": {"mood_boost": 20, "food_multiplier": 2}
        },
        {
            "name": "暴风雨",
            "description": "恶劣天气，移动变慢，建筑可能受损",
            "type": "global", 
            "weight": 0.15,
            "seasons": [Season.SPRING, Season.SUMMER],
            "effects": {"speed_penalty": 0.5, "building_damage": 0.1}
        },
        {
            "name": "商人来访",
            "description": "神秘商人带来稀有资源",
            "type": "global",
            "weight": 0.08,
            "seasons": [Season.SPRING, Season.SUMMER, Season.AUTUMN],
            "effects": {"trade_opportunity": True}
        },
        {
            "name": "流星雨",
            "description": "夜晚出现流星雨，带来稀有矿石",
            "type": "global",
            "weight": 0.05,
            "seasons": [Season.SPRING, Season.AUTUMN, Season.WINTER],
            "effects": {"rare_ores": True, "mood_boost": 10}
        },
        {
            "name": "疾病传播",
            "description": "某种疾病在AI中传播",
            "type": "global",
            "weight": 0.08,
            "seasons": [Season.WINTER],
            "effects": {"health_penalty": 0.3}
        },
    ]
    
    def update(self, game_time: GameTime, weather: WeatherSystem):
        """更新事件"""
        # 减少活跃事件持续时间
        for event in self.active_events:
            event.duration -= 1
            
        # 清理过期事件
        self.active_events = [e for e in self.active_events if e.duration > 0]
        
        # 随机触发新事件
        if random.random() < 0.01:  # 1%概率每tick
            self._try_trigger_event(game_time, weather)
            
    def _try_trigger_event(self, game_time: GameTime, weather: WeatherSystem):
        """尝试触发事件"""
        # 筛选符合季节的事件
        valid_events = [e for e in self.EVENT_POOL 
                       if game_time.season in e.get("seasons", [])]
        
        if not valid_events:
            return
            
        # 按权重选择
        weights = [e.get("weight", 0.1) for e in valid_events]
        event_template = random.choices(valid_events, weights=weights)[0]
        
        # 创建事件
        event = WorldEvent(
            id=f"event_{game_time.tick}",
            name=event_template["name"],
            description=event_template["description"],
            event_type=event_template["type"],
            duration=random.randint(300, 600),  # 50-100分钟
            effects=event_template.get("effects", {})
        )
        
        self.active_events.append(event)
        self.event_history.append(event)
        
        print(f"🌟 世界事件: {event.name} - {event.description}")
        
    def get_active_effects(self) -> Dict:
        """获取所有活跃事件的效果叠加"""
        combined = {}
        for event in self.active_events:
            for key, value in event.effects.items():
                if key in combined:
                    if isinstance(value, (int, float)):
                        combined[key] += value
                    else:
                        combined[key] = value
                else:
                    combined[key] = value
        return combined


# ============ 地形系统增强 ============

class TerrainType(Enum):
    PLAINS = "plains"      # 平原
    FOREST = "forest"      # 森林
    MOUNTAIN = "mountain"  # 山地
    RIVER = "river"        # 河流
    LAKE = "lake"          # 湖泊
    DESERT = "desert"      # 沙漠

@dataclass
class TerrainCell:
    """地形单元"""
    x: int
    y: int
    terrain: TerrainType
    fertility: float = 1.0   # 肥沃度
    resources: Dict[str, float] = field(default_factory=dict)
    
    def get_building_suitability(self) -> float:
        """获取建房的适宜度"""
        scores = {
            TerrainType.PLAINS: 1.0,
            TerrainType.FOREST: 0.7,
            TerrainType.MOUNTAIN: 0.3,
            TerrainType.RIVER: 0.9,   # 河边适合建房
            TerrainType.LAKE: 0.8,
            TerrainType.DESERT: 0.4,
        }
        return scores.get(self.terrain, 0.5)
        
    def get_mining_yield(self) -> float:
        """获取采矿产出"""
        if self.terrain == TerrainType.MOUNTAIN:
            return 2.0
        elif self.terrain == TerrainType.FOREST:
            return 0.5
        return 0.0
        
    def get_farming_yield(self, season: Season) -> float:
        """获取农业产出"""
        base = self.fertility
        
        # 季节修正
        season_mod = {
            Season.SPRING: 1.2,
            Season.SUMMER: 1.0,
            Season.AUTUMN: 1.5,  # 丰收
            Season.WINTER: 0.0,  # 无法种植
        }
        
        # 地形修正
        terrain_mod = {
            TerrainType.PLAINS: 1.0,
            TerrainType.FOREST: 0.6,
            TerrainType.RIVER: 1.3,  # 河边肥沃
            TerrainType.DESERT: 0.3,
        }
        
        return base * season_mod.get(season, 1.0) * terrain_mod.get(self.terrain, 0.5)


# ============ 增强版AI ============

@dataclass
class LivingAgent:
    """活的世界中的AI"""
    id: str
    name: str
    x: int
    y: int
    
    # 基础状态
    energy: float = 100
    max_energy: float = 100
    health: float = 100
    mood: float = 50  # 0-100 心情
    alive: bool = True
    
    # 资源
    inventory: Dict[str, float] = field(default_factory=dict)
    money: float = 0
    
    # 系统
    memory: MemoryStream = field(default_factory=lambda: MemoryStream(""))
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    
    # 当前状态
    current_action: str = "idle"
    action_target: Optional[Tuple[int, int]] = None
    home: Optional[Tuple[int, int]] = None
    
    # 性格
    traits = {
        'curiosity': 0.5,
        'sociability': 0.5,
        'industriousness': 0.5,
        'caution': 0.5,
    }
    
    def __post_init__(self):
        if not self.memory.agent_id:
            self.memory.agent_id = self.id
            
    def update(self, world: 'LivingWorld'):
        """AI更新"""
        if not self.alive:
            return
            
        # 基础消耗
        self.energy -= 0.1
        
        # 天气影响
        weather = world.weather
        if weather.current == Weather.RAINY:
            self.mood -= 0.1
        elif weather.current == Weather.SUNNY:
            self.mood += 0.05
            
        # 事件影响
        for event in world.events.active_events:
            if "mood_boost" in event.effects:
                self.mood += event.effects["mood_boost"] / 100
                
        # 限制
        self.mood = max(0, min(100, self.mood))
        
        # 检查死亡
        if self.energy <= 0:
            self.alive = False
            print(f"💀 {self.name} 因能量耗尽死亡")
            
    def decide_action(self, world: 'LivingWorld') -> Dict:
        """决策（简化版，实际用LLM）"""
        # 夜晚回家
        if world.time.hour >= 20 or world.time.hour < 6:
            if self.home:
                return {"action": "go_home", "target": self.home}
            else:
                return {"action": "build_shelter"}
                
        # 饿了找食物
        if self.energy < 40:
            return {"action": "find_food"}
            
        # 没有家，优先建房（河边或平原）
        if not self.home:
            return {"action": "find_home_location"}
            
        # 默认探索
        return {"action": "explore"}


# ============ 活的世界 ============

@dataclass
class LivingWorld:
    """活的世界 - v0.4核心"""
    width: int = 200
    height: int = 200
    
    # 系统
    time: GameTime = field(default_factory=GameTime)
    weather: WeatherSystem = field(default_factory=WeatherSystem)
    events: EventManager = field(default_factory=EventManager)
    
    # 世界内容
    terrain: Dict[Tuple[int, int], TerrainCell] = field(default_factory=dict)
    agents: Dict[str, LivingAgent] = field(default_factory=dict)
    buildings: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        self._generate_terrain()
        
    def _generate_terrain(self):
        """生成地形"""
        # 使用简单噪声生成地形
        for x in range(self.width):
            for y in range(self.height):
                # 中心是平原，边缘是山地
                dist_from_center = math.sqrt((x - 100)**2 + (y - 100)**2)
                
                if dist_from_center > 80:
                    terrain = TerrainType.MOUNTAIN
                elif random.random() < 0.1:
                    terrain = TerrainType.RIVER if random.random() < 0.7 else TerrainType.LAKE
                elif random.random() < 0.3:
                    terrain = TerrainType.FOREST
                else:
                    terrain = TerrainType.PLAINS
                    
                self.terrain[(x, y)] = TerrainCell(x, y, terrain)
                
    def update(self):
        """世界更新"""
        # 更新时间
        self.time.advance()
        
        # 更新天气
        self.weather.update(self.time.season)
        
        # 更新事件
        self.events.update(self.time, self.weather)
        
        # 更新所有AI
        for agent in self.agents.values():
            agent.update(self)
            
        # 每日反思
        if self.time.hour == 23 and self.time.tick % 6 == 0:
            for agent in self.agents.values():
                if agent.alive:
                    agent.memory.daily_reflection()


# ============ 管理员上帝视角系统 ============

class AdminMode(Enum):
    NORMAL = "normal"      # 普通玩家模式
    GOD = "god"            # 上帝视角
    
@dataclass
class Camera:
    """相机系统"""
    x: float = 0
    y: float = 0
    zoom: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 3.0
    
    mode: AdminMode = AdminMode.NORMAL
    
    # 普通模式限制
    normal_max_zoom: float = 1.5
    normal_view_range: int = 50  # 只能看到50格范围
    
    def set_mode(self, mode: AdminMode):
        """设置模式"""
        self.mode = mode
        if mode == AdminMode.GOD:
            self.min_zoom = 0.05  # 可以缩得更小
            print("👁️ 进入上帝视角模式")
        else:
            self.min_zoom = 0.5
            self.zoom = min(self.zoom, self.normal_max_zoom)
            print("👤 返回普通模式")
            
    def can_see(self, target_x: int, target_y: int, player_x: int, player_y: int) -> bool:
        """检查是否能看到目标位置"""
        if self.mode == AdminMode.GOD:
            return True
            
        # 普通模式限制视野
        dist = abs(target_x - player_x) + abs(target_y - player_y)
        return dist <= self.normal_view_range
        
    def world_to_screen(self, world_x: int, world_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """世界坐标转屏幕坐标"""
        cell_size = 20 * self.zoom
        screen_x = int(world_x * cell_size - self.x + screen_width / 2)
        screen_y = int(world_y * cell_size - self.y + screen_height / 2)
        return screen_x, screen_y
        
    def screen_to_world(self, screen_x: int, screen_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """屏幕坐标转世界坐标"""
        cell_size = 20 * self.zoom
        world_x = int((screen_x - screen_width / 2 + self.x) / cell_size)
        world_y = int((screen_y - screen_height / 2 + self.y) / cell_size)
        return world_x, world_y
        
    def move(self, dx: float, dy: float):
        """移动相机"""
        self.x += dx * (2.0 if self.mode == AdminMode.GOD else 1.0)
        self.y += dy * (2.0 if self.mode == AdminMode.GOD else 1.0)
        
    def zoom_in(self):
        """放大"""
        self.zoom = min(self.max_zoom, self.zoom * 1.1)
        
    def zoom_out(self):
        """缩小"""
        max_z = 3.0 if self.mode == AdminMode.GOD else self.normal_max_zoom
        self.zoom = max(self.min_zoom, min(max_z, self.zoom / 1.1))


# 导出
__all__ = [
    'GameTime', 'Season', 'Weather', 'WeatherSystem',
    'Memory', 'MemoryStream', 'Relationship',
    'WorldEvent', 'EventManager',
    'TerrainType', 'TerrainCell',
    'LivingAgent', 'LivingWorld',
    'Camera', 'AdminMode'
]
