"""
AI Brain v0.2 - LLM智能大脑
基于调研报告升级：LangGraph + 向量记忆
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MemorySystem:
    """向量记忆系统 - 借鉴斯坦福Generative Agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memories: List[Dict] = []  # 记忆流
        self.reflections: List[Dict] = []  # 反思（高层次洞察）
        
        # 尝试使用向量数据库
        try:
            from langchain.embeddings import OpenAIEmbeddings
            from langchain.vectorstores import Chroma
            
            self.embeddings = OpenAIEmbeddings(
                api_key=os.getenv('OPENAI_API_KEY')
            )
            self.vectorstore = Chroma(
                collection_name=f"agent_{agent_id}",
                embedding_function=self.embeddings
            )
            self.use_vector = True
        except:
            self.use_vector = False
            print(f"⚠️ Agent {agent_id} 使用简化记忆系统")
    
    def add_memory(self, event: str, importance: float = 5, 
                   emotions: Dict[str, float] = None):
        """添加记忆"""
        memory = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'importance': importance,
            'emotions': emotions or {},
            'access_count': 0,
            'last_accessed': datetime.now().isoformat()
        }
        
        self.memories.append(memory)
        
        # 向量存储
        if self.use_vector:
            try:
                self.vectorstore.add_texts(
                    [event],
                    metadatas=[memory]
                )
            except Exception as e:
                print(f"向量存储失败: {e}")
        
        # 保持记忆数量合理
        if len(self.memories) > 100:
            # 删除重要性最低且久未访问的记忆
            self.memories.sort(key=lambda m: m['importance'] + m.get('access_count', 0))
            self.memories = self.memories[50:]  # 保留50条
    
    def retrieve(self, query: str, k: int = 5) -> List[str]:
        """检索相关记忆"""
        # 更新访问计数
        for m in self.memories[-10:]:  # 最近10条增加权重
            m['access_count'] = m.get('access_count', 0) + 1
        
        if self.use_vector:
            try:
                results = self.vectorstore.similarity_search(query, k=k)
                return [r.page_content for r in results]
            except:
                pass
        
        # 简化检索：返回最近的重要记忆
        recent = sorted(self.memories, key=lambda m: m['timestamp'], reverse=True)[:5]
        return [m['event'] for m in recent]
    
    def reflect(self) -> List[str]:
        """
        反思机制 - 每天总结形成洞察
        借鉴斯坦福论文
        """
        if len(self.memories) < 10:
            return []
        
        # 找出高频主题
        recent_events = [m['event'] for m in self.memories[-20:]]
        
        # 简化：返回最近记忆的总结
        insights = []
        
        # 检查是否有模式
        work_count = sum(1 for e in recent_events if '采集' in e or '建造' in e)
        social_count = sum(1 for e in recent_events if '朋友' in e or '交易' in e)
        
        if work_count > 10:
            insights.append("我最近工作很努力")
        if social_count > 5:
            insights.append("我交了很多新朋友")
        
        return insights


