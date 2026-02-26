"""
AnotherYou ECO - 自主演化AI世界 v0.1
核心：自然规律驱动的AI社会模拟
"""

import asyncio
import random
import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# ============ 常量定义 ============

TICKS_PER_HOUR = 60  # 每小时60tick
HOURS_PER_DAY = 24
DAY_START = 6  # 早晨6点
NIGHT_START = 20  # 晚上8点

class NeedType(Enum):
    """需求类型 - 马斯洛需求层次"""
    SURVIVAL = auto()      # 生存：饥饿、口渴、健康
    SAFETY = auto()        # 安全：住所、财产、秩序
    BELONGING = auto()     # 归属：友谊、爱情、社群
    ESTEEM = auto()        # 尊重：成就、地位、认可
    SELF_ACTUALIZATION = auto()  # 自我实现：创造、探索

class ResourceType(Enum):
    """资源类型"""
    FOOD = "food"           # 食物
    WATER = "water"         # 水
    WOOD = "wood"           # 木材
    STONE = "stone"         # 石头
    TOOL = "tool"           # 工具
    MEDICINE = "medicine"   # 药品
    LUXURY = "luxury"       # 奢侈品

class SkillType(Enum):
    """技能类型"""
    GATHERING = "gathering"   # 采集
    FARMING = "farming"       # 农耕
    CRAFTING = "crafting"     #  crafting
    TRADING = "trading"       # 交易
    SOCIAL = "social"         # 社交
    COMBAT = "combat"         # 战斗

class RelationshipType(Enum):
    """关系类型"""
    STRANGER = 0
    ACQUAINTANCE = 1
    FRIEND = 2
    CLOSE_FRIEND = 3
    FAMILY = 4
    RIVAL = -1
    ENEMY = -2

# ============ 数据类 ============

@dataclass
class Need:
    """需求"""
    type: NeedType
    name: str
    current: float = 100.0  # 当前值
    max: float = 100.0
    decay_rate: float = 1.0  # 每秒衰减
    priority: float = 0.0   # 动态优先级
    
    def update(self, delta_time: float):
        """更新需求"""
        self.current = max(0, self.current - self.decay_rate * delta_time)
        # 越低优先级越高
        self.priority = (self.max - self.current) / self.max
    
    def satisfy(self, amount: float):
        """满足需求"""
        self.current = min(self.max, self.current + amount)

@dataclass
class Memory:
    """记忆"""
    timestamp: datetime
    event: str
    importance: float  # 0-10
    emotions: Dict[str, float] = field(default_factory=dict)  # 情绪标签
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'event': self.event,
            'importance': self.importance,
            'emotions': self.emotions
        }

@dataclass
class Relationship:
    """关系"""
    target_id: str
    type: RelationshipType
    trust: float = 0.0      # -100 到 100
    affection: float = 0.0  # 好感度
    history: List[Memory] = field(default_factory=list)

# ============ 核心类 ============

class World:
    """世界 - 容器和规则引擎"""
    
    def __init__(self):
        self.time = datetime(2024, 1, 1, 8, 0)  # 起始时间
        self.tick = 0
        self.agents: Dict[str, 'Agent'] = {}
        self.resources: Dict[Tuple[int, int], Dict] = {}  # 位置 -> 资源
        self.buildings: Dict[Tuple[int, int], Dict] = {}  # 位置 -> 建筑
        self.events: List[Dict] = []  # 世界事件日志
        
        # 生态参数
        self.resource_regen_rate = 0.1  # 资源再生率
        self.weather = 'sunny'  # 天气
        
        self._init_world()
    
    def _init_world(self):
        """初始化世界"""
        # 生成初始资源
        for _ in range(50):
            x = random.randint(-50, 50)
            y = random.randint(-50, 50)
            self.resources[(x, y)] = {
                'type': random.choice([ResourceType.FOOD, ResourceType.WOOD, ResourceType.STONE]),
                'amount': random.randint(5, 20),
                'quality': random.uniform(0.5, 1.0)
            }
    
    def update(self, delta_ticks: int = 1):
        """更新世界"""
        self.tick += delta_ticks
        
        # 时间推进
        minutes_passed = delta_ticks / TICKS_PER_HOUR * 60
        self.time += timedelta(minutes=minutes_passed)
        
        # 资源再生
        if random.random() < self.resource_regen_rate:
            self._spawn_resource()
        
        # 更新所有AI
        for agent in self.agents.values():
            agent.update(delta_ticks)
        
        # 处理交互
        self._process_interactions()
    
    def _spawn_resource(self):
        """生成新资源"""
        x = random.randint(-100, 100)
        y = random.randint(-100, 100)
        if (x, y) not in self.resources:
            self.resources[(x, y)] = {
                'type': random.choice(list(ResourceType)),
                'amount': random.randint(3, 10),
                'quality': random.uniform(0.5, 1.0)
            }
    
    def _process_interactions(self):
        """处理AI之间的交互"""
        # 找出距离近的AI
        agent_list = list(self.agents.values())
        for i, a1 in enumerate(agent_list):
            for a2 in agent_list[i+1:]:
                dist = abs(a1.x - a2.x) + abs(a1.y - a2.y)
                if dist <= 2:  # 相邻
                    a1.encounter(a2)
                    a2.encounter(a1)
    
    def get_time_of_day(self) -> str:
        """获取时间段"""
        hour = self.time.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def is_night(self) -> bool:
        """是否夜晚"""
        return self.time.hour >= NIGHT_START or self.time.hour < DAY_START


