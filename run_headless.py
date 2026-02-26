"""
Headless Runner - 无显示器版本
在服务器后台运行，输出日志到文件
"""

import asyncio
import random
import json
import time
from datetime import datetime
from typing import Dict, List
import os
import sys

sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.living_world import (
    LivingWorld, LivingAgent, 
    Season, Weather, AdminMode
)

class HeadlessRunner:
    """无界面运行器"""
    
    def __init__(self):
        self.world = LivingWorld(width=100, height=100)
        self.tick_count = 0
        self.log_file = "/tmp/another_you_eco.log"
        self.snapshot_dir = "/tmp/eco_snapshots"
        
        # 创建快照目录
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        # 创建初始AI
        for i in range(10):
            agent = LivingAgent(
                id=f"agent_{i}",
                name=f"AI-{i}",
                x=random.randint(40, 60),
                y=random.randint(40, 60)
            )
            self.world.agents[agent.id] = agent
            
        self.log("🌍 AnotherYou ECO v0.4 - Headless Mode")
        self.log("=" * 50)
        
    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        # 写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            
    def get_world_state(self) -> Dict:
        """获取世界状态"""
        alive_agents = [a for a in self.world.agents.values() if a.alive]
        
        return {
            "tick": self.world.time.tick,
            "time": str(self.world.time),
            "weather": str(self.world.weather),
            "season": self.world.time.season.value,
            "hour": self.world.time.hour,
            "alive_count": len(alive_agents),
            "total_agents": len(self.world.agents),
            "events": [e.name for e in self.world.events.active_events],
        }
        
    def get_agent_details(self) -> List[Dict]:
        """获取AI详情"""
        details = []
        for agent in self.world.agents.values():
            if agent.alive:
                details.append({
                    "id": agent.id,
                    "name": agent.name,
                    "energy": round(agent.energy, 1),
                    "mood": round(agent.mood, 1),
                    "action": agent.current_action,
                    "position": (agent.x, agent.y),
                    "thought": agent.thought[:30] if agent.thought else "..."
                })
        return details
        
    async def run(self):
        """主循环"""
        self.log("启动模拟...")
        
        while True:
            # 更新世界
            self.world.update()
            
            # AI决策
            for agent in self.world.agents.values():
                if agent.alive:
                    decision = agent.decide_action(self.world)
                    # 简单执行
                    if decision.get('action') == 'move':
                        direction = decision.get('direction', 'N')
                        dx = {'N': 0, 'S': 0, 'E': 1, 'W': -1}.get(direction, 0)
                        dy = {'N': -1, 'S': 1, 'E': 0, 'W': 0}.get(direction, 0)
                        agent.x = max(0, min(99, agent.x + dx))
                        agent.y = max(0, min(99, agent.y + dy))
                        
            self.tick_count += 1
            
            # 每100 tick输出状态
            if self.tick_count % 100 == 0:
                state = self.get_world_state()
                self.log(f"⏰ {state['time']} | 🌤️ {state['weather']} | 👥 {state['alive_count']}/{state['total_agents']} AI存活")
                
                if state['events']:
                    self.log(f"   🌟 活跃事件: {', '.join(state['events'])}")
                    
            # 每500 tick输出AI详情
            if self.tick_count % 500 == 0:
                self.log("-" * 40)
                self.log("AI状态:")
                for agent in self.get_agent_details()[:5]:
                    self.log(f"  {agent['name']}: 能量{agent['energy']} 心情{agent['mood']} 行动:{agent['action']}")
                    if agent['thought'] != '...':
                        self.log(f"    💭 {agent['thought']}")
                self.log("-" * 40)
                
            # 每小时（游戏时间）保存快照
            if self.world.time.hour != getattr(self, '_last_hour', -1):
                self._last_hour = self.world.time.hour
                self.save_snapshot()
                
            await asyncio.sleep(0.1)  # 10 tick/秒
            
    def save_snapshot(self):
        """保存世界快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "world": self.get_world_state(),
            "agents": self.get_agent_details()
        }
        
        filename = f"{self.snapshot_dir}/snapshot_{self.world.time.tick}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
        self.log(f"💾 快照已保存: {filename}")


async def main():
    runner = HeadlessRunner()
    await runner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 模拟已停止")
