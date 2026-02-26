"""
LLM Brain - 真正的AI思考系统
使用OpenAI API让AI自主决策
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class LLMBrain:
    """LLM大脑 - 真正的智能决策"""
    
    def __init__(self, agent_id: str, personality: Dict):
        self.agent_id = agent_id
        self.personality = personality
        
        # OpenAI配置
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model = os.getenv('AI_MODEL', 'gpt-4o-mini')
        
        self.enabled = bool(self.api_key and self.api_key != 'your_openai_api_key_here')
        self.client = None
        
        if self.enabled:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                print(f"🧠 {agent_id} LLM大脑已激活 ({self.model})")
            except Exception as e:
                print(f"⚠️ LLM初始化失败: {e}")
                self.enabled = False
        else:
            print(f"⚠️ {agent_id} 使用本地规则引擎 (无API密钥)")
    
    async def think(self, context: Dict) -> Dict:
        """
        AI思考决策
        
        输入: 当前感知到的世界状态
        输出: 决策动作
        """
        if not self.enabled or not self.client:
            return self._local_decision(context)
        
        try:
            return await self._llm_decision(context)
        except Exception as e:
            print(f"LLM决策失败: {e}, 使用本地规则")
            return self._local_decision(context)
    
    async def _llm_decision(self, context: Dict) -> Dict:
        """使用LLM进行决策"""
        
        # 构建系统提示
        system_prompt = f"""你是Agent {self.agent_id}，一个生活在虚拟世界中的AI生命体。

你的性格特质:
- 好奇心: {self.personality.get('curiosity', 0.5):.1f}/1.0 (越高越喜欢探索)
- 攻击性: {self.personality.get('aggression', 0.5):.1f}/1.0 (越高越具竞争性)
- 社交性: {self.personality.get('sociability', 0.5):.1f}/1.0 (越高越喜欢互动)
- 坚持度: {self.personality.get('persistence', 0.5):.1f}/1.0 (越高越坚持目标)

世界规则:
1. 你有能量值，每秒消耗0.1，耗尽会死亡
2. 你可以移动(N/S/E/W)和互动
3. 视野范围内可以看到物体和其他AI
4. 互动物体可能获得能量或资源
5. 你需要自己发现什么是有益的，什么是有害的

重要: 你必须基于自己的观察和推理做出决策，而不是预设行为。"""

        # 构建当前状态
        user_prompt = self._build_state_prompt(context)
        
        # 调用LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # 解析响应
        result = json.loads(response.choices[0].message.content)
        
        # 验证和补充
        decision = self._validate_decision(result, context)
        
        print(f"🤖 {self.agent_id}: {decision.get('reasoning', '思考中...')}")
        
        return decision
    
    def _build_state_prompt(self, context: Dict) -> str:
        """构建状态提示"""
        
        # 自身状态
        self_state = context.get('self', {})
        energy = self_state.get('energy', 0)
        position = self_state.get('position', (0, 0))
        
        # 可见物体
        objects = context.get('objects', [])
        objects_desc = []
        for obj in objects[:5]:  # 最多5个
            obj_type = obj.get('type', 'unknown')
            distance = obj.get('distance', 0)
            direction = obj.get('direction', '?')
            props = obj.get('properties', {})
            
            desc = f"- {obj_type} 在{direction}方向{distance}格"
            if 'edible' in props:
                desc += f" (可食用,营养{props.get('nutrition', 0)})"
            if 'material' in props:
                desc += f" (材料:{props['material']})"
            objects_desc.append(desc)
        
        # 可见其他AI
        agents = context.get('agents', [])
        agents_desc = []
        for agent in agents[:3]:
            desc = f"- AI {agent.get('id', '?')[:8]} 在{agent.get('direction', '?')}方向{agent.get('distance', 0)}格"
            if agent.get('action'):
                desc += f" 正在{agent['action']}"
            agents_desc.append(desc)
        
        # 已发现的行为
        discovered = context.get('discovered_behaviors', [])
        
        prompt = f"""当前状态:

