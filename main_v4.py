"""
Main Visualizer v0.4 - 活的世界可视化
整合所有新系统
"""

import pygame
import asyncio
import random
import math
from typing import Dict, List, Tuple, Optional

# 导入核心系统
import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.living_world import (
    LivingWorld, LivingAgent, 
    GameTime, Season, Weather, WeatherSystem,
    TerrainType, AdminMode, Camera
)
from ui.admin_panel import AdminPanel
from effects.particles import WeatherParticles, SeasonEffects

# 配置
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000
FPS = 60

# 颜色
COLORS = {
    'bg': (20, 25, 20),
    'terrain': {
        TerrainType.PLAINS: (100, 150, 80),
        TerrainType.FOREST: (34, 100, 34),
        TerrainType.MOUNTAIN: (120, 120, 120),
        TerrainType.RIVER: (65, 105, 225),
        TerrainType.LAKE: (50, 90, 200),
        TerrainType.DESERT: (210, 180, 140),
    },
    'agent': {
        'idle': (100, 200, 100),
        'working': (255, 200, 100),
        'sleeping': (100, 100, 200),
        'social': (255, 150, 200),
        'dead': (80, 80, 80),
    },
    'ui': {
        'bg': (30, 30, 35),
        'text': (255, 255, 255),
        'highlight': (255, 215, 0),
        'admin': (255, 100, 100),
    }
}


