"""
Agent Core - AI角色核心系统
记忆 + 规划 + 行动 + 反思
参考 Stanford Smallville + Voyager
"""

import json
import sqlite3
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import os

# 数据库路径
DB_PATH = os.path.expanduser("~/.another_you/agents.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@dataclass
class Memory:
    """记忆条目"""
    timestamp: str
    content: str
    importance: float  # 0-10
    memory_type: str  # observation, reflection, plan, action
    
@dataclass
class Skill:
    """技能"""
    name: str
    description: str
    success_count: int = 0
    fail_count: int = 0
    learned_at: str = ""
    
class MemoryStream:
    """记忆流 - Stanford Smallville风格"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: List[Memory] = []
        self._init_db()
        self._load_memories()
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                timestamp TEXT,
                content TEXT,
                importance REAL,
                memory_type TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def _load_memories(self):
        """从数据库加载记忆"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, content, importance, memory_type FROM memories WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 100",
            (self.agent_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        self.memories = [
            Memory(ts, content, imp, mtype)
            for ts, content, imp, mtype in rows
        ]
        
    def add(self, content: str, importance: float = 5, memory_type: str = "observation"):
        """添加记忆"""
        memory = Memory(
            timestamp=datetime.now().isoformat(),
            content=content,
            importance=importance,
            memory_type=memory_type
        )
        self.memories.insert(0, memory)
        
        # 保存到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (agent_id, timestamp, content, importance, memory_type) VALUES (?, ?, ?, ?, ?)",
            (self.agent_id, memory.timestamp, content, importance, memory_type)
        )
        conn.commit()
        conn.close()
        
    def retrieve(self, query: str, k: int = 5) -> List[Memory]:
        """检索相关记忆（简化版，实际用向量相似度）"""
        # 按重要性 + 时间衰减 + 关键词匹配
        scored = []
        for i, m in enumerate(self.memories[:50]):
            recency = 1.0 - (i / 50)
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
        # 获取今天的高重要性事件
        today_events = [m for m in self.memories if m.importance >= 6][:10]
        
        if not today_events:
            return ""
            
        # 分析主题
        themes = {}
        for e in today_events:
            content = e.content.lower()
            if any(word in content for word in ['食物', '吃', '饿']):
                themes['生存'] = themes.get('生存', 0) + 1
            if any(word in content for word in ['朋友', '聊天', '社交']):
                themes['社交'] = themes.get('社交', 0) + 1
            if any(word in content for word in ['建', '造', '房子']):
                themes['建设'] = themes.get('建设', 0) + 1
            if any(word in content for word in ['钱', '金币', '交易']):
                themes['经济'] = themes.get('经济', 0) + 1
                
        if themes:
            main_theme = max(themes, key=themes.get)
            reflection = f"今天主要关注{main_theme}，这是当前最优先的需求。"
            self.add(reflection, importance=8, memory_type="reflection")
            return reflection
        return ""


class SkillLibrary:
    """技能库 - Voyager风格终身学习"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.skills: Dict[str, Skill] = {}
        self._init_db()
        self._load_skills()
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                name TEXT UNIQUE,
                description TEXT,
                success_count INTEGER,
                fail_count INTEGER,
                learned_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def _load_skills(self):
        """加载技能"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, description, success_count, fail_count, learned_at FROM skills WHERE agent_id = ?",
            (self.agent_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        for name, desc, success, fail, learned in rows:
            self.skills[name] = Skill(name, desc, success, fail, learned)
            
    def learn(self, name: str, description: str) -> bool:
        """学习新技能"""
        if name in self.skills:
            return False
            
        skill = Skill(
            name=name,
            description=description,
            learned_at=datetime.now().isoformat()
        )
        self.skills[name] = skill
        
        # 保存到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO skills (agent_id, name, description, success_count, fail_count, learned_at) VALUES (?, ?, ?, 0, 0, ?)",
            (self.agent_id, name, description, skill.learned_at)
        )
        conn.commit()
        conn.close()
        return True
        
    def record_success(self, name: str):
        """记录技能成功使用"""
        if name in self.skills:
            self.skills[name].success_count += 1
            self._update_skill(name)
            
    def record_fail(self, name: str):
        """记录技能失败"""
        if name in self.skills:
            self.skills[name].fail_count += 1
            self._update_skill(name)
            
    def _update_skill(self, name: str):
        """更新技能记录"""
        skill = self.skills[name]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE skills SET success_count = ?, fail_count = ? WHERE agent_id = ? AND name = ?",
            (skill.success_count, skill.fail_count, self.agent_id, name)
        )
        conn.commit()
        conn.close()
        
    def get_skills_summary(self) -> str:
        """获取技能摘要"""
        if not self.skills:
            return "还没有学会任何技能"
        return "、".join([f"{s.name}({s.success_count})" for s in list(self.skills.values())[:5]])