【自身】
- 能量: {energy:.1f}/100 ({'危险!' if energy < 30 else '偏低' if energy < 50 else '正常'})
- 位置: ({position[0]}, {position[1]})

【视野内物体】
{chr(10).join(objects_desc) if objects_desc else '无'}

【视野内其他AI】
{chr(10).join(agents_desc) if agents_desc else '无其他AI'}

【已发现的知识】
{chr(10).join(f'- {b}' for b in discovered[-5:]) if discovered else '还没有发现'}

请基于以上信息，决定下一步行动。

输出JSON格式:
{{
    "action": "move/interact/wait",
    "direction": "N/S/E/W (如果是move)",
    "target_id": "目标ID (如果是interact)",
    "reasoning": "你的思考过程，为什么做这个决定",
    "expected_outcome": "你期望发生什么"
}}"""

        return prompt
    
    def _validate_decision(self, result: Dict, context: Dict) -> Dict:
        """验证和补充决策"""
        action = result.get('action', 'wait')
        
        # 确保action有效
        if action not in ['move', 'interact', 'wait']:
            action = 'wait'
        
        decision = {
            'action': action,
            'reasoning': result.get('reasoning', '没有思考过程'),
            'expected_outcome': result.get('expected_outcome', '未知'),
        }
        
        if action == 'move':
            direction = result.get('direction', 'N')
            if direction not in ['N', 'S', 'E', 'W']:
                direction = 'N'
            decision['direction'] = direction
            decision['distance'] = 1
            
        elif action == 'interact':
            target_id = result.get('target_id', '')
            # 验证目标是否存在
            valid_targets = [o['id'] for o in context.get('objects', [])]
            valid_targets += [a['id'] for a in context.get('agents', [])]
            
            if target_id not in valid_targets:
                # 选择最近的物体
                if context.get('objects'):
                    target_id = context['objects'][0]['id']
                else:
                    action = 'wait'
                    decision['action'] = 'wait'
            
            decision['target_id'] = target_id
        
        return decision
    
    def _local_decision(self, context: Dict) -> Dict:
        """本地规则决策（LLM失败时备用）"""
        
        energy = context.get('self', {}).get('energy', 50)
        objects = context.get('objects', [])
        
        # 能量低时寻找食物
        if energy < 40:
            for obj in objects:
                if obj.get('properties', {}).get('edible'):
                    return {
                        'action': 'interact',
                        'target_id': obj['id'],
                        'reasoning': '能量低，寻找食物',
                        'expected_outcome': '获得能量'
                    }
        
        # 随机移动
        import random
        return {
            'action': 'move',
            'direction': random.choice(['N', 'S', 'E', 'W']),
            'reasoning': '探索周围环境',
            'expected_outcome': '发现新事物'
        }
    
    async def reflect(self, experiences: List[Dict]) -> str:
        """
        反思最近的经历，形成洞察
        借鉴斯坦福Generative Agents
        """
        if not self.enabled or not experiences:
            return ""
        
        try:
            prompt = f"""基于以下经历，总结你学到了什么：

{chr(10).join(f"- {e.get('event', '未知事件')}" for e in experiences[-5:])}

用一句话总结你的新发现或洞察："""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            insight = response.choices[0].message.content.strip()
            print(f"💡 {self.agent_id} 反思: {insight}")
            return insight
            
        except Exception as e:
            return ""
    
    async def generate_thought_bubble(self, context: Dict) -> str:
        """生成AI当前的想法（用于显示）"""
        if not self.enabled:
            return "..."
        
        try:
            energy = context.get('self', {}).get('energy', 50)
            
            prompt = f"""你当前能量{energy:.0f}，正在{context.get('action', 'idle')}。
用10个字以内表达你现在的想法或感受："""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=20
            )
            
            return response.choices[0].message.content.strip('"')
            
        except:
            return "..."