class AIBrainV2:
    """AI大脑 v0.2 - LLM驱动"""
    
    def __init__(self, agent_id: str, name: str, personality: Dict):
        self.agent_id = agent_id
        self.name = name
        self.personality = personality
        
        # 记忆系统
        self.memory = MemorySystem(agent_id)
        
        # LLM配置
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.enabled = bool(self.api_key and self.api_key != 'your_openai_api_key_here')
        
        if self.enabled:
            try:
                from langchain.chat_models import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7,
                    api_key=self.api_key
                )
                print(f"🧠 {name} 的AI大脑已激活")
            except Exception as e:
                print(f"⚠️ LLM初始化失败: {e}")
                self.enabled = False
    
    def think(self, context: Dict) -> Dict:
        """
        思考决策 - 核心AI逻辑
        借鉴AutoGPT：观察→记忆检索→规划→行动
        """
        # 1. 检索相关记忆
        situation = f"当前{context.get('state')}，需求{context.get('top_need')}"
        relevant_memories = self.memory.retrieve(situation, k=5)
        reflections = self.memory.reflect()
        
        # 2. 使用LLM决策（如果启用）
        if self.enabled:
            return self._llm_decide(context, relevant_memories, reflections)
        
        # 3. 简化决策（备用）
        return self._rule_based_decide(context)
    
    def _llm_decide(self, context: Dict, memories: List[str], 
                    reflections: List[str]) -> Dict:
        """LLM决策"""
        
        prompt = f"""你是{self.name}，一个生活在虚拟世界中的AI。

你的性格:
- 攻击性: {self.personality.get('aggression', 0.5):.1f}
- 社交性: {self.personality.get('sociability', 0.5):.1f}
- 好奇心: {self.personality.get('curiosity', 0.5):.1f}
- 贪婪度: {self.personality.get('greed', 0.5):.1f}

当前状态:
- 位置: ({context.get('x', 0)}, {context.get('y', 0)})
- 状态: {context.get('state', 'idle')}
- 最紧迫需求: {context.get('top_need', '无')}
- 饥饿度: {context.get('hunger', 100):.0f}
- 能量: {context.get('energy', 100):.0f}
- 背包: {context.get('inventory', {})}

相关记忆:
{chr(10).join(f"- {m}" for m in memories[:3])}

自我反思:
{chr(10).join(f"- {r}" for r in reflections)}

请决定下一步行动。输出JSON格式:
{{
    "action": "行动类型(gather/build/trade/social/explore/rest)",
    "target": "具体目标",
    "reasoning": "决策理由",
    "duration": "预计持续时间(分钟)"
}}"""

        try:
            response = self.llm.predict(prompt)
            result = json.loads(response)
            
            # 记录决策记忆
            self.memory.add_memory(
                f"决定{result.get('action')}，因为{result.get('reasoning', '无')}",
                importance=4
            )
            
            return result
        
        except Exception as e:
            print(f"LLM决策失败: {e}")
            return self._rule_based_decide(context)
    
    def _rule_based_decide(self, context: Dict) -> Dict:
        """规则-based决策（备用）"""
        need = context.get('top_need', 'survival')
        
        actions = {
            'survival': {'action': 'gather', 'target': 'food', 'reasoning': '需要食物'},
            'safety': {'action': 'build', 'target': 'home', 'reasoning': '需要住所'},
            'belonging': {'action': 'social', 'target': 'friend', 'reasoning': '需要社交'},
            'esteem': {'action': 'trade', 'target': 'market', 'reasoning': '需要财富'},
        }
        
        return actions.get(need, {'action': 'explore', 'target': 'world', 'reasoning': '探索'})
    
    def generate_dialogue(self, other_name: str, relationship: float, 
                         context: str) -> str:
        """生成自然对话"""
        
        if not self.enabled:
            return self._default_dialogue(other_name, relationship)
        
        # 检索与这个人相关的记忆
        memories = self.memory.retrieve(f"与{other_name}的", k=3)
        
        prompt = f"""你是{self.name}，正在和{other_name}对话。

关系: {'朋友' if relationship > 20 else '熟人' if relationship > 0 else '陌生人'}
场景: {context}

相关记忆:
{chr(10).join(f"- {m}" for m in memories)}

请生成一句自然的对话（20字以内）:"""

        try:
            response = self.llm.predict(prompt)
            dialogue = response.strip().strip('"')
            
            # 记录对话
            self.memory.add_memory(f"对{other_name}说: {dialogue}", importance=3)
            
            return dialogue
        except:
            return self._default_dialogue(other_name, relationship)
    
    def _default_dialogue(self, other_name: str, relationship: float) -> str:
        """默认对话"""
        if relationship > 20:
            return f"{other_name}，好久不见！"
        elif relationship > 0:
            return f"嗨，{other_name}"
        else:
            return "你好"
    
    def negotiate_price(self, item: str, buyer: bool, 
                       market_price: float) -> float:
        """谈判价格 - 借鉴经济系统"""
        
        # 根据性格调整
        if buyer:
            # 买家想低价
            greed = self.personality.get('greed', 0.5)
            return market_price * (0.8 - greed * 0.2)
        else:
            # 卖家想高价
            greed = self.personality.get('greed', 0.5)
            return market_price * (1.0 + greed * 0.3)
