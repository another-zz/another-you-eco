"""
Professional HUD - 专业游戏HUD
高对比、大字体、清晰易读
"""

import pygame
from typing import Dict, Optional

class ProfessionalHUD:
    """专业游戏HUD"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 字体 - 更大更清晰
        self.font_small = pygame.font.SysFont('microsoftyahei', 12)
        self.font = pygame.font.SysFont('microsoftyahei', 14, bold=True)
        self.font_large = pygame.font.SysFont('microsoftyahei', 18, bold=True)
        self.font_title = pygame.font.SysFont('microsoftyahei', 22, bold=True)
        
        # 颜色 - 高对比
        self.colors = {
            'bg_dark': (20, 22, 25, 240),
            'bg_panel': (35, 38, 45, 230),
            'border': (100, 110, 130),
            'text': (255, 255, 255),
            'text_dim': (180, 190, 200),
            'highlight': (255, 215, 0),
            'energy': (100, 220, 100),
            'energy_low': (255, 100, 100),
            'mood_happy': (255, 200, 100),
            'mood_sad': (150, 180, 220),
            'info': (150, 200, 255),
        }
        
        # 图标
        self.icons = {
            'sun': '☀️',
            'rain': '🌧️',
            'snow': '❄️',
            'cloud': '☁️',
            'moon': '🌙',
            'energy': '⚡',
            'mood': '😊',
            'money': '💰',
            'target': '🎯',
        }
        
    def render(self, screen: pygame.Surface, game_state: Dict):
        """渲染完整HUD"""
        
        # 左上：玩家信息
        self._render_player_panel(screen, game_state.get('player', {}))
        
        # 右上：时间天气
        self._render_time_panel(screen, game_state)
        
        # 底部：工具栏
        self._render_toolbar(screen, game_state)
        
        # 小地图（上帝模式）
        if game_state.get('god_mode'):
            self._render_minimap(screen, game_state)
            
    def _render_player_panel(self, screen: pygame.Surface, player: Dict):
        """渲染玩家面板（左上）"""
        panel_w = 240
        panel_h = 160
        x, y = 15, 15
        
        # 背景
        self._draw_panel(screen, x, y, panel_w, panel_h)
        
        # 标题：玩家名
        name = player.get('name', 'Player')
        title = self.font_title.render(f"👤 {name}", True, self.colors['highlight'])
        screen.blit(title, (x + 12, y + 10))
        
        # 状态："另一个你"
        status = player.get('status', 'AI控制中')
        status_color = self.colors['energy'] if '玩家' in status else self.colors['text_dim']
        status_text = self.font.render(f"🎮 {status}", True, status_color)
        screen.blit(status_text, (x + 12, y + 38))
        
        line_y = y + 65
        
        # 金币
        money = player.get('money', 0)
        money_text = self.font_large.render(f"💰 {money}G", True, self.colors['highlight'])
        screen.blit(money_text, (x + 12, line_y))
        line_y += 28
        
        # 能量条
        energy = player.get('energy', 100)
        self._render_bar(screen, x + 12, line_y, 200, 14, 
                        energy / 100, f"{self.icons['energy']} 能量", 
                        self.colors['energy'] if energy > 30 else self.colors['energy_low'])
        line_y += 22
        
        # 心情
        mood = player.get('mood', 50)
        mood_icon = '😄' if mood > 70 else '🙂' if mood > 40 else '😔'
        mood_color = self.colors['mood_happy'] if mood > 50 else self.colors['mood_sad']
        self._render_bar(screen, x + 12, line_y, 200, 14, 
                        mood / 100, f"{mood_icon} 心情", mood_color)
                        
    def _render_time_panel(self, screen: pygame.Surface, game_state: Dict):
        """渲染时间面板（右上）"""
        panel_w = 280
        panel_h = 90
        x = self.screen_width - panel_w - 15
        y = 15
        
        # 背景
        self._draw_panel(screen, x, y, panel_w, panel_h)
        
        # 年份季节
        year = game_state.get('year', 1)
        season = game_state.get('season', 'Spring')
        season_icon = {'Spring': '🌸', 'Summer': '☀️', 'Autumn': '🍂', 'Winter': '❄️'}.get(season, '🌸')
        
        season_text = self.font_large.render(f"{season_icon} Year {year} {season}", 
                                            True, self.colors['text'])
        screen.blit(season_text, (x + 12, y + 10))
        
        # 日期时间
        day = game_state.get('day', 1)
        hour = game_state.get('hour', 12)
        minute = game_state.get('minute', 0)
        time_str = f"Day {day}  {hour:02d}:{minute:02d}"
        
        time_text = self.font.render(time_str, True, self.colors['text_dim'])
        screen.blit(time_text, (x + 12, y + 35))
        
        # 天气
        weather = game_state.get('weather', 'Sunny')
        weather_icon = self.icons.get(weather.lower(), '☀️')
        weather_text = self.font.render(f"{weather_icon} {weather}", True, self.colors['info'])
        screen.blit(weather_text, (x + 12, y + 58))
        
    def _render_toolbar(self, screen: pygame.Surface, game_state: Dict):
        """渲染底部工具栏"""
        bar_h = 60
        y = self.screen_height - bar_h - 10
        
        # 背景条
        pygame.draw.rect(screen, (25, 27, 30, 240), 
                        (10, y, self.screen_width - 20, bar_h))
        pygame.draw.rect(screen, self.colors['border'], 
                        (10, y, self.screen_width - 20, bar_h), 2)
        
        # 当前目标
        goal = game_state.get('goal', '探索世界')
        goal_text = self.font_large.render(f"{self.icons['target']} 目标: {goal}", 
                                          True, self.colors['highlight'])
        screen.blit(goal_text, (25, y + 18))
        
        # 右侧：控制提示
        controls = game_state.get('controls', 'WASD:移动 | F12:上帝模式')
        ctrl_text = self.font.render(controls, True, self.colors['text_dim'])
        screen.blit(ctrl_text, (self.screen_width - ctrl_text.get_width() - 25, y + 20))
        
        # 速度指示
        speed = game_state.get('speed', 1)
        paused = game_state.get('paused', False)
        
        if paused:
            speed_text = "⏸️ 暂停"
            speed_color = (255, 200, 100)
        else:
            speed_text = f"⚡ {speed}x"
            speed_color = (100, 255, 150)
            
        speed_render = self.font_large.render(speed_text, True, speed_color)
        screen.blit(speed_render, (self.screen_width // 2 - 30, y + 16))
        
    def _render_minimap(self, screen: pygame.Surface, game_state: Dict):
        """渲染小地图"""
        size = 140
        x = self.screen_width - size - 20
        y = 120
        
        # 背景
        pygame.draw.rect(screen, (20, 22, 25, 240), (x, y, size, size))
        pygame.draw.rect(screen, self.colors['border'], (x, y, size, size), 2)
        
        # 标题
        title = self.font.render("🗺️ 地图", True, self.colors['text'])
        screen.blit(title, (x + 10, y + 5))
        
        # 简化的地图区域
        map_rect = pygame.Rect(x + 8, y + 28, size - 16, size - 36)
        pygame.draw.rect(screen, (40, 45, 50), map_rect)
        
        # 玩家位置点
        if game_state.get('player_pos'):
            px, py = game_state['player_pos']
            world_w = game_state.get('world_width', 100)
            world_h = game_state.get('world_height', 100)
            
            dot_x = map_rect.x + (px / world_w) * map_rect.width
            dot_y = map_rect.y + (py / world_h) * map_rect.height
            
            pygame.draw.circle(screen, (255, 215, 0), (int(dot_x), int(dot_y)), 4)
            
    def _draw_panel(self, screen: pygame.Surface, x: int, y: int, w: int, h: int):
        """绘制面板背景"""
        # 主背景
        pygame.draw.rect(screen, (30, 33, 38), (x, y, w, h))
        # 边框
        pygame.draw.rect(screen, self.colors['border'], (x, y, w, h), 2)
        # 顶部高光
        pygame.draw.line(screen, (60, 65, 75), (x + 2, y + 1), (x + w - 3, y + 1), 1)
        
    def _render_bar(self, screen: pygame.Surface, x: int, y: int, 
                   width: int, height: int, percent: float, 
                   label: str, color: tuple):
        """渲染进度条"""
        # 标签
        text = self.font.render(label, True, self.colors['text'])
        screen.blit(text, (x, y - 2))
        
        # 条背景
        bar_x = x + 70
        bar_rect = pygame.Rect(bar_x, y, width - 70, height)
        pygame.draw.rect(screen, (50, 55, 60), bar_rect)
        pygame.draw.rect(screen, (80, 85, 90), bar_rect, 1)
        
        # 填充
        fill_width = int((width - 70) * max(0, min(1, percent)))
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, y, fill_width, height)
            pygame.draw.rect(screen, color, fill_rect)
            # 高光
            pygame.draw.line(screen, 
                           (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)),
                           (bar_x, y), (bar_x + fill_width, y), 1)
