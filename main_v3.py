"""
AnotherYou ECO v0.3 - 纯自主演化
只给物理规则，让AI自然发现一切
"""

import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto

# ============ 基础物理规则（不可修改） ============

PHYSICS = {
    # 能量系统
    'energy': {
        'max': 100,
        'decay_rate': 0.1,  # 每秒消耗
        'critical': 20,     # 危险阈值
    },
    # 世界规则
    'world': {
        'day_length': 600,  # 10分钟一天
        'season_length': 10,  # 10天一季
    },
    # 资源生成
    'resource_spawn': {
        'rate': 0.01,  # 每tick生成概率
        'types': ['berry_bush', 'tree', 'rock', 'water_source'],
    }
}

class PhysicalObject:
    """物理对象 - 世界中的实体"""
    
    def __init__(self, obj_id: str, obj_type: str, x: int, y: int):
        self.id = obj_id
        self.type = obj_type
        self.x = x
        self.y = y
        self.properties = {}
        
        # 根据类型设置物理属性
        if obj_type == 'berry_bush':
            self.properties = {
                'edible': True,
                'nutrition': 15,
                'amount': random.randint(3, 8),
                'regrow_time': 300,  # 5分钟再生
            }
        elif obj_type == 'tree':
            self.properties = {
                'edible': False,
                'material': 'wood',
                'hardness': 3,
            }
        elif obj_type == 'rock':
            self.properties = {
                'edible': False,
                'material': 'stone',
                'hardness': 5,
            }
        elif obj_type == 'water_source':
            self.properties = {
                'drinkable': True,
                'hydration': 20,
            }


from ai.llm_brain import LLMBrain