class Agent:
    """AI生命体 - 自主决策的个体"""
    
    def __init__(self, agent_id: str, name: str, world: World):
        self.id = agent_id
        self.name = name
        self.world = world
        
        # 位置
        self.x = random.randint(-20, 20)
        self.y = random.randint(-20, 20)
        
        # 生理状态
        self.alive = True
        self.age = 0
        
        # 需求系统（核心）
        self.needs = {
            NeedType.SURVIVAL: Need(NeedType.SURVIVAL, "生存", 100, 100, 0.5),
            NeedType.SAFETY: Need(NeedType.SAFETY, "安全", 80, 100, 0.2),
            NeedType.BELONGING: Need(NeedType.BELONGING, "归属", 60, 100, 0.3),
            NeedType.ESTEEM: Need(NeedType.ESTEEM, "尊重", 50, 100, 0.15),
            NeedType.SELF_ACTUALIZATION: Need(NeedType.SELF_ACTUALIZATION, "自我实现", 30, 100, 0.1),
        }
        
        # 资源
        self.inventory: Dict[ResourceType, float] = {
            ResourceType.FOOD: 10,
            ResourceType.WATER: 10,
        }
        self.money = random.randint(10, 50)
        
        # 技能
        self.skills = {skill: random.uniform(0.1, 0.5) for skill in SkillType}
        self.occupation = None  # 职业
        
        # 社会关系
        self.relationships: Dict[str, Relationship] = {}
        self.reputation = 0  # 声望
        
        # 记忆
        self.memories: List[Memory] = []
        self.short_term_memory = []  # 最近事件
        
        # 当前状态
        self.state = 'idle'  # idle, working, sleeping, socializing, traveling
        self.current_action = None
        self.action_timer = 0
        
        # 性格
        self.personality = {
            'aggression': random.uniform(0, 1),
            'sociability': random.uniform(0, 1),
            'curiosity': random.uniform(0, 1),
            'greed': random.uniform(0, 1),
            'altruism': random.uniform(0, 1),
        }
        
        # 住所
        self.home = None
    
    def update(self, delta_ticks: int):
        """AI更新 - 每tick调用"""
        if not self.alive:
            return
        
        # 更新需求
        for need in self.needs.values():
            need.update(delta_ticks / TICKS_PER_HOUR)
        
        # 检查生存
        if self.needs[NeedType.SURVIVAL].current <= 0:
            self._die("饥饿")
            return
        
        # 决策
        if self.action_timer <= 0:
            self._decide_action()
        else:
            self._continue_action(delta_ticks)
        
        self.age += delta_ticks / TICKS_PER_HOUR / 24  # 年龄增长
    
    def _decide_action(self):
        """决策下一步行动 - 核心AI逻辑"""
        # 按优先级排序需求
        urgent_needs = sorted(
            self.needs.values(),
            key=lambda n: n.priority,
            reverse=True
        )
        
        top_need = urgent_needs[0]
        
        # 根据最紧迫需求决策
        if top_need.type == NeedType.SURVIVAL and top_need.priority > 0.7:
            self._handle_survival_need()
        
        elif top_need.type == NeedType.SAFETY and top_need.priority > 0.5:
            self._handle_safety_need()
        
        elif top_need.type == NeedType.BELONGING and top_need.priority > 0.4:
            self._handle_social_need()
        
        elif top_need.type == NeedType.ESTEEM:
            self._handle_esteem_need()
        
        else:
            self._handle_self_actualization()
        
        # 记录决策
        self._add_memory(f"决定{self.current_action}", importance=3)
    
    def _handle_survival_need(self):
        """处理生存需求"""
        # 找食物
        if self.inventory.get(ResourceType.FOOD, 0) < 5:
            # 寻找食物资源
            food_source = self._find_resource(ResourceType.FOOD)
            if food_source:
                self.state = 'working'
                self.current_action = 'gathering_food'
                self.target = food_source
                self.action_timer = 30
            else:
                # 尝试交易获取食物
                self._try_trade_for(ResourceType.FOOD)
        else:
            # 进食
            self._eat()
    
    def _handle_safety_need(self):
        """处理安全需求"""
        if not self.home:
            # 建造住所
            if self._has_resources_for_home():
                self.state = 'working'
                self.current_action = 'building_home'
                self.action_timer = 120
            else:
                # 收集建材
                self._gather_building_materials()
        elif self.world.is_night():
            # 夜晚回家
            self.state = 'sleeping'
            self.current_action = 'sleeping_at_home'
            self.action_timer = 240  # 睡4小时
    
    def _handle_social_need(self):
        """处理社交需求"""
        # 找朋友
        if self.relationships:
            # 找关系好的
            friends = [r for r in self.relationships.values() 
                      if r.type in [RelationshipType.FRIEND, RelationshipType.CLOSE_FRIEND]]
            if friends:
                target = random.choice(friends)
                self.state = 'socializing'
                self.current_action = 'visiting_friend'
                self.target = target.target_id
                self.action_timer = 60
                return
        
        # 没有朋友，尝试结交
        self.state = 'traveling'
        self.current_action = 'looking_for_people'
        self.target = (random.randint(-30, 30), random.randint(-30, 30))
        self.action_timer = 60
    
    def _handle_esteem_need(self):
        """处理尊重需求"""
        # 提升技能或赚钱
        if random.random() < 0.5:
            self.state = 'working'
            self.current_action = 'practicing_skill'
            self.action_timer = 90
        else:
            self.state = 'working'
            self.current_action = 'trading'
            self.action_timer = 60
    
    def _handle_self_actualization(self):
        """处理自我实现"""
        # 探索或创造
        self.state = 'traveling'
        self.current_action = 'exploring'
        self.target = (random.randint(-50, 50), random.randint(-50, 50))
        self.action_timer = 120
    
    def _continue_action(self, delta_ticks: int):
        """继续当前行动"""
        self.action_timer -= delta_ticks
        
        if self.current_action == 'gathering_food':
            self._gather(ResourceType.FOOD)
        
        elif self.current_action == 'building_home':
            self._build_home()
        
        elif self.current_action == 'sleeping_at_home':
            self._sleep(delta_ticks)
        
        elif self.current_action == 'traveling' or self.current_action == 'looking_for_people':
            self._move_toward_target()
        
        elif self.current_action == 'socializing':
            self._socialize()
    
    def _gather(self, resource_type: ResourceType):
        """采集资源"""
        # 简化：直接获得资源
        amount = self.skills[SkillType.GATHERING] * 2
        self.inventory[resource_type] = self.inventory.get(resource_type, 0) + amount
        
        # 消耗生存需求（采集很累）
        self.needs[NeedType.SURVIVAL].current -= 5
        
        # 提升技能
        self.skills[SkillType.GATHERING] = min(1.0, self.skills[SkillType.GATHERING] + 0.01)
    
    def _eat(self):
        """进食"""
        if self.inventory.get(ResourceType.FOOD, 0) >= 1:
            self.inventory[ResourceType.FOOD] -= 1
            self.needs[NeedType.SURVIVAL].satisfy(30)
            self._add_memory("吃了一顿饭", importance=2)
    
    def _sleep(self, delta_ticks: int):
        """睡觉"""
        # 恢复需求
        hours_slept = delta_ticks / TICKS_PER_HOUR
        self.needs[NeedType.SURVIVAL].satisfy(hours_slept * 10)
        self.needs[NeedType.SAFETY].satisfy(hours_slept * 5)
    
    def _move_toward_target(self):
        """向目标移动"""
        if isinstance(self.target, tuple):
            tx, ty = self.target
            dx = 1 if tx > self.x else -1 if tx < self.x else 0
            dy = 1 if ty > self.y else -1 if ty < self.y else 0
            self.x += dx
            self.y += dy
    
    def _socialize(self):
        """社交"""
        # 简化：满足归属需求
        self.needs[NeedType.BELONGING].satisfy(10)
        self.needs[NeedType.ESTEEM].satisfy(5)
    
    def encounter(self, other: 'Agent'):
        """遇到另一个AI"""
        # 更新关系
        if other.id not in self.relationships:
            self.relationships[other.id] = Relationship(
                other.id, RelationshipType.STRANGER
            )
        
        rel = self.relationships[other.id]
        
        # 根据性格决定是否交朋友
        if self.personality['sociability'] > 0.5 and other.personality['sociability'] > 0.5:
            rel.trust += 1
            if rel.trust > 20 and rel.type == RelationshipType.STRANGER:
                rel.type = RelationshipType.ACQUAINTANCE
                self._add_memory(f"结识了{other.name}", importance=5)
        
        # 可能交易
        if random.random() < 0.3:
            self._attempt_trade(other)
    
    def _attempt_trade(self, other: 'Agent'):
        """尝试交易"""
        # 简化：资源交换
        pass
    
    def _add_memory(self, event: str, importance: float = 5):
        """添加记忆"""
        memory = Memory(
            timestamp=self.world.time,
            event=event,
            importance=importance
        )
        self.memories.append(memory)
        self.short_term_memory.append(memory)
        
        # 限制短期记忆数量
        if len(self.short_term_memory) > 10:
            self.short_term_memory.pop(0)
    
    def _die(self, cause: str):
        """死亡"""
        self.alive = False
        self.world.events.append({
            'time': self.world.time,
            'type': 'death',
            'agent': self.name,
            'cause': cause
        })
        print(f"💀 {self.name} 因{cause}去世了")
    
    # 辅助方法
    def _find_resource(self, resource_type: ResourceType) -> Optional[Tuple[int, int]]:
        """寻找资源"""
        for (x, y), res in self.world.resources.items():
            if res['type'] == resource_type and res['amount'] > 0:
                return (x, y)
        return None
    
    def _has_resources_for_home(self) -> bool:
        """检查是否有足够资源建家"""
        return (self.inventory.get(ResourceType.WOOD, 0) >= 20 and
                self.inventory.get(ResourceType.STONE, 0) >= 10)
    
    def _gather_building_materials(self):
        """收集建材"""
        if self.inventory.get(ResourceType.WOOD, 0) < 20:
            self.state = 'working'
            self.current_action = 'gathering_wood'
            self.action_timer = 60
        else:
            self.state = 'working'
            self.current_action = 'gathering_stone'
            self.action_timer = 60
    
    def _build_home(self):
        """建造家"""
        if self._has_resources_for_home():
            self.inventory[ResourceType.WOOD] -= 20
            self.inventory[ResourceType.STONE] -= 10
            self.home = (self.x, self.y)
            self.world.buildings[(self.x, self.y)] = {
                'type': 'home',
                'owner': self.id,
                'quality': self.skills[SkillType.CRAFTING]
            }
            self._add_memory("建造了自己的家", importance=8)
            self.needs[NeedType.SAFETY].satisfy(50)
    
    def _try_trade_for(self, resource_type: ResourceType):
        """尝试交易获取资源"""
        # 简化实现
        pass
    
    def get_status(self) -> Dict:
        """获取状态摘要"""
        return {
            'name': self.name,
            'state': self.state,
            'action': self.current_action,
            'position': (self.x, self.y),
            'needs': {n.name: f"{n.current:.0f}" for n in self.needs.values()},
            'inventory': {k.value: f"{v:.1f}" for k, v in self.inventory.items()},
            'home': self.home is not None,
            'friends': len([r for r in self.relationships.values() 
                          if r.type in [RelationshipType.FRIEND, RelationshipType.CLOSE_FRIEND]])
        }


