"""
HUD - 游戏界面HUD系统
清晰、专业、高对比度
"""

import pygame
from typing import Optional

class HUD:
    """游戏HUD"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 字体
        self.font_small = pygame.font.SysFont('microsoftyahei', 12)
        self.font = pygame.font.SysFont('microsoftyahei', 14)
        self.font_large = pygame.font.SysFont('microsoftyahei', 18, bold=True)
        self.font_title = pygame.font.SysFont('microsoftyahei', 24, bold=True)
        
        # 颜色
        self.colors = {
            'bg': (30, 30, 35, 230),
            'border': (100, 100, 120),
            'text': (255, 255, 255),
            'highlight': (255, 215, 0),
            'info': (150, 200, 255),
            'success': (100, 255, 100),
            'warning': (255, 200, 100),
            'danger': (255, 100, 100),
        }
        
    def render(self, screen: pygame.Surface, game_state: dict):
        """渲染HUD"""
        
        # 顶部栏
        self._render_top_bar(screen, game_state)
        
        # 底部工具栏
        self._render_bottom_bar(screen, game_state)
        
        # 玩家信息（左下）
        if game_state.get('player'):
            self._render_player_info(screen, game_state['player'])
            
        # 小地图（右上，上帝模式）
        if game_state.get('god_mode') and game_state.get('minimap'):
            self._render_minimap(screen, game_state['minimap'])
            
    def _render_top_bar(self, screen: pygame.Surface, game_state: dict):
        """渲染顶部栏"""
        bar_height = 50
        
        # 背景
        pygame.draw.rect(screen, (25, 25, 30), (0, 0, self.screen_width, bar_height))
        pygame.draw.line(screen, (80, 80, 100), (0, bar_height), (self.screen_width, bar_height), 2)
        
        # 左侧：游戏标题
        title = self.font_title.render("AnotherYou ECO", True, self.colors['highlight'])
        screen.blit(title, (20, 10))
        
        # 中间：时间和天气
        time_str = game_state.get('time', 'Year 1 Spring Day 1 12:00')
        weather = game_state.get('weather', '☀️ Sunny')
        
        time_text = self.font_large.render(time_str, True, self.colors['text'])
        screen.blit(time_text, (self.screen_width//2 - time_text.get_width()//2, 8))
        
        weather_text = self.font.render(weather, True, self.colors['info'])
        screen.blit(weather_text, (self.screen_width//2 - weather_text.get_width()//2, 28))
        
        # 右侧：模式指示
        mode = game_state.get('mode', 'PLAYER')
        mode_color = self.colors['danger'] if mode == 'GOD' else self.colors['info']
        mode_text = self.font_large.render(f"👁️ {mode} MODE", True, mode_color)
        screen.blit(mode_text, (self.screen_width - mode_text.get_width() - 20, 12))
        
    def _render_bottom_bar(self, screen: pygame.Surface, game_state: dict):
        """渲染底部工具栏"""
        bar_height = 50
        y = self.screen_height - bar_height
        
        # 背景
        pygame.draw.rect(screen, (25, 25, 30), (0, y, self.screen_width, bar_height))
        pygame.draw.line(screen, (80, 80, 100), (0, y), (self.screen_width, y), 2)
        
        # 控制提示
        controls = game_state.get('controls', 'WASD:移动 | F12:上帝模式')
        text = self.font.render(controls, True, (180, 180, 180))
        screen.blit(text, (20, y + 15))
        
        # 速度指示
        speed = game_state.get('speed', 1)
        paused = game_state.get('paused', False)
        
        if paused:
            speed_text = "⏸️ PAUSED"
            speed_color = self.colors['warning']
        else:
            speed_text = f"⚡ {speed}x"
            speed_color = self.colors['success']
            
        text = self.font_large.render(speed_text, True, speed_color)
        screen.blit(text, (self.screen_width - 150, y + 12))
        
    def _render_player_info(self, screen: pygame.Surface, player: dict):
        """渲染玩家信息面板"""
        panel_width = 220
        panel_height = 140
        x = 20
        y = self.screen_height - panel_height - 60
        
        # 背景
        pygame.draw.rect(screen, (30, 30, 35, 240), (x, y, panel_width, panel_height))
        pygame.draw.rect(screen, (100, 100, 120), (x, y, panel_width, panel_height), 2)
        
        # 标题
        name = player.get('name', 'Player')
        title = self.font_large.render(f"👤 {name}", True, self.colors['highlight'])
        screen.blit(title, (x + 10, y + 10))
        
        # 属性条
        line_y = y + 40
        
        # 能量
        energy = player.get('energy', 100)
        self._render_bar(screen, x + 10, line_y, 180, 12, 
                        energy / 100, "⚡ 能量", self.colors['success'])
        line_y += 25
        
        # 心情
        mood = player.get('mood', 50)
        self._render_bar(screen, x + 10, line_y, 180, 12, 
                        mood / 100, "😊 心情", self.colors['info'])
        line_y += 25
        
        # 金币
        money = player.get('money', 0)
        money_text = self.font.render(f"💰 {money} G", True, self.colors['highlight'])
        screen.blit(money_text, (x + 10, line_y))
        line_y += 22
        
        # 当前目标
        goal = player.get('goal', '探索中...')
        goal_text = self.font_small.render(f"🎯 {goal}", True, (200, 200, 200))
        screen.blit(goal_text, (x + 10, line_y))
        
    def _render_bar(self, screen: pygame.Surface, x: int, y: int, 
                   width: int, height: int, percent: float, 
                   label: str, color: tuple):
        """渲染进度条"""
        # 标签
        text = self.font.render(label, True, self.colors['text'])
        screen.blit(text, (x, y - 2))
        
        # 条背景
        bar_x = x + 60
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, y, width - 60, height))
        
        # 填充
        fill_width = int((width - 60) * max(0, min(1, percent)))
        pygame.draw.rect(screen, color, (bar_x, y, fill_width, height))
        
        # 数值
        value_text = self.font_small.render(f"{int(percent * 100)}", True, self.colors['text'])
        screen.blit(value_text, (bar_x + width - 55, y))
        
    def _render_minimap(self, screen: pygame.Surface, minimap: dict):
        """渲染小地图"""
        size = 150
        x = self.screen_width - size - 20
        y = 60
        
        # 背景
        pygame.draw.rect(screen, (20, 20, 25), (x, y, size, size))
        pygame.draw.rect(screen, (100, 100, 120), (x, y, size, size), 2)
        
        # 标题
        title = self.font.render("🗺️ 地图", True, self.colors['text'])
        screen.blit(title, (x + 10, y + 5))
        
        # 简化的地图显示
        map_area = pygame.Rect(x + 5, y + 25, size - 10, size - 30)
        
        # 这里应该渲染实际的地图缩略图
        # 简化：只显示玩家位置
        if minimap.get('player_pos'):
            px, py = minimap['player_pos']
            dot_x = x + 5 + (px / minimap.get('world_width', 100)) * (size - 10)
            dot_y = y + 25 + (py / minimap.get('world_height', 100)) * (size - 30)
            pygame.draw.circle(screen, (255, 215, 0), (int(dot_x), int(dot_y)), 4)