class PureAgent:
    """
    纯AI生命体 - 只给物理身体，不给行为预设
    
    AI必须自己发现：
    - 饿了要吃东西（而不是预设"寻找食物"行为）
    - 可以采集/种植/交易（自己发明）
    - 可以社交/合作/竞争（自然涌现）
    """
    
    def __init__(self, agent_id: str, world: 'PureWorld'):
        self.id = agent_id
        self.world = world
        
        # === 物理身体（不可修改） ===
        self.x = random.randint(-50, 50)
        self.y = random.randint(-50, 50)
        self.energy = 80.0  # 能量，耗尽=死亡
        self.alive = True
        self.age = 0
        
        # === 感知能力（传感器） ===
        self.sight_range = 10  # 视野范围
        self.memory_capacity = 100  # 记忆容量
        
        # === 执行能力（执行器） ===
        self.can_move = True
        self.can_interact = True
        self.inventory_size = 10
        
        # === AI自己发现的一切（初始为空） ===
        self.discovered_behaviors: Set[str] = set()  # 发现的行为
        self.knowledge: Dict[str, any] = {}  # 知识库
        self.beliefs: Dict[str, float] = {}  # 信念（"采集比狩猎好"）
        self.skills: Dict[str, float] = {}  # 技能水平
        
        # 原始记忆（原始感知记录）
        self.raw_experiences: List[Dict] = []
        
        # 社会关系（自主形成）
        self.known_agents: Dict[str, Dict] = {}  # 对其他AI的认知
        
        # 当前状态
        self.current_action = None
        self.action_target = None
        
        # 遗传性格（影响探索倾向）
        self.traits = {
            'curiosity': random.uniform(0.3, 0.9),      # 好奇心
            'aggression': random.uniform(0.1, 0.6),     # 攻击性
            'sociability': random.uniform(0.2, 0.8),    # 社交倾向
            'persistence': random.uniform(0.3, 0.9),    # 坚持度
        }
        
        # LLM大脑
        self.brain = LLMBrain(self.id, self.traits)
        self.thought = "..."  # 当前想法
    
    async def think_async(self, perception: Dict) -> Dict:
        """
        感知环境 - AI的传感器
        返回原始数据，AI自己解释含义
        """
        # 视野内的物体
        visible_objects = []
        for obj in self.world.objects.values():
            dist = abs(obj.x - self.x) + abs(obj.y - self.y)
            if dist <= self.sight_range:
                visible_objects.append({
                    'id': obj.id,
                    'type': obj.type,
                    'distance': dist,
                    'direction': self._get_direction(obj.x, obj.y),
                    'properties': obj.properties,
                })
        
        # 视野内的其他AI
        visible_agents = []
        for agent in self.world.agents.values():
            if agent.id != self.id and agent.alive:
                dist = abs(agent.x - self.x) + abs(agent.y - self.y)
                if dist <= self.sight_range:
                    visible_agents.append({
                        'id': agent.id,
                        'distance': dist,
                        'direction': self._get_direction(agent.x, agent.y),
                        'action': agent.current_action,
                    })
        
        # 自身状态
        self_state = {
            'energy': self.energy,
            'position': (self.x, self.y),
            'inventory': self._get_inventory(),
        }
        
        return {
            'objects': visible_objects,
            'agents': visible_agents,
            'self': self_state,
            'time': self.world.tick,
        }
    
    async def think_async(self, perception: Dict) -> Dict:
        """
        思考决策 - AI的核心（异步版本，支持LLM）
        """
        # 记录经验
        self._record_experience(perception)
        
        # 添加发现的行为到上下文
        perception['discovered_behaviors'] = list(self.discovered_behaviors)
        
        # 使用LLM大脑决策
        decision = await self.brain.think(perception)
        
        # 更新想法气泡
        self.thought = decision.get('reasoning', '...')[:30]
        
        return decision
    
    def think(self, perception: Dict) -> Dict:
        """
        思考决策 - AI的核心
        
        没有预设行为！AI必须：
        1. 解释感知（"那个红色物体是什么？"）
        2. 回忆经验（"上次碰到它发生了什么？"）
        3. 形成目标（"我需要能量"）
        4. 选择行动（"尝试吃那个物体"）
        """
        
        # 记录经验
        self._record_experience(perception)
        
        # 基础生存驱动（本能，不是预设行为）
        if self.energy < PHYSICS['energy']['critical']:
            # 能量危急 - 必须行动，但AI自己决定如何
            return self._survival_decision(perception)
        
        # 正常状态 - AI自主探索
        return self._exploratory_decision(perception)
    
    def _survival_decision(self, perception: Dict) -> Dict:
        """
        生存决策 - 能量危急时
        AI必须自己发现如何获取能量
        """
        # 检查已知能获取能量的方法
        known_methods = [b for b in self.discovered_behaviors 
                        if 'energy' in b or 'eat' in b or 'food' in b]
        
        if known_methods:
            # 使用已知方法
            method = random.choice(known_methods)
            return self._execute_known_method(method, perception)
        
        # 不知道方法 - 随机尝试（探索）
        return self._random_exploration(perception, urgent=True)
    
    def _exploratory_decision(self, perception: Dict) -> Dict:
        """
        探索决策 - 正常状态时
        AI自由探索世界，发现规律
        """
        # 好奇心驱动
        if random.random() < self.traits['curiosity']:
            return self._random_exploration(perception, urgent=False)
        
        # 重复已知有效行为
        if self.discovered_behaviors:
            method = random.choice(list(self.discovered_behaviors))
            return self._execute_known_method(method, perception)
        
        # 默认：随机移动
        return {'action': 'move', 'direction': random.choice(['N', 'S', 'E', 'W'])}
    
    def _random_exploration(self, perception: Dict, urgent: bool) -> Dict:
        """随机探索 - 尝试新行为"""
        # 可能的原始动作
        actions = ['move', 'interact', 'wait']
        
        if urgent:
            # 危急时偏向移动和互动
            action = random.choices(actions, weights=[0.5, 0.4, 0.1])[0]
        else:
            action = random.choice(actions)
        
        if action == 'move':
            return {
                'action': 'move',
                'direction': random.choice(['N', 'S', 'E', 'W']),
                'distance': random.randint(1, 5)
            }
        
        elif action == 'interact':
            # 随机选择一个附近物体互动
            if perception['objects']:
                target = random.choice(perception['objects'])
                return {
                    'action': 'interact',
                    'target_id': target['id'],
                    'interaction_type': 'unknown',  # AI不知道会发生什么
                }
        
        return {'action': 'wait', 'duration': 10}
    
    def _execute_known_method(self, method: str, perception: Dict) -> Dict:
        """执行已知方法"""
        # 解析方法（简单字符串匹配）
        if 'move_to' in method:
            # 移动到某类物体
            obj_type = method.replace('move_to_', '')
            for obj in perception['objects']:
                if obj['type'] == obj_type:
                    return {
                        'action': 'move',
                        'target': (obj['distance'], obj['direction'])
                    }
        
        elif 'eat' in method:
            # 吃某类物体
            for obj in perception['objects']:
                if obj['properties'].get('edible'):
                    return {
                        'action': 'interact',
                        'target_id': obj['id'],
                        'expected': 'energy_gain'
                    }
        
        # 方法失效，重新探索
        return self._random_exploration(perception, urgent=False)
    
    def act(self, decision: Dict):
        """执行行动"""
        action = decision.get('action')
        
        if action == 'move':
            self._move(decision)
        
        elif action == 'interact':
            self._interact(decision)
        
        elif action == 'wait':
            pass  # 什么都不做
        
        self.current_action = action
        
        # 消耗能量
        self.energy -= PHYSICS['energy']['decay_rate']
        
        if self.energy <= 0:
            self._die("能量耗尽")
    
    def _move(self, decision: Dict):
        """移动"""
        direction = decision.get('direction')
        distance = decision.get('distance', 1)
        
        dx, dy = 0, 0
        if direction == 'N': dy = -1
        elif direction == 'S': dy = 1
        elif direction == 'E': dx = 1
        elif direction == 'W': dx = -1
        
        # 移动
        for _ in range(distance):
            new_x, new_y = self.x + dx, self.y + dy
            # 检查碰撞
            if self.world.is_passable(new_x, new_y):
                self.x, self.y = new_x, new_y
    
    def _interact(self, decision: Dict):
        """互动 - 与世界物体互动"""
        target_id = decision.get('target_id')
        target = self.world.objects.get(target_id)
        
        if not target:
            return
        
        # 记录这次互动
        interaction = {
            'time': self.world.tick,
            'target_type': target.type,
            'target_properties': target.properties.copy(),
        }
        
        # 尝试"吃"
        if target.properties.get('edible') and target.properties.get('amount', 0) > 0:
            nutrition = target.properties['nutrition']
            self.energy = min(PHYSICS['energy']['max'], self.energy + nutrition)
            target.properties['amount'] -= 1
            
            interaction['result'] = 'energy_gain'
            interaction['energy_change'] = +nutrition
            
            # 发现！吃这个能获得能量
            self._discover(f"eat_{target.type}")
            self._learn(f"{target.type}提供能量")
        
        # 尝试收集材料
        elif target.properties.get('material'):
            material = target.properties['material']
            self._add_to_inventory(material, 1)
            
            interaction['result'] = 'collected'
            interaction['material'] = material
            
            self._discover(f"collect_{material}")
        
        self.raw_experiences.append(interaction)
    
    def _discover(self, behavior: str):
        """发现新行为"""
        if behavior not in self.discovered_behaviors:
            self.discovered_behaviors.add(behavior)
            print(f"🌟 {self.id} 发现了: {behavior}")
            
            # 告知世界（可能传播给其他AI）
            self.world.record_discovery(self.id, behavior)
    
    def _learn(self, knowledge: str):
        """学习知识"""
        self.knowledge[knowledge] = self.world.tick
    
    def _record_experience(self, perception: Dict):
        """记录经验"""
        if len(self.raw_experiences) > self.memory_capacity:
            self.raw_experiences.pop(0)
    
    def _get_direction(self, target_x: int, target_y: int) -> str:
        """获取方向"""
        dx = target_x - self.x
        dy = target_y - self.y
        
        if abs(dx) > abs(dy):
            return 'E' if dx > 0 else 'W'
        else:
            return 'S' if dy > 0 else 'N'
    
    def _get_inventory(self) -> Dict:
        """获取背包"""
        return getattr(self, '_inventory', {})
    
    def _add_to_inventory(self, item: str, amount: int):
        """添加物品到背包"""
        if not hasattr(self, '_inventory'):
            self._inventory = {}
        self._inventory[item] = self._inventory.get(item, 0) + amount
    
    def _die(self, cause: str):
        """死亡"""
        self.alive = False
        self.world.record_death(self.id, cause)
    
    def update(self):
        """更新 - 每tick调用"""
        if not self.alive:
            return
        
        # 感知
        perception = self.perceive()
        
        # 思考
        decision = self.think(perception)
        
        # 行动
        self.act(decision)
        
        # 年龄增长
        self.age += 1