class HighLevelPlanner:
    """高级规划器 - 生成长期目标"""
    
    GOALS = [
        ("建造自己的房子", 0.3),
        ("赚取100金币", 0.25),
        ("结交3个朋友", 0.2),
        ("探索整个地图", 0.15),
        ("学会采集技能", 0.1),
    ]
    
    def __init__(self, memory: MemoryStream, skills: SkillLibrary):
        self.memory = memory
        self.skills = skills
        self.current_goal: Optional[str] = None
        self.goal_progress = 0
        
    def generate_daily_goal(self, context: Dict) -> str:
        """生成每日目标"""
        # 基于当前状态选择目标
        energy = context.get('energy', 100)
        money = context.get('money', 0)
        
        # 如果能量低，优先找食物
        if energy < 40:
            self.current_goal = "寻找食物恢复能量"
            return self.current_goal
            
        # 如果钱少，优先赚钱
        if money < 50:
            self.current_goal = "采集资源出售赚钱"
            return self.current_goal
            
        # 随机选择长期目标
        goals = [g for g, _ in self.GOALS]
        weights = [w for _, w in self.GOALS]
        
        # 根据已有技能调整权重
        if '采集' in self.skills.get_skills_summary():
            weights[4] = 0.02  # 降低学习采集的优先级
            
        self.current_goal = random.choices(goals, weights=weights)[0]
        return self.current_goal
        
    def break_into_subgoals(self) -> List[str]:
        """将目标分解为子目标"""
        if not self.current_goal:
            return []
            
        subgoals_map = {
            "建造自己的房子": ["采集木材", "采集石材", "寻找建造地点", "开始建造"],
            "赚取100金币": ["寻找资源", "采集资源", "寻找商人", "出售资源"],
            "结交3个朋友": ["寻找其他AI", "主动打招呼", "帮助对方", "建立友谊"],
            "探索整个地图": ["向东探索", "向西探索", "向南探索", "向北探索"],
            "学会采集技能": ["找到资源点", "尝试采集", "总结经验"],
            "寻找食物恢复能量": ["寻找食物来源", "采集食物", "食用食物"],
            "采集资源出售赚钱": ["寻找贵重资源", "大量采集", "寻找买家"],
        }
        
        return subgoals_map.get(self.current_goal, ["探索周围环境"])


