"""
Kimi Brain - 接入月之暗面 Kimi Coding API
修复代理和兼容性问题
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp

class KimiBrain:
    """Kimi Coding AI 大脑"""
    
    def __init__(self, agent_id: str, personality: Dict):
        self.agent_id = agent_id
        self.personality = personality
        
        # Kimi API 配置
        self.api_key = os.getenv('KIMI_API_KEY', 'sk-kimi-2ntHyfQuoYBjZCVVOggMDOzbDGA7pYcH8pJZDTpYUNGMpSf8VMKOYDq8npxqXtet')
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "kimi-coding"
        
        self.enabled = bool(self.api_key)
        self.session = None
        
        # 禁用代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        
        if self.enabled:
            print(f"🌙 {agent_id} Kimi大脑已激活")
        
        # 对话历史
        self.conversation_history = []
        
    async def _get_session(self):
        """获取aiohttp会话（无代理）"""
        if self.session is None or self.session.closed:
            # 明确禁用代理
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(
                connector=connector,
                trust_env=False  # 不信任环境代理设置
            )
        return self.session
        
    async def think(self, context: Dict) -> Dict:
        """AI思考决策"""
        if not self.enabled:
            return self._local_decision(context)
        
        try:
            return await self._kimi_decision(context)
        except Exception as e:
            print(f"Kimi决策失败: {e}")
            return self._local_decision(context)
    
    async def _kimi_decision(self, context: Dict) -> Dict:
        """使用Kimi API进行决策"""
        
        system_prompt = f"""你是Agent {self.agent_id}，一个生活在虚拟世界中的AI生命体。

你的性格特质:
- 好奇心: {self.personality.get('curiosity', 0.5):.1f}/1.0
- 攻击性: {self.personality.get('aggression', 0.5):.1f}/1.0  
- 社交性: {self.personality.get('sociability', 0.5):.1f}/1.0
- 坚持度: {self.personality.get('persistence', 0.5):.1f}/1.0

世界规则:
1. 你有能量值，每秒消耗0.1，耗尽会死亡
2. 你可以移动(N/S/E/W)和互动
3. 视野范围内可以看到物体和其他AI
4. 互动物体可能获得能量或资源
5. 你需要自己发现什么是有益的，什么是有害的

重要: 你必须基于自己的观察和推理做出决策，而不是预设行为。
请用中文思考和回复。"""

        user_prompt = self._build_state_prompt(context)
        
        # 使用aiohttp直接调用API（避免httpx代理问题）
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"API错误: {response.status} - {text[:200]}")
                    return self._local_decision(context)
                
                data = await response.json()
                content = data['choices'][0]['message']['content']
                
                # 解析响应
                result = self._parse_response(content)
                decision = self._validate_decision(result, context)
                
                print(f"🌙 {self.agent_id}: {decision.get('reasoning', '思考中...')[:40]}")
                
                return decision
                
        except Exception as e:
            print(f"API调用失败: {e}")
            return self._local_decision(context)
    
    def _build_state_prompt(self, context: Dict) -> str:
        """构建状态提示"""
        
        self_state = context.get('self', {})
        energy = self_state.get('energy', 0)
        position = self_state.get('position', (0, 0))
        
        # 可见物体
        objects = context.get('objects', [])
        objects_desc = []
        for obj in objects[:5]:
            obj_type = obj.get('type', 'unknown')
            distance = obj.get('distance', 0)
            direction = obj.get('direction', '?')
            props = obj.get('properties', {})
            
            desc = f"- {obj_type} 在{direction}方向{distance}格"
            if 'edible' in props:
                desc += f" (可食用)"
            objects_desc.append(desc)
        
        # 可见AI
        agents = context.get('agents', [])
        agents_desc = []
        for agent in agents[:3]:
            desc = f"- AI {agent.get('id', '?')[:8]} 在{agent.get('direction', '?')}方向"
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
    "reasoning": "你的思考过程，为什么做这个决定（用中文）",
    "expected_outcome": "你期望发生什么"
}}"""

        return prompt
    
    def _parse_response(self, content: str) -> Dict:
        """解析响应"""
        try:
            # 查找JSON部分
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
                
            return json.loads(json_str.strip())
        except:
            # 文本解析
            return self._parse_text_response(content)
    
    def _parse_text_response(self, content: str) -> Dict:
        """解析文本响应"""
        content_lower = content.lower()
        
        action = "wait"
        if "移动" in content or "走" in content or "move" in content_lower:
            action = "move"
        elif "互动" in content or "交互" in content or "interact" in content_lower:
            action = "interact"
            
        direction = "N"
        if "北" in content or "north" in content_lower:
            direction = "N"
        elif "南" in content or "south" in content_lower:
            direction = "S"
        elif "东" in content or "east" in content_lower:
            direction = "E"
        elif "西" in content or "west" in content_lower:
            direction = "W"
            
        return {
            "action": action,
            "direction": direction,
            "reasoning": content[:80],
            "expected_outcome": "未知"
        }
    
    def _validate_decision(self, result: Dict, context: Dict) -> Dict:
        """验证和补充决策"""
        action = result.get('action', 'wait')
        
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
            valid_targets = [o['id'] for o in context.get('objects', [])]
            valid_targets += [a['id'] for a in context.get('agents', [])]
            
            if target_id not in valid_targets:
                if context.get('objects'):
                    target_id = context['objects'][0]['id']
                else:
                    action = 'wait'
                    decision['action'] = 'wait'
            
            decision['target_id'] = target_id
        
        return decision
    
    def _local_decision(self, context: Dict) -> Dict:
        """本地规则决策（备用）"""
        import random
        
        energy = context.get('self', {}).get('energy', 50)
        objects = context.get('objects', [])
        
        if energy < 40:
            for obj in objects:
                if obj.get('properties', {}).get('edible'):
                    return {
                        'action': 'interact',
                        'target_id': obj['id'],
                        'reasoning': '能量低，寻找食物',
                        'expected_outcome': '获得能量'
                    }
        
        return {
            'action': 'move',
            'direction': random.choice(['N', 'S', 'E', 'W']),
            'reasoning': '探索周围环境',
            'expected_outcome': '发现新事物'
        }
    
    async def generate_thought(self, context: Dict) -> str:
        """生成AI当前的想法"""
        if not self.enabled:
            return "..."
        
        try:
            energy = context.get('self', {}).get('energy', 50)
            
            session = await self._get_session()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"你当前能量{energy:.0f}。用10个字以内表达你现在的想法："
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 20
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content'].strip('"').strip()
                    
        except:
            pass
            
        return "..."
