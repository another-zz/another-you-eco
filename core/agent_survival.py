"""
Agent Survival - AI生存系统
能量管理 + 进食 + 睡觉 + 复活
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SurvivalNeeds:
    """生存需求"""
    energy: float = 100.0
    hunger: float = 0.0  # 0-100，越高越饿
    health: float = 100.0
    rest_need: float = 0.0  # 休息需求
    
    # 阈值
    CRITICAL_ENERGY = 30.0
    LOW_ENERGY = 50.0
    CRITICAL_HUNGER = 70.0
    
class SurvivalSystem:
    """生存系统"""
    
    def __init__(self, agent_core):
        self.agent = agent_core
        self.needs = SurvivalNeeds()
        
        # 家/睡觉地点
        self.home_location: Optional[Tuple[int, int]] = None
        self.is_sleeping = False
        
        # 食物库存
        self.food_inventory = 0
        
        # 死亡状态
        self.is_dead = False
        self.death_time = 0
        self.respawn_timer = 0
        self.RESPAWN_TIME = 86400  # 24秒（游戏时间）后复活
        
        # 天气影响
        self.weather_multiplier = 1.0
        
    def set_home(self, x: int, y: int):
        """设置家"""
        self.home_location = (x, y)
        
    def update(self, dt: float, weather_effects: Dict, hour: int):
        """更新生存状态"""
        if self.is_dead:
            self._update_death(dt)
            return
            
        # 应用天气影响
        self.weather_multiplier = weather_effects.get('energy_drain', 1.0)
        
        # 基础消耗
        base_drain = 0.02 * dt * self.weather_multiplier
        
        # 移动消耗更多
        if self.agent.current_action == 'move':
            base_drain *= 1.5
            
        # 睡觉恢复
        if self.is_sleeping:
            self.needs.energy += 0.1 * dt
            self.needs.hunger += 0.01 * dt
            self.needs.rest_need -= 0.2 * dt
            
            # 夜晚睡觉效果更好
            if hour < 6 or hour > 20:
                self.needs.energy += 0.05 * dt
        else:
            self.needs.energy -= base_drain
            self.needs.hunger += 0.015 * dt
            self.needs.rest_need += 0.01 * dt
            
        # 限制范围
        self.needs.energy = max(0, min(100, self.needs.energy))
        self.needs.hunger = max(0, min(100, self.needs.hunger))
        self.needs.rest_need = max(0, min(100, self.needs.rest_need))
        
        # 饥饿影响健康
        if self.needs.hunger > 80:
            self.needs.health -= 0.05 * dt
        elif self.needs.hunger < 20 and self.needs.energy > 50:
            self.needs.health = min(100, self.needs.health + 0.02 * dt)
            
        # 检查死亡
        if self.needs.energy <= 0 or self.needs.health <= 0:
            self._die()
            
    def _update_death(self, dt: float):
        """更新死亡状态"""
        self.respawn_timer += dt
        if self.respawn_timer >= self.RESPAWN_TIME:
            self._respawn()
            
    def _die(self):
        """死亡"""
        self.is_dead = True
        self.death_time = 0
        self.respawn_timer = 0
        print(f"💀 {self.agent.name} 因能量耗尽死亡，将在24小时后复活")
        
    def _respawn(self):
        """复活"""
        self.is_dead = False
        self.needs.energy = 50.0
        self.needs.hunger = 50.0
        self.needs.health = 80.0
        self.needs.rest_need = 0.0
        self.respawn_timer = 0
        
        # 记录复活
        self.agent.memory.add("从死亡中复活，失去了一些记忆", importance=9)
        print(f"✨ {self.agent.name} 已复活")
        
    def eat(self, food_amount: float = 20.0) -> bool:
        """进食"""
        if self.food_inventory > 0:
            self.food_inventory -= 1
            self.needs.hunger = max(0, self.needs.hunger - food_amount)
            self.needs.energy = min(100, self.needs.energy + food_amount * 0.5)
            self.agent.memory.add("吃了一顿饭，感觉好多了", importance=4)
            return True
        return False
        
    def gather_food(self, location_type: str) -> float:
        """采集食物"""
        food_gained = 0
        
        if location_type == 'water':
            # 钓鱼
            food_gained = random.uniform(10, 25)
            self.agent.memory.add("在河边钓到了鱼", importance=3)
        elif location_type == 'forest':
            # 采集浆果
            food_gained = random.uniform(5, 15)
            self.agent.memory.add("在森林采集了浆果", importance=3)
        elif location_type == 'grass':
            # 采集野菜
            food_gained = random.uniform(3, 10)
            
        if food_gained > 0:
            self.food_inventory += 1
            
        return food_gained
        
    def sleep(self):
        """开始睡觉"""
        if not self.is_sleeping:
            self.is_sleeping = True
            self.agent.memory.add("开始睡觉休息", importance=3)
            
    def wake_up(self):
        """醒来"""
        if self.is_sleeping:
            self.is_sleeping = False
            self.agent.memory.add("睡醒了，精神焕发", importance=3)
            
    def should_sleep(self, hour: int) -> bool:
        """判断是否应该睡觉"""
        # 夜晚
        if hour >= 22 or hour <= 5:
            return True
        # 能量低
        if self.needs.energy < self.needs.CRITICAL_ENERGY:
            return True
        # 休息需求高
        if self.needs.rest_need > 70:
            return True
        return False
        
    def get_survival_priority(self) -> str:
        """获取生存优先级行动"""
        # 最高优先级：濒死
        if self.needs.energy < 20 or self.needs.health < 30:
            return 'critical_survival'
            
        # 高优先级：能量低
        if self.needs.energy < self.needs.CRITICAL_ENERGY:
            return 'find_food'
            
        # 中优先级：饥饿
        if self.needs.hunger > self.needs.CRITICAL_HUNGER:
            return 'eat_food'
            
        # 低优先级：休息
        if self.needs.rest_need > 50:
            return 'rest'
            
        return 'normal'
        
    def get_status_color(self) -> Tuple[int, int, int]:
        """获取状态颜色（用于显示）"""
        if self.is_dead:
            return (100, 100, 100)  # 灰色
        if self.needs.energy < 30:
            return (255, 50, 50)    # 红色
        if self.needs.energy < 60:
            return (255, 200, 50)   # 黄色
        return (50, 255, 100)       # 绿色
        
    def get_status_emoji(self) -> str:
        """获取状态emoji"""
        if self.is_dead:
            return '💀'
        if self.is_sleeping:
            return '💤'
        if self.needs.energy < 30:
            return '⚠️'
        if self.needs.hunger > 70:
            return '🍽️'
        return '✅'