class PureWorld:
    """纯净世界 - 只提供物理环境"""
    
    def __init__(self):
        self.tick = 0
        self.agents: Dict[str, PureAgent] = {}
        self.objects: Dict[str, PhysicalObject] = {}
        
        # 事件记录
        self.discoveries: List[Dict] = []  # 所有发现
        self.deaths: List[Dict] = []  # 死亡记录
        
        self._init_world()
    
    def _init_world(self):
        """初始化世界 - 只生成物理对象"""
        # 生成初始资源
        for i in range(30):
            obj_type = random.choice(PHYSICS['resource_spawn']['types'])
            x = random.randint(-100, 100)
            y = random.randint(-100, 100)
            obj = PhysicalObject(f"obj_{i}", obj_type, x, y)
            self.objects[obj.id] = obj
        
        # 创建初始AI
        for i in range(5):
            agent = PureAgent(f"agent_{i}", self)
            self.agents[agent.id] = agent
    
    def update(self):
        """更新世界"""
        self.tick += 1
        
        # 随机生成新资源
        if random.random() < PHYSICS['resource_spawn']['rate']:
            self._spawn_resource()
        
        # 更新所有AI
        for agent in self.agents.values():
            agent.update()
        
        # 清理死亡AI
        self.agents = {k: v for k, v in self.agents.items() if v.alive}
    
    def _spawn_resource(self):
        """生成新资源"""
        obj_type = random.choice(PHYSICS['resource_spawn']['types'])
        x = random.randint(-100, 100)
        y = random.randint(-100, 100)
        obj_id = f"obj_{self.tick}_{random.randint(0, 999)}"
        obj = PhysicalObject(obj_id, obj_type, x, y)
        self.objects[obj_id] = obj
    
    def is_passable(self, x: int, y: int) -> bool:
        """检查是否可通过"""
        # 简化：世界无边界，都可通行
        return True
    
    def record_discovery(self, agent_id: str, behavior: str):
        """记录发现"""
        self.discoveries.append({
            'tick': self.tick,
            'agent': agent_id,
            'behavior': behavior
        })
    
    def record_death(self, agent_id: str, cause: str):
        """记录死亡"""
        self.deaths.append({
            'tick': self.tick,
            'agent': agent_id,
            'cause': cause
        })
        print(f"💀 {agent_id} 死亡: {cause}")
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'tick': self.tick,
            'alive_agents': len([a for a in self.agents.values() if a.alive]),
            'total_objects': len(self.objects),
            'discoveries': len(self.discoveries),
            'deaths': len(self.deaths),
        }


