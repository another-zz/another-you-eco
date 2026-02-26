"""
AnotherYou ECO - LLM版可视化
使用真正的AI大脑
"""

import pygame
import asyncio
import random
from typing import Dict, List, Tuple

# 导入核心代码
import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')
from main_v3_llm import PureWorld, PureAgent, PHYSICS

# Pygame配置
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 30

# 颜色
COLORS = {
    'bg': (20, 30, 20),
    'grid': (40, 50, 40),
    'agent': {
        'idle': (100, 200, 100),
        'exploring': (100, 150, 255),
        'gathering': (255, 200, 100),
        'eating': (255, 150, 150),
        'dead': (100, 100, 100),
    },
    'object': {
        'berry_bush': (255, 50, 50),
        'tree': (34, 139, 34),
        'rock': (128, 128, 128),
        'water_source': (65, 105, 225),
    },
    'ui_bg': (30, 30, 30),
    'ui_text': (255, 255, 255),
    'ui_highlight': (255, 215, 0),
    'thought': (255, 255, 200),
}


class LLMVisualizer:
    """LLM版可视化器"""
    
    def __init__(self, world: PureWorld):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO - LLM大脑观测台")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('microsoftyahei', 14)
        self.font_large = pygame.font.SysFont('microsoftyahei', 20)
        self.font_small = pygame.font.SysFont('microsoftyahei', 12)
        
        self.world = world
        self.camera = {'x': 0, 'y': 0, 'zoom': 1.0}
        self.selected_agent = None
        self.paused = False
        self.speed = 1
        
        # 轨迹
        self.trails: Dict[str, List[Tuple[int, int]]] = {}
        
    def world_to_screen(self, wx: int, wy: int) -> Tuple[int, int]:
        """世界坐标转屏幕坐标"""
        sx = int(wx * 20 * self.camera['zoom'] - self.camera['x'])
        sy = int(wy * 20 * self.camera['zoom'] - self.camera['y'])
        return sx, sy
        
    def handle_input(self):
        """处理输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    self._select_agent(mx, my)
                    
        return True
    
    def _select_agent(self, mx: int, my: int):
        """选择AI"""
        for agent in self.world.agents.values():
            ax, ay = self.world_to_screen(agent.x, agent.y)
            if (ax - mx) ** 2 + (ay - my) ** 2 < 400:
                self.selected_agent = agent
                return
        self.selected_agent = None
        
    async def update(self):
        """更新"""
        if not self.paused:
            for _ in range(self.speed):
                # 更新所有AI
                for agent in list(self.world.agents.values()):
                    if agent.alive:
                        perception = agent.perceive()
                        decision = await agent.think_async(perception)
                        agent.act(decision)
                        
                        # 记录轨迹
                        if agent.id not in self.trails:
                            self.trails[agent.id] = []
                        self.trails[agent.id].append((agent.x, agent.y))
                        if len(self.trails[agent.id]) > 50:
                            self.trails[agent.id].pop(0)
                            
                self.world.tick += 1
                
    def render(self):
        """渲染"""
        self.screen.fill(COLORS['bg'])
        
        # 绘制网格
        for x in range(0, SCREEN_WIDTH, 20):
            pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 20):
            pygame.draw.line(self.screen, COLORS['grid'], (0, y), (SCREEN_WIDTH, y))
        
        # 绘制物体
        for obj in self.world.objects.values():
            x, y = self.world_to_screen(obj.x, obj.y)
            color = COLORS['object'].get(obj.type, (150, 150, 150))
            pygame.draw.circle(self.screen, color, (x, y), 6)
        
        # 绘制AI
        for agent in self.world.agents.values():
            x, y = self.world_to_screen(agent.x, agent.y)
            
            # 颜色根据状态
            color = COLORS['agent']['idle'] if agent.alive else COLORS['agent']['dead']
            
            # 绘制AI
            pygame.draw.circle(self.screen, color, (x, y), 10)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 10, 2)
            
            # 能量条
            if agent.alive:
                bar_width = 20
                energy_pct = agent.energy / PHYSICS['energy']['max']
                pygame.draw.rect(self.screen, (50, 50, 50), (x - 10, y - 18, bar_width, 4))
                pygame.draw.rect(self.screen, (0, 255, 0) if energy_pct > 0.5 else (255, 0, 0),
                               (x - 10, y - 18, int(bar_width * energy_pct), 4))
            
            # 想法气泡
            if agent.alive and agent.thought:
                thought_text = self.font_small.render(agent.thought[:20], True, COLORS['thought'])
                self.screen.blit(thought_text, (x - 30, y - 35))
            
            # 选中高亮
            if agent == self.selected_agent:
                pygame.draw.circle(self.screen, (255, 215, 0), (x, y), 15, 2)
        
        # UI
        self._draw_ui()
        
        pygame.display.flip()
        
    def _draw_ui(self):
        """绘制UI"""
        # 顶部信息
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (0, 0, SCREEN_WIDTH, 40))
        
        alive_count = len([a for a in self.world.agents.values() if a.alive])
        info = f"Tick: {self.world.tick} | 存活: {alive_count} | 速度: {self.speed}x"
        if self.paused:
            info += " [暂停]"
        
        text = self.font_large.render(info, True, COLORS['ui_text'])
        self.screen.blit(text, (10, 10))
        
        # 选中AI详情
        if self.selected_agent:
            self._draw_agent_panel()
        
        # 底部提示
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        hint = "空格:暂停 | 1-2:速度 | 左键:选择AI"
        text = self.font.render(hint, True, (150, 150, 150))
        self.screen.blit(text, (10, SCREEN_HEIGHT - 25))
        
    def _draw_agent_panel(self):
        """绘制AI详情"""
        panel_x = SCREEN_WIDTH - 300
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (panel_x, 50, 290, 300))
        
        agent = self.selected_agent
        y = 60
        
        # ID
        title = self.font_large.render(f"AI: {agent.id[:10]}", True, COLORS['ui_highlight'])
        self.screen.blit(title, (panel_x + 10, y))
        y += 30
        
        # 状态
        status = "存活" if agent.alive else "死亡"
        text = self.font.render(f"状态: {status}", True, COLORS['ui_text'])
        self.screen.blit(text, (panel_x + 10, y))
        y += 25
        
        if agent.alive:
            text = self.font.render(f"能量: {agent.energy:.1f}", True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            text = self.font.render(f"位置: ({agent.x}, {agent.y})", True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            # 当前想法
            y += 10
            text = self.font.render("当前想法:", True, COLORS['ui_highlight'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            thought = agent.thought[:40] if agent.thought else "..."
            text = self.font_small.render(thought, True, COLORS['thought'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            # 发现的行为
            y += 10
            text = self.font.render("已发现:", True, COLORS['ui_highlight'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            for behavior in list(agent.discovered_behaviors)[:3]:
                text = self.font_small.render(f"• {behavior}", True, (200, 200, 200))
                self.screen.blit(text, (panel_x + 10, y))
                y += 20
                
    async def run(self):
        """主循环"""
        print("🧠 AnotherYou ECO - LLM大脑版")
        print("=" * 40)
        print("每个AI都有自己的LLM大脑，真正自主思考")
        print("=" * 40)
        
        running = True
        while running:
            running = self.handle_input()
            await self.update()
            self.render()
            self.clock.tick(FPS)
            await asyncio.sleep(0)
            
        pygame.quit()


async def main():
    world = PureWorld()
    
    # 创建几个AI
    for i in range(3):
        agent = PureAgent(f"llm_agent_{i}", world)
        world.agents[agent.id] = agent
    
    visualizer = LLMVisualizer(world)
    await visualizer.run()


if __name__ == "__main__":
    asyncio.run(main())