class LivingWorldVisualizer:
    """活的世界可视化器 v0.4"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.4 - 活的世界")
        self.clock = pygame.time.Clock()
        
        # 字体
        self.font = pygame.font.SysFont('microsoftyahei', 14)
        self.font_bold = pygame.font.SysFont('microsoftyahei', 14, bold=True)
        self.font_large = pygame.font.SysFont('microsoftyahei', 18, bold=True)
        self.font_title = pygame.font.SysFont('microsoftyahei', 24, bold=True)
        
        # 世界
        self.world = LivingWorld(width=200, height=200)
        
        # 创建初始AI
        for i in range(20):
            agent = LivingAgent(
                id=f"agent_{i}",
                name=f"AI-{i}",
                x=random.randint(80, 120),
                y=random.randint(80, 120)
            )
            self.world.agents[agent.id] = agent
            
        # 相机系统
        self.camera = Camera()
        self.camera.x = 100 * 20  # 初始位置在世界中心
        self.camera.y = 100 * 20
        
        # 管理员面板
        self.admin_panel = AdminPanel(self.world, self.camera)
        
        # 粒子系统
        self.particles = WeatherParticles(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 状态
        self.paused = False
        self.speed = 1
        self.show_terrain = True
        self.show_agents = True
        self.show_debug = False
        
        # 玩家控制的AI（普通模式）
        self.player_agent = random.choice(list(self.world.agents.values()))
        
    def handle_input(self):
        """处理输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                # 管理员模式切换
                if event.key == pygame.K_F12:
                    if self.camera.mode == AdminMode.NORMAL:
                        self.camera.set_mode(AdminMode.GOD)
                        self.admin_panel.add_log("进入上帝视角模式")
                    else:
                        self.camera.set_mode(AdminMode.NORMAL)
                        self.admin_panel.add_log("返回普通模式")
                        
                # 管理员面板
                elif event.key == pygame.K_TAB:
                    if self.camera.mode == AdminMode.GOD:
                        self.admin_panel.toggle()
                        
                # 基础控制
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                    
                # 显示切换
                elif event.key == pygame.K_t:
                    self.show_terrain = not self.show_terrain
                elif event.key == pygame.K_a:
                    self.show_agents = not self.show_agents
                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug
                    
            # 鼠标滚轮缩放
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 上滚
                    self.camera.zoom_in()
                elif event.button == 5:  # 下滚
                    self.camera.zoom_out()
                elif event.button == 1:  # 左键
                    # 管理员模式下点击选择AI
                    if self.camera.mode == AdminMode.GOD:
                        mx, my = pygame.mouse.get_pos()
                        self.admin_panel.handle_click(mx, my, SCREEN_WIDTH, SCREEN_HEIGHT)
                        
        # 相机移动（WASD）
        keys = pygame.key.get_pressed()
        speed = 10 * (3 if self.camera.mode == AdminMode.GOD else 1)
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.camera.move(0, -speed)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.camera.move(0, speed)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.camera.move(-speed, 0)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.camera.move(speed, 0)
            
        # 普通模式下相机跟随玩家
        if self.camera.mode == AdminMode.NORMAL and self.player_agent:
            target_x = self.player_agent.x * 20
            target_y = self.player_agent.y * 20
            self.camera.x += (target_x - self.camera.x) * 0.05
            self.camera.y += (target_y - self.camera.y) * 0.05
            
        return True
        
    async def update(self):
        """更新世界"""
        if not self.paused:
            for _ in range(self.speed):
                self.world.update()
                
                # AI决策（简化版）
                for agent in self.world.agents.values():
                    if agent.alive:
                        decision = agent.decide_action(self.world)
                        # 这里应该执行决策...
                        
        # 更新粒子系统
        self.particles.set_camera(self.camera.x, self.camera.y)
        self.particles.update(self.world.weather.current, self.world.weather.intensity)
        
    def render(self):
        """渲染"""
        self.screen.fill(COLORS['bg'])
        
        # 绘制地形
        if self.show_terrain:
            self._render_terrain()
            
        # 绘制AI
        if self.show_agents:
            self._render_agents()
            
        # 绘制粒子效果
        self.particles.render(self.screen)
        
        # 季节叠加效果
        SeasonEffects.render_overlay(self.screen, self.world.time.season, self.world.time.hour)
        
        # UI
        self._render_ui()
        
        # 管理员面板
        self.admin_panel.render(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        pygame.display.flip()
        
    def _render_terrain(self):
        """渲染地形"""
        cell_size = 20 * self.camera.zoom
        
        # 计算可见范围
        start_x = max(0, int((self.camera.x - SCREEN_WIDTH//2) / cell_size) - 1)
        end_x = min(self.world.width, int((self.camera.x + SCREEN_WIDTH//2) / cell_size) + 1)
        start_y = max(0, int((self.camera.y - SCREEN_HEIGHT//2) / cell_size) - 1)
        end_y = min(self.world.height, int((self.camera.y + SCREEN_HEIGHT//2) / cell_size) + 1)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                # 检查是否可见（普通模式限制）
                if self.camera.mode == AdminMode.NORMAL and self.player_agent:
                    if not self.camera.can_see(x, y, self.player_agent.x, self.player_agent.y):
                        continue
                        
                cell = self.world.terrain.get((x, y))
                if cell:
                    sx, sy = self.camera.world_to_screen(x, y, SCREEN_WIDTH, SCREEN_HEIGHT)
                    
                    # 检查是否在屏幕内
                    if -cell_size < sx < SCREEN_WIDTH + cell_size and -cell_size < sy < SCREEN_HEIGHT + cell_size:
                        color = COLORS['terrain'].get(cell.terrain, (100, 100, 100))
                        
                        # 绘制地形块
                        rect = pygame.Rect(sx, sy, cell_size + 1, cell_size + 1)
                        pygame.draw.rect(self.screen, color, rect)
                        
                        # 调试：显示坐标
                        if self.show_debug and self.camera.zoom > 0.8:
                            text = self.font.render(f"{x},{y}", True, (50, 50, 50))
                            self.screen.blit(text, (sx + 2, sy + 2))
                            
    def _render_agents(self):
        """渲染AI"""
        for agent in self.world.agents.values():
            # 检查是否可见
            if self.camera.mode == AdminMode.NORMAL and self.player_agent:
                if not self.camera.can_see(agent.x, agent.y, self.player_agent.x, self.player_agent.y):
                    continue
                    
            sx, sy = self.camera.world_to_screen(agent.x, agent.y, SCREEN_WIDTH, SCREEN_HEIGHT)
            
            # 检查是否在屏幕内
            if -50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50:
                size = max(4, int(10 * self.camera.zoom))
                
                # 颜色
                if not agent.alive:
                    color = COLORS['agent']['dead']
                else:
                    color = COLORS['agent'].get(agent.current_action, COLORS['agent']['idle'])
                    
                # 玩家高亮
                if agent == self.player_agent:
                    pygame.draw.circle(self.screen, (255, 215, 0), (sx, sy), size + 4, 2)
                    
                # 绘制AI
                pygame.draw.circle(self.screen, color, (sx, sy), size)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), size, 1)
                
                # 名字（上帝模式或靠近玩家）
                if self.camera.mode == AdminMode.GOD or self.camera.zoom > 1.0:
                    name_text = self.font.render(agent.name, True, (255, 255, 255))
                    self.screen.blit(name_text, (sx - 15, sy - size - 15))
                    
                # 状态图标
                if agent.current_action == 'sleeping':
                    z_text = self.font.render("Zzz", True, (200, 200, 255))
                    self.screen.blit(z_text, (sx + size, sy - size))
                    
    def _render_ui(self):
        """渲染UI"""
        # 顶部信息栏
        bar_height = 50
        pygame.draw.rect(self.screen, COLORS['ui']['bg'], (0, 0, SCREEN_WIDTH, bar_height))
        
        # 模式指示
        mode_color = COLORS['ui']['admin'] if self.camera.mode == AdminMode.GOD else COLORS['ui']['text']
        mode_text = "👁️ GOD MODE" if self.camera.mode == AdminMode.GOD else "👤 PLAYER MODE"
        text = self.font_title.render(mode_text, True, mode_color)
        self.screen.blit(text, (20, 10))
        
        # 时间天气
        time_text = f"{self.world.time} | {self.world.weather}"
        text = self.font_large.render(time_text, True, COLORS['ui']['text'])
        self.screen.blit(text, (300, 15))
        
        # 统计
        alive = len([a for a in self.world.agents.values() if a.alive])
        stats = f"AI: {alive} | Speed: {self.speed}x"
        if self.paused:
            stats += " [PAUSED]"
        text = self.font_large.render(stats, True, COLORS['ui']['highlight'])
        self.screen.blit(text, (SCREEN_WIDTH - 300, 15))
        
        # 底部控制提示
        hint_y = SCREEN_HEIGHT - 30
        pygame.draw.rect(self.screen, COLORS['ui']['bg'], (0, hint_y, SCREEN_WIDTH, 30))
        
        hints = []
        if self.camera.mode == AdminMode.GOD:
            hints = ["F12:退出上帝模式", "TAB:面板", "WASD:移动", "滚轮:缩放", "点击:选择AI"]
        else:
            hints = ["F12:上帝模式", "WASD:移动", "滚轮:缩放(有限)"]
            
        hint_text = " | ".join(hints)
        text = self.font.render(hint_text, True, (150, 150, 150))
        self.screen.blit(text, (20, hint_y + 5))
        
    async def run(self):
        """主循环"""
        print("🌍 AnotherYou ECO v0.4 - 活的世界")
        print("=" * 50)
        print("✨ 新特性:")
        print("  • 时间系统（日夜+四季）")
        print("  • 天气系统（雨/雪/风暴）")
        print("  • AI记忆与反思")
        print("  • 随机事件")
        print("  • 管理员上帝视角")
        print("=" * 50)
        print("控制:")
        print("  F12 - 切换上帝模式")
        print("  TAB - 管理员面板（上帝模式）")
        print("  WASD - 移动")
        print("  空格 - 暂停")
        print("  1/2/3 - 速度")
        print("=" * 50)
        
        running = True
        while running:
            running = self.handle_input()
            await self.update()
            self.render()
            self.clock.tick(FPS)
            await asyncio.sleep(0)
            
        pygame.quit()


async def main():
    visualizer = LivingWorldVisualizer()
    await visualizer.run()


if __name__ == "__main__":
    asyncio.run(main())
