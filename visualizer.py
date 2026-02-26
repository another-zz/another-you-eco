"""
AnotherYou ECO - 可视化界面
Pygame显示AI自主演化过程
"""

import pygame
import asyncio
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass

# 导入核心代码
import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')
from main_v3 import PureWorld, PureAgent, PhysicalObject, PHYSICS

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
}


class Camera:
    """相机 - 控制视野"""
    
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.target_agent = None
        
    def follow(self, agent):
        """跟随某个AI"""
        self.target_agent = agent
        
    def update(self):
        """更新相机位置"""
        if self.target_agent and self.target_agent.alive:
            # 平滑跟随
            target_x = self.target_agent.x * 20 - SCREEN_WIDTH // 2
            target_y = self.target_agent.y * 20 - SCREEN_HEIGHT // 2
            self.x += (target_x - self.x) * 0.1
            self.y += (target_y - self.y) * 0.1
            
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """世界坐标转屏幕坐标"""
        screen_x = int(world_x * 20 * self.zoom - self.x)
        screen_y = int(world_y * 20 * self.zoom - self.y)
        return screen_x, screen_y


class Visualizer:
    """可视化器"""
    
    def __init__(self, world: PureWorld):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO - 自主演化观测台")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('microsoftyahei', 14)
        self.font_large = pygame.font.SysFont('microsoftyahei', 20)
        self.font_small = pygame.font.SysFont('microsoftyahei', 12)
        
        self.world = world
        self.camera = Camera()
        self.selected_agent = None
        self.show_trails = True
        self.paused = False
        self.speed = 1  # 1, 2, 5, 10
        
        # 轨迹记录
        self.trails: Dict[str, List[Tuple[int, int]]] = {}
        
        # 统计
        self.stats_history = []
        
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
                elif event.key == pygame.K_t:
                    self.show_trails = not self.show_trails
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                elif event.key == pygame.K_4:
                    self.speed = 10
                elif event.key == pygame.K_f:
                    # 跟随随机AI
                    if self.world.agents:
                        self.selected_agent = random.choice(list(self.world.agents.values()))
                        self.camera.follow(self.selected_agent)
                        
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键选择AI
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self._select_agent_at(mouse_x, mouse_y)
                elif event.button == 4:  # 滚轮上
                    self.camera.zoom = min(2.0, self.camera.zoom * 1.1)
                elif event.button == 5:  # 滚轮下
                    self.camera.zoom = max(0.5, self.camera.zoom / 1.1)
                    
        # 相机移动
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.camera.y -= 20
            self.camera.target_agent = None
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.camera.y += 20
            self.camera.target_agent = None
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.camera.x -= 20
            self.camera.target_agent = None
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.camera.x += 20
            self.camera.target_agent = None
            
        return True
    
    def _select_agent_at(self, screen_x: int, screen_y: int):
        """选择点击位置的AI"""
        for agent in self.world.agents.values():
            ax, ay = self.camera.world_to_screen(agent.x, agent.y)
            dist = ((ax - screen_x)**2 + (ay - screen_y)**2) ** 0.5
            if dist < 15:
                self.selected_agent = agent
                self.camera.follow(agent)
                return
        self.selected_agent = None
        
    def update(self):
        """更新状态"""
        if not self.paused:
            # 更新世界多次（根据速度）
            for _ in range(self.speed):
                self.world.update()
                
                # 记录轨迹
                for agent in self.world.agents.values():
                    if agent.id not in self.trails:
                        self.trails[agent.id] = []
                    self.trails[agent.id].append((agent.x, agent.y))
                    # 限制轨迹长度
                    if len(self.trails[agent.id]) > 100:
                        self.trails[agent.id].pop(0)
                        
            # 记录统计
            if self.world.tick % 60 == 0:
                self.stats_history.append({
                    'tick': self.world.tick,
                    'alive': len([a for a in self.world.agents.values() if a.alive]),
                    'discoveries': len(self.world.discoveries),
                })
                if len(self.stats_history) > 100:
                    self.stats_history.pop(0)
                    
        self.camera.update()
        
    def render(self):
        """渲染画面"""
        self.screen.fill(COLORS['bg'])
        
        # 绘制网格
        self._draw_grid()
        
        # 绘制轨迹
        if self.show_trails:
            self._draw_trails()
        
        # 绘制物体
        self._draw_objects()
        
        # 绘制AI
        self._draw_agents()
        
        # 绘制UI
        self._draw_ui()
        
        pygame.display.flip()
        
    def _draw_grid(self):
        """绘制网格"""
        grid_size = 20 * self.camera.zoom
        offset_x = -self.camera.x % grid_size
        offset_y = -self.camera.y % grid_size
        
        for x in range(int(offset_x), SCREEN_WIDTH, int(grid_size)):
            pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, SCREEN_HEIGHT))
        for y in range(int(offset_y), SCREEN_HEIGHT, int(grid_size)):
            pygame.draw.line(self.screen, COLORS['grid'], (0, y), (SCREEN_WIDTH, y))
            
    def _draw_trails(self):
        """绘制AI轨迹"""
        for agent_id, trail in self.trails.items():
            if len(trail) < 2:
                continue
                
            agent = self.world.agents.get(agent_id)
            if not agent or not agent.alive:
                continue
                
            points = []
            for x, y in trail:
                sx, sy = self.camera.world_to_screen(x, y)
                points.append((sx, sy))
                
            if len(points) > 1:
                pygame.draw.lines(self.screen, (100, 100, 100, 50), False, points, 1)
                
    def _draw_objects(self):
        """绘制世界物体"""
        for obj in self.world.objects.values():
            x, y = self.camera.world_to_screen(obj.x, obj.y)
            
            # 检查是否在屏幕内
            if -20 < x < SCREEN_WIDTH + 20 and -20 < y < SCREEN_HEIGHT + 20:
                color = COLORS['object'].get(obj.type, (150, 150, 150))
                size = int(8 * self.camera.zoom)
                
                pygame.draw.circle(self.screen, color, (x, y), size)
                
                # 绘制数量
                if 'amount' in obj.properties:
                    text = self.font_small.render(str(obj.properties['amount']), True, (255, 255, 255))
                    self.screen.blit(text, (x - 5, y - 15))
                    
    def _draw_agents(self):
        """绘制AI"""
        for agent in self.world.agents.values():
            x, y = self.camera.world_to_screen(agent.x, agent.y)
            
            if -30 < x < SCREEN_WIDTH + 30 and -30 < y < SCREEN_HEIGHT + 30:
                # 选择颜色
                if not agent.alive:
                    color = COLORS['agent']['dead']
                else:
                    color = COLORS['agent'].get(agent.current_action, COLORS['agent']['idle'])
                    
                size = int(10 * self.camera.zoom)
                
                # 绘制AI圆圈
                pygame.draw.circle(self.screen, color, (x, y), size)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), size, 2)
                
                # 绘制能量条
                if agent.alive:
                    bar_width = size * 2
                    bar_height = 4
                    energy_pct = agent.energy / PHYSICS['energy']['max']
                    
                    pygame.draw.rect(self.screen, (50, 50, 50), 
                                   (x - bar_width//2, y - size - 10, bar_width, bar_height))
                    pygame.draw.rect(self.screen, 
                                   (255, 0, 0) if energy_pct < 0.3 else (0, 255, 0),
                                   (x - bar_width//2, y - size - 10, int(bar_width * energy_pct), bar_height))
                
                # 绘制ID
                if self.camera.zoom > 0.8:
                    text = self.font_small.render(agent.id[:8], True, (255, 255, 255))
                    self.screen.blit(text, (x - 20, y + size + 5))
                    
                # 选中高亮
                if agent == self.selected_agent:
                    pygame.draw.circle(self.screen, (255, 215, 0), (x, y), size + 5, 2)
                    
    def _draw_ui(self):
        """绘制UI界面"""
        # 顶部信息栏
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (0, 0, SCREEN_WIDTH, 40))
        
        info_text = f"Tick: {self.world.tick} | 存活: {len([a for a in self.world.agents.values() if a.alive])} | 发现: {len(self.world.discoveries)} | 死亡: {len(self.world.deaths)} | 速度: {self.speed}x"
        if self.paused:
            info_text += " [暂停]"
            
        text = self.font_large.render(info_text, True, COLORS['ui_text'])
        self.screen.blit(text, (10, 10))
        
        # 右侧选中AI详情
        if self.selected_agent:
            self._draw_agent_panel()
        else:
            self._draw_world_panel()
            
        # 底部操作提示
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        hint = "WASD:移动相机 | 空格:暂停 | T:轨迹 | 1-4:速度 | F:跟随 | 滚轮:缩放 | 左键:选择"
        text = self.font.render(hint, True, (150, 150, 150))
        self.screen.blit(text, (10, SCREEN_HEIGHT - 25))
        
    def _draw_agent_panel(self):
        """绘制选中AI详情面板"""
        panel_x = SCREEN_WIDTH - 300
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (panel_x, 50, 290, 400))
        pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, 50, 290, 400), 2)
        
        agent = self.selected_agent
        y = 60
        
        # 标题
        title = self.font_large.render(f"AI: {agent.id[:12]}", True, COLORS['ui_highlight'])
        self.screen.blit(title, (panel_x + 10, y))
        y += 30
        
        # 状态
        status = "存活" if agent.alive else "死亡"
        text = self.font.render(f"状态: {status}", True, COLORS['ui_text'])
        self.screen.blit(text, (panel_x + 10, y))
        y += 25
        
        if agent.alive:
            # 能量
            text = self.font.render(f"能量: {agent.energy:.1f}/{PHYSICS['energy']['max']}", True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            # 位置
            text = self.font.render(f"位置: ({agent.x}, {agent.y})", True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            # 当前行为
            text = self.font.render(f"行为: {agent.current_action or 'idle'}", True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            # 发现的行为
            y += 10
            text = self.font.render("已发现行为:", True, COLORS['ui_highlight'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
            for behavior in list(agent.discovered_behaviors)[:5]:
                text = self.font_small.render(f"  • {behavior}", True, (200, 200, 200))
                self.screen.blit(text, (panel_x + 10, y))
                y += 20
                
    def _draw_world_panel(self):
        """绘制世界统计面板"""
        panel_x = SCREEN_WIDTH - 300
        pygame.draw.rect(self.screen, COLORS['ui_bg'], (panel_x, 50, 290, 300))
        pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, 50, 290, 300), 2)
        
        y = 60
        title = self.font_large.render("世界统计", True, COLORS['ui_highlight'])
        self.screen.blit(title, (panel_x + 10, y))
        y += 35
        
        stats = [
            f"运行时间: {self.world.tick} ticks",
            f"存活AI: {len([a for a in self.world.agents.values() if a.alive])}",
            f"总死亡: {len(self.world.deaths)}",
            f"发现总数: {len(self.world.discoveries)}",
            f"资源点: {len(self.world.objects)}",
        ]
        
        for stat in stats:
            text = self.font.render(stat, True, COLORS['ui_text'])
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
            
        # 最近发现
        y += 10
        text = self.font.render("最近发现:", True, COLORS['ui_highlight'])
        self.screen.blit(text, (panel_x + 10, y))
        y += 25
        
        for discovery in self.world.discoveries[-5:]:
            text = self.font_small.render(f"{discovery['agent'][:8]}: {discovery['behavior'][:20]}", True, (200, 200, 200))
            self.screen.blit(text, (panel_x + 10, y))
            y += 20
            
    async def run(self):
        """主循环"""
        print("🎮 AnotherYou ECO 可视化启动")
        print("=" * 40)
        print("控制:")
        print("  WASD - 移动相机")
        print("  空格 - 暂停/继续")
        print("  T - 显示/隐藏轨迹")
        print("  1-4 - 调整速度")
        print("  F - 跟随随机AI")
        print("  滚轮 - 缩放")
        print("  左键 - 选择AI")
        print("=" * 40)
        
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.render()
            self.clock.tick(FPS)
            
            # 让出控制权
            await asyncio.sleep(0)
            
        pygame.quit()


async def main():
    """启动可视化"""
    world = PureWorld()
    visualizer = Visualizer(world)
    await visualizer.run()


if __name__ == "__main__":
    asyncio.run(main())