class ReActLoop:
    """ReAct循环 - Observe → Think → Plan → Act"""
    
    def __init__(self, memory: MemoryStream, planner: HighLevelPlanner, skills: SkillLibrary):
        self.memory = memory
        self.planner = planner
        self.skills = skills
        
    def observe(self, context: Dict) -> Dict:
        """观察环境"""
        observations = {
            'time': context.get('time', '12:00'),
            'location': context.get('location', (0, 0)),
            'nearby_objects': context.get('nearby', []),
            'energy': context.get('energy', 100),
            'mood': context.get('mood', 50),
        }
        
        # 记录观察
        if observations['nearby_objects']:
            obj_names = [o.get('type', 'unknown') for o in observations['nearby_objects'][:3]]
            self.memory.add(f"看到: {', '.join(obj_names)}", importance=3)
            
        return observations
        
    def think(self, observations: Dict) -> str:
        """思考"""
        # 检索相关记忆
        query = f"{observations['location']} {observations.get('nearby_objects', [])}"
        relevant_memories = self.memory.retrieve(query, k=3)
        
        # 简单思考逻辑（实际用LLM）
        thoughts = []
        
        if observations['energy'] < 30:
            thoughts.append("能量很低，需要找食物")
        elif observations['energy'] < 60:
            thoughts.append("能量中等，可以继续当前任务")
        else:
            thoughts.append("能量充足，可以执行计划")
            
        # 基于记忆调整
        for mem in relevant_memories:
            if '危险' in mem.content or '死亡' in mem.content:
                thoughts.append("记得这里有危险，要小心")
                
        return "; ".join(thoughts) if thoughts else "继续执行计划"
        
    def plan(self, thoughts: str, observations: Dict) -> str:
        """规划行动"""
        # 如果没有目标或目标完成，生成新目标
        if not self.planner.current_goal:
            self.planner.generate_daily_goal(observations)
            
        subgoals = self.planner.break_into_subgoals()
        if subgoals:
            current_subgoal = subgoals[0]
            return current_subgoal
        return "探索"
        
    def act(self, plan: str, context: Dict) -> Dict:
        """执行行动"""
        action = {"type": "idle", "target": None}
        
        if "采集" in plan:
            action = {"type": "gather", "target": context.get('nearest_resource')}
        elif "寻找" in plan or "探索" in plan:
            # 随机方向移动
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            dx, dy = random.choice(directions)
            action = {"type": "move", "dx": dx, "dy": dy}
        elif "建造" in plan:
            action = {"type": "build", "target": context.get('build_location')}
        elif "社交" in plan or "打招呼" in plan:
            action = {"type": "social", "target": context.get('nearest_agent')}
            
        # 记录行动
        self.memory.add(f"执行: {plan}", importance=4, memory_type="action")
        
        return action
        
    def step(self, context: Dict) -> Dict:
        """执行一步ReAct循环"""
        observations = self.observe(context)
        thoughts = self.think(observations)
        plan = self.plan(thoughts, observations)
        action = self.act(plan, context)
        
        return {
            'observations': observations,
            'thoughts': thoughts,
            'plan': plan,
            'action': action
        }


class AgentCore:
    """AI角色核心 - 整合所有系统"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        
        # 核心系统
        self.memory = MemoryStream(agent_id)
        self.skills = SkillLibrary(agent_id)
        self.planner = HighLevelPlanner(self.memory, self.skills)
        self.react = ReActLoop(self.memory, self.planner, self.skills)
        
        # 状态
        self.energy = 100.0
        self.mood = 70.0
        self.money = random.randint(50, 200)
        self.x = 50.0
        self.y = 50.0
        
        # 当前行动
        self.current_action = "idle"
        self.action_target = None
        self.thought_bubble = "..."
        
    def update(self, dt: float, world_context: Dict) -> Dict:
        """更新AI状态"""
        # 能量消耗
        self.energy -= 0.02 * dt
        if self.energy < 0:
            self.energy = 0
            
        # ReAct循环
        result = self.react.step(world_context)
        
        self.current_action = result['action']['type']
        self.action_target = result['action'].get('target')
        self.thought_bubble = result['thoughts'][:30] + "..." if len(result['thoughts']) > 30 else result['thoughts']
        
        # 执行移动
        if result['action']['type'] == 'move':
            dx = result['action'].get('dx', 0) * dt * 2
            dy = result['action'].get('dy', 0) * dt * 2
            self.x = max(0, min(99, self.x + dx))
            self.y = max(0, min(99, self.y + dy))
            
        return result
        
    def daily_reflection(self):
        """每日反思"""
        reflection = self.memory.daily_reflection()
        if reflection:
            print(f"🧠 {self.name}: {reflection}")
            
    def on_player_takeover(self):
        """玩家接管时调用"""
        self.memory.add("玩家接管了控制", importance=7)
        
    def on_player_release(self, player_actions: List[str]):
        """玩家释放控制时调用"""
        # 反思玩家做了什么
        action_summary = "、".join(player_actions) if player_actions else "移动了一段距离"
        reflection = f"玩家让我做了: {action_summary}。我需要调整计划。"
        self.memory.add(reflection, importance=8, memory_type="reflection")
        
        # 可能学会新技能
        if "采集" in action_summary and "采集" not in self.skills.get_skills_summary():
            self.skills.learn("基础采集", "从环境中采集资源")
            print(f"📚 {self.name} 学会了基础采集!")
            
    def get_state(self) -> Dict:
        """获取状态"""
        return {
            'id': self.agent_id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'energy': self.energy,
            'mood': self.mood,
            'money': self.money,
            'goal': self.planner.current_goal or "无目标",
            'thought': self.thought_bubble,
            'skills': self.skills.get_skills_summary(),
            'action': self.current_action,
        }