class Simulation:
    """模拟主控"""
    
    def __init__(self):
        self.world = World()
        self.running = False
        self.speed = 1  # 速度倍率
        
        # 创建初始AI
        self._create_initial_agents()
    
    def _create_initial_agents(self):
        """创建初始AI"""
        names = ["小蓝", "小红", "小绿", "小黄", "小紫"]
        for i, name in enumerate(names):
            agent = Agent(f"agent_{i}", name, self.world)
            self.world.agents[agent.id] = agent
    
    async def run(self):
        """运行模拟"""
        self.running = True
        print("🌍 AnotherYou ECO 启动")
        print("=" * 50)
        
        tick = 0
        while self.running:
            # 更新世界
            self.world.update(self.speed)
            
            # 每10tick输出状态
            if tick % 10 == 0:
                self._print_status()
            
            tick += 1
            
            # 控制速度
            await asyncio.sleep(0.1 / self.speed)
    
    def _print_status(self):
        """打印状态"""
        print(f"\n📅 Day {self.world.time.day}, {self.world.time.strftime('%H:%M')}")
        print(f"👥 人口: {len([a for a in self.world.agents.values() if a.alive])}")
        print(f"🏠 建筑: {len(self.world.buildings)}")
        print(f"🌾 资源点: {len(self.world.resources)}")
        
        print("\nAI状态:")
        for agent in self.world.agents.values():
            if agent.alive:
                status = agent.get_status()
                print(f"  {status['name']}: {status['action']} | "
                      f"生存{status['needs']['生存']} | "
                      f"归属{status['needs']['归属']} | "
                      f"{'有家' if status['home'] else '无家'} | "
                      f"{status['friends']}朋友")


if __name__ == "__main__":
    sim = Simulation()
    asyncio.run(sim.run())