async def main():
    """主程序"""
    world = PureWorld()
    
    print("🌍 AnotherYou ECO v0.3 - 纯自主演化")
    print("=" * 50)
    print("物理规则:")
    print(f"  - 能量每秒消耗 {PHYSICS['energy']['decay_rate']}")
    print(f"  - 危险阈值 {PHYSICS['energy']['critical']}")
    print(f"  - 资源生成率 {PHYSICS['resource_spawn']['rate']}/tick")
    print("=" * 50)
    print("\nAI必须自己发现：")
    print("  - 什么物体可以吃")
    print("  - 如何获取能量")
    print("  - 如何与其他AI互动")
    print("\n等待发现...\n")
    
    tick = 0
    while True:
        world.update()
        tick += 1
        
        # 每100tick输出状态
        if tick % 100 == 0:
            stats = world.get_stats()
            print(f"\n[Tick {stats['tick']}] 存活: {stats['alive_agents']} | "
                  f"发现: {stats['discoveries']} | 死亡: {stats['deaths']}")
            
            # 显示AI发现
            for agent in world.agents.values():
                if agent.alive and agent.discovered_behaviors:
                    print(f"  {agent.id}: {', '.join(agent.discovered_behaviors)}")
        
        await asyncio.sleep(0.01)  # 10ms per tick


if __name__ == "__main__":
    asyncio.run(main())
