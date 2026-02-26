"""
Agent Survival - AI生存系统
防止集体死亡
"""

import random
from typing import Dict, Tuple

class SurvivalSystem:
    """生存系统"""
    
    def __init__(self):
        self.energy = 100.0
        self.hunger = 0.0
        self.health = 100.0
        self.is_dead = False
        self.is_sleeping = False
        self.food_inventory = 2  # 初始食物
        
    def update(self, dt: float, weather_effects: Dict, hour: int):
        """更新生存状态"""
        if self.is_dead:
            return
            
        # 天气影响
        energy_drain = weather_effects.get('energy_drain', 1.0)
        
        # 基础消耗
        base_drain = 0.015 * dt * energy_drain
        
        # 睡觉恢复
        if self.is_sleeping:
            self.energy += 0.15 * dt
            self.hunger += 0.01 * dt
            if hour < 6 or hour > 20:
                self.energy += 0.08 * dt
        else:
            self.energy -= base_drain
            self.hunger += 0.012 * dt
            
        # 限制
        self.energy = max(0, min(100, self.energy))
        self.hunger = max(0, min(100, self.hunger))
        
        # 饥饿影响
        if self.hunger > 80:
            self.energy -= 0.05 * dt
            
        # 检查死亡
        if self.energy <= 0:
            self.is_dead = True
            print(f"💀 AI因能量耗尽死亡")
            
    def get_priority(self) -> str:
        """获取生存优先级"""
        if self.is_dead:
            return 'dead'
        if self.energy < 25:
            return 'critical'
        if self.energy < 45:
            return 'low_energy'
        if self.hunger > 70:
            return 'hungry'
        if self.is_sleeping and self.energy > 80:
            return 'wake_up'
        return 'normal'
        
    def should_sleep(self, hour: int) -> bool:
        """是否应该睡觉"""
        if self.energy < 35:
            return True
        if hour >= 22 or hour <= 5:
            return True
        return False
        
    def eat(self) -> bool:
        """进食"""
        if self.food_inventory > 0:
            self.food_inventory -= 1
            self.hunger = max(0, self.hunger - 30)
            self.energy = min(100, self.energy + 15)
            return True
        return False
        
    def gather_food(self, tile_type: str) -> bool:
        """采集食物"""
        if tile_type == 'water' and random.random() < 0.3:
            self.food_inventory += 1
            return True
        if tile_type == 'forest' and random.random() < 0.2:
            self.food_inventory += 1
            return True
        return False
