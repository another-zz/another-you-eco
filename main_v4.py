"""
Main Visualizer v0.4.1 - 修复版
更清晰的可视化，更好的相机控制
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

# 颜色 - 更鲜明的配色
COLORS = {
    'bg': (15, 20, 15),
    'terrain': {
        TerrainType.PLAINS: (120, 160, 80),      # 平原 - 亮绿
        TerrainType.FOREST: (34, 85, 51),        # 森林 - 深绿
        TerrainType.MOUNTAIN: (100, 100, 110),   # 山地 - 灰
        TerrainType.RIVER: (65, 120, 220),       # 河流 - 蓝
        TerrainType.LAKE: (50, 100, 200),        # 湖泊 - 深蓝
        TerrainType.DESERT: (200, 180, 120),     # 沙漠 - 黄
    },
    'agent': {
        'idle': (80, 200, 80),
        'working': (255, 180, 60),
        'sleeping': (100, 100, 200),
        'social': (255, 120, 180),
        'dead': (80, 80, 80),
    },
    'ui': {
        'bg': (25, 25, 30),
        'text': (255, 255, 255),
        'highlight': (255, 215, 0),
        'admin': (255, 100, 100),
        'info': (150, 200, 255),
    }
}


class LivingWorldVisualizer:
    """活的世界可视化器 v0.4.1"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.4.1 - 活的世界")
        self.clock = pygame.time.Clock()
        
        # 字体
        self.font = pygame.font.SysFont('microsoftyahei', 14)
        self.font_bold = pygame.font.SysFont('microsoftyahei', 14, bold=True)
        self.font_large = pygame.font.SysFont('microsoftyahei', 18, bold=True)
        self.font_title = pygame.font.SysFont('microsoftyahei', 24, bold=True)
        
        # 世界
        self.world = LivingWorld(width=100, height=100)  # 减小世界尺寸
        
        # 创建初始AI
        for i in range(15):
            agent = LivingAgent(
                id=f"agent_{i}",
                name=f"AI-{i}",
                x=random.randint(40, 60),
                y=random.randint(40, 60)
            )
            self.world.agents[agent.id] = agent
            
        # 相机系统 - 初始位置在世界中心
        self.camera = Camera()
        self.camera.x = 50 * 20  # 世界中心
        self.camera.y = 50 * 20
        self.camera.zoom = 1.0
        
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
        
        # 玩家控制的AI
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
                        # 普通模式时相机跟随玩家
                        if self.player_agent:
                            self.camera.x = self.player_agent.x * 20
                            self.camera.y = self.player_agent.y * 20
                        
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
                    
                # 显示切换 - 使用不同按键避免冲突
                elif event.key == pygame.K_t:
                    self.show_terrain = not self.show_terrain
                elif event.key == pygame.K_y:
                    self.show_agents = not self.show_agents
                elif event.key == pygame.K_u:
                    self.show_debug = not self.show_debug
                    
            # 鼠标滚轮缩放
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 上滚
                    self.camera.zoom_in()
                elif event.button == 5:  # 下滚
                    self.camera.zoom_out()
                elif event.button == 1:  # 左键
                    if self.camera.mode == AdminMode.GOD:
                        mx, my = pygame.mouse.get_pos()
                        self.admin_panel.handle_click(mx, my, SCREEN_WIDTH, SCREEN_HEIGHT)
                        
        # 相机移动（WASD）- 只在上帝模式或按住Shift时
        keys = pygame.key.get_pressed()
        move_speed = 15
        
        # 上帝模式下自由移动
        if self.camera.mode == AdminMode.GOD:
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.camera.y -= move_speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.camera.y += move_speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera.x -= move_speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera.x += move_speed
        else:
            # 普通模式 - 切换控制的AI
            if keys[pygame.K_w]:
                self.player_agent.y = max(0, self.player_agent.y - 1)
            if keys[pygame.K_s]:
                self.player_agent.y = min(99, self.player_agent.y + 1)
            if keys[pygame.K_a]:
                self.player_agent.x = max(0, self.player_agent.x - 1)
            if keys[pygame.K_d]:
                self.player_agent.x = min(99, self.player_agent.x + 1)
                
            # 相机跟随玩家
            target_x = self.player_agent.x * 20
            target_y = self.player_agent.y * 20
            self.camera.x += (target_x - self.camera.x) * 0.1
            self.camera.y += (target_y - self.camera.y) * 0.1
            
        return True
        
    async def update(self):
        """更新世界"""
        if not self.paused:
            for _ in range(self.speed):
                self.world.update()
                
                # AI决策
                for agent in self.world.agents.values():
                    if agent.alive:
                        decision = agent.decide_action(self.world)
                        if decision.get('action') == 'move':
                            direction = decision.get('direction', 'N')
                            dx = {'N': 0, 'S': 0, 'E': 1, 'W': -1}.get(direction, 0)
                            dy = {'N': -1, 'S': 1, 'E': 0, 'W': 0}.get(direction, 0)
                            agent.x = max(0, min(99, agent.x + dx))
                            agent.y = max(0, min(99, agent.y + dy))
                            agent.current_action = 'moving'
                        else:
                            agent.current_action = decision.get('action', 'idle')
                            
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
        """渲染地形 - 优化版"""
        cell_size = 20 * self.camera.zoom
        
        # 计算可见范围
        start_x = max(0, int((self.camera.x - SCREEN_WIDTH//2) / cell_size) - 1)
        end_x = min(self.world.width, int((self.camera.x + SCREEN_WIDTH//2) / cell_size) + 2)
        start_y = max(0, int((self.camera.y - SCREEN_HEIGHT//2) / cell_size) - 1)
        end_y = min(self.world.height, int((self.camera.y + SCREEN_HEIGHT//2) / cell_size) + 2)
        
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
                        
                        # 只在调试模式且放大时显示坐标
                        if self.show_debug and self.camera.zoom > 1.5:
                            text = self.font.render(f"{x},{y}", True, (30, 30, 30))
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
                size = max(6, int(12 * self.camera.zoom))
                
                # 颜色
                if not agent.alive:
                    color = COLORS['agent']['dead']
                else:
                    color = COLORS['agent'].get(agent.current_action, COLORS['agent']['idle'])
                    
                # 玩家高亮
                if agent == self.player_agent:
                    pygame.draw.circle(self.screen, (255, 215, 0), (sx, sy), size + 5, 3)
                    
                # 绘制AI
                pygame.draw.circle(self.screen, color, (sx, sy), size)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), size, 2)
                
                # 名字
                if self.camera.zoom > 0.7 or agent == self.player_agent:
                    name_text = self.font.render(agent.name, True, (255, 255, 255))
                    self.screen.blit(name_text, (sx - 15, sy - size - 18))
                    
                # 能量条
                if agent.alive and self.camera.zoom > 0.8:
                    bar_width = 30
                    bar_height = 4
                    energy_pct = agent.energy / 100
                    
                    bar_x = sx - bar_width // 2
                    bar_y = sy + size + 5
                    
                    pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                    energy_color = (0, 255, 0) if energy_pct > 0.5 else (255, 200, 0) if energy_pct > 0.3 else (255, 0, 0)
                    pygame.draw.rect(self.screen, energy_color, (bar_x, bar_y, int(bar_width * energy_pct), bar_height))
                    
    def _render_ui(self):
        """渲染UI"""
        # 顶部信息栏
        bar_height = 60
        pygame.draw.rect(self.screen, COLORS['ui']['bg'], (0, 0, SCREEN_WIDTH, bar_height))
        
        # 模式指示
        mode_color = COLORS['ui']['admin'] if self.camera.mode == AdminMode.GOD else COLORS['ui']['info']
        mode_text = "👁️ GOD MODE" if self.camera.mode == AdminMode.GOD else "👤 PLAYER MODE"
        text = self.font_title.render(mode_text, True, mode_color)
        self.screen.blit(text, (20, 15))
        
        # 时间天气 - 更醒目
        time_str = f"{self.world.time}"
        weather_str = f"{self.world.weather}"
        
        time_text = self.font_large.render(time_str, True, COLORS['ui']['text'])
        self.screen.blit(time_text, (300, 10))
        
        weather_text = self.font_large.render(weather_str, True, (200, 220, 255))
        self.screen.blit(weather_text, (300, 32))
        
        # 统计
        alive_count = len([a for a in self.world.agents.values() if a.alive])
        stats_text = f"AI: {alive_count} | Speed: {self.speed}x"
        if self.paused:
            stats_text += " [PAUSED]"
        text = self.font_large.render(stats_text, True, COLORS['ui']['highlight'])
        self.screen.blit(text, (SCREEN_WIDTH - 250, 18))
        
        # 底部控制提示
        hint_y = SCREEN_HEIGHT - 40
        pygame.draw.rect(self.screen, COLORS['ui']['bg'], (0, hint_y, SCREEN_WIDTH, 40))
        
        if self.camera.mode == AdminMode.GOD:
            hints = "F12:退出上帝 | TAB:面板 | WASD:移动相机 | 滚轮:缩放 | 点击:选择AI | T/Y/U:显示切换"
        else:
            hints = "F12:上帝模式 | WASD:移动你的AI | 滚轮:缩放 | T/Y/U:显示切换"
            
        text = self.font.render(hints, True, (180, 180, 180))
        self.screen.blit(text, (20, hint_y + 10))
        
        # 活跃事件提示
        if self.world.events.active_events:
            event = self.world.events.active_events[0]
            event_text = f"🌟 事件: {event.name}"
            text = self.font_bold.render(event_text, True, (255, 200, 100))
            self.screen.blit(text, (SCREEN_WIDTH - 400, hint_y + 10))
        
    async def run(self):
        """主循环"""
        print("🌍 AnotherYou ECO v0.4.1 - 活的世界")
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
        print("  WASD - 移动相机（上帝）/移动AI（玩家）")
        print("  滚轮 - 缩放地图")
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
