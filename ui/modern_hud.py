"""
Modern HUD - 现代游戏HUD
圆角面板 + 图标 + 颜色编码 + 动画
"""

import pygame
import math
from typing import Dict

class ModernHUD:
    """现代风格HUD"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 字体
        self.font_small = pygame.font.SysFont('microsoftyahei', 11)
        self.font = pygame.font.SysFont('microsoftyahei', 13, bold=True)
        self.font_large = pygame.font.SysFont('microsoftyahei', 16, bold=True)
        self.font_title = pygame.font.SysFont('microsoftyahei', 20, bold=True)
        
        # 颜色主题
        self.theme = {
            'panel_bg': (25, 28, 35, 230),
            'panel_border': (80, 90, 110),
            'panel_highlight': (100, 180, 255),
            'text': (255, 255, 255),
            'text_dim': (160, 170, 180),
            'accent_gold': (255, 215, 0),
            'accent_cyan': (100, 200, 255),
            'energy_high': (100, 255, 100),
            'energy_mid': (255, 220, 80),
            'energy_low': (255, 80, 80),
        }
        
        # 动画状态
        self.animation_time = 0
        self.pulse = 0
        
    def update(self, dt: float):
        """更新动画"""
        self.animation_time += dt
        self.pulse = (math.sin(self.animation_time * 3) + 1) / 2
        
    def render(self, screen: pygame.Surface, game_state: Dict):
        """渲染HUD"""
        self._render_player_panel(screen, game_state.get('player', {}))
        self._render_time_panel(screen, game_state)
        self._render_toolbar(screen, game_state)
        
        if game_state.get('god_mode'):
            self._render_minimap(screen, game_state)
            
    def _draw_rounded_panel(self, screen, x, y, w, h, radius=12, border=True, glow=False):
        """绘制圆角面板"""
        # 阴影
        shadow_rect = pygame.Rect(x + 3, y + 3, w, h)
        self._draw_rounded_rect(screen, shadow_rect, radius, (0, 0, 0, 60))
        
        # 主体
        panel_rect = pygame.Rect(x, y, w, h)
        self._draw_rounded_rect(screen, panel_rect, radius, self.theme['panel_bg'])
        
        if border:
            pygame.draw.rect(screen, self.theme['panel_border'], panel_rect, 2, border_radius=radius)
            
        # 顶部高光
        highlight_rect = pygame.Rect(x + 4, y + 2, w - 8, 2)
        pygame.draw.rect(screen, (80, 90, 100, 150), highlight_rect, border_radius=1)
        
        if glow:
            glow_color = (*self.theme['panel_highlight'][:3], int(30 * self.pulse))
            glow_rect = pygame.Rect(x - 2, y - 2, w + 4, h + 4)
            self._draw_rounded_rect(screen, glow_rect, radius + 2, glow_color)
            
    def _draw_rounded_rect(self, screen, rect, radius, color):
        """绘制圆角矩形"""
        if len(color) == 4 and color[3] < 255:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, color, (0, 0, rect.width, rect.height), border_radius=radius)
            screen.blit(s, rect.topleft)
        else:
            pygame.draw.rect(screen, color, rect, border_radius=radius)
            
    def _render_player_panel(self, screen, player):
        """渲染玩家面板"""
        panel_w, panel_h = 260, 180
        x, y = 15, 15
        
        is_player = '玩家' in player.get('status', '')
        self._draw_rounded_panel(screen, x, y, panel_w, panel_h, glow=is_player)
        
        # 头像
        avatar_rect = pygame.Rect(x + 12, y + 12, 40, 40)
        pygame.draw.circle(screen, (60, 70, 90), avatar_rect.center, 20)
        pygame.draw.circle(screen, self.theme['panel_highlight'], avatar_rect.center, 20, 2)
        
        # 名字
        name = player.get('name', 'Player')
        name_text = self.font_title.render(f"👤 {name}", True, self.theme['text'])
        screen.blit(name_text, (x + 60, y + 12))
        
        # 状态
        status = player.get('status', '🤖 AI自主')
        status_color = self.theme['energy_high'] if '玩家' in status else self.theme['text_dim']
        status_text = self.font.render(status, True, status_color)
        screen.blit(status_text, (x + 60, y + 38))
        
        line_y = y + 65
        
        # 金币
        money = player.get('money', 0)
        money_icon = self.font_large.render("💰", True, self.theme['accent_gold'])
        screen.blit(money_icon, (x + 12, line_y))
        money_text = self.font_large.render(f"{money}", True, self.theme['accent_gold'])
        screen.blit(money_text, (x + 40, line_y))
        line_y += 32
        
        # 能量条
        energy = player.get('energy', 100)
        self._render_modern_bar(screen, x + 12, line_y, 230, 16, 
                               energy / 100, "⚡", 
                               self._get_energy_color(energy))
        line_y += 26
        
        # 心情条
        mood = player.get('mood', 50)
        mood_icon = '😄' if mood > 70 else '🙂' if mood > 40 else '😔'
        mood_color = self.theme['energy_high'] if mood > 50 else (150, 180, 220)
        self._render_modern_bar(screen, x + 12, line_y, 230, 16, 
                               mood / 100, mood_icon, mood_color)
        line_y += 26
        
        # 目标
        goal = player.get('goal', '探索中...')
        goal_text = self.font_small.render(f"🎯 {goal}", True, self.theme['text_dim'])
        screen.blit(goal_text, (x + 12, line_y))
        
    def _render_time_panel(self, screen, game_state):
        """渲染时间面板"""
        panel_w, panel_h = 280, 100
        x = self.screen_width - panel_w - 15
        y = 15
        
        self._draw_rounded_panel(screen, x, y, panel_w, panel_h)
        
        season = game_state.get('season', 'Spring')
        season_icons = {'Spring': '🌸', 'Summer': '☀️', 'Autumn': '🍂', 'Winter': '❄️'}
        season_icon = season_icons.get(season, '🌸')
        year = game_state.get('year', 1)
        
        season_text = self.font_title.render(f"{season_icon} Year {year} {season}", 
                                            True, self.theme['text'])
        screen.blit(season_text, (x + 15, y + 12))
        
        day = game_state.get('day', 1)
        hour = game_state.get('hour', 12)
        minute = game_state.get('minute', 0)
        time_str = f"Day {day}  {hour:02d}:{minute:02d}"
        
        time_text = self.font_large.render(time_str, True, self.theme['accent_cyan'])
        screen.blit(time_text, (x + 15, y + 40))
        
        # 天气
        weather = game_state.get('weather', 'Sunny')
        weather_icons = {'Sunny': '☀️', 'Rainy': '🌧️', 'Snowy': '❄️', 'Cloudy': '☁️'}
        weather_icon = weather_icons.get(weather, '☀️')
        
        weather_text = self.font.render(f"{weather_icon} {weather}", True, self.theme['text_dim'])
        screen.blit(weather_text, (x + 15, y + 68))
        
    def _render_toolbar(self, screen, game_state):
        """渲染底部工具栏"""
        bar_h = 55
        y = self.screen_height - bar_h - 12
        
        bar_rect = pygame.Rect(12, y, self.screen_width - 24, bar_h)
        self._draw_rounded_rect(screen, bar_rect, 10, self.theme['panel_bg'])
        pygame.draw.rect(screen, self.theme['panel_border'], bar_rect, 2, border_radius=10)
        
        # 控制提示
        controls = game_state.get('controls', 'WASD:移动 | 空格:切换')
        ctrl_text = self.font.render(controls, True, self.theme['text_dim'])
        screen.blit(ctrl_text, (25, y + 18))
        
        # 速度指示
        speed = game_state.get('speed', 1)
        paused = game_state.get('paused', False)
        
        if paused:
            speed_text = "⏸️ 暂停"
            speed_color = (255, 200, 100)
        else:
            speed_text = f"⚡ {speed}x"
            speed_color = (100, 255, 150)
            
        pulse_alpha = int(100 + 50 * self.pulse)
        pulse_rect = pygame.Rect(self.screen_width // 2 - 35, y + 10, 70, 35)
        pulse_surf = pygame.Surface((70, 35), pygame.SRCALPHA)
        pygame.draw.rect(pulse_surf, (*speed_color, pulse_alpha), (0, 0, 70, 35), border_radius=8)
        screen.blit(pulse_surf, pulse_rect.topleft)
        
        speed_render = self.font_large.render(speed_text, True, speed_color)
        screen.blit(speed_render, (self.screen_width // 2 - 30, y + 15))
        
        # 模式指示
        mode = game_state.get('mode', 'PLAYER')
        mode_color = self.theme['energy_low'] if mode == 'GOD' else self.theme['accent_cyan']
        mode_text = self.font.render(f"👁️ {mode} MODE", True, mode_color)
        screen.blit(mode_text, (self.screen_width - mode_text.get_width() - 25, y + 18))
        
    def _render_minimap(self, screen, game_state):
        """渲染小地图"""
        size = 140
        x = self.screen_width - size - 20
        y = 130
        
        map_rect = pygame.Rect(x, y, size, size)
        self._draw_rounded_rect(screen, map_rect, 10, (20, 25, 30, 240))
        pygame.draw.rect(screen, self.theme['panel_border'], map_rect, 2, border_radius=10)
        
        title = self.font.render("🗺️ 地图", True, self.theme['text'])
        screen.blit(title, (x + 10, y + 8))
        
        map_area = pygame.Rect(x + 8, y + 32, size - 16, size - 40)
        pygame.draw.rect(screen, (35, 40, 50), map_area, border_radius=4)
        
        if game_state.get('player_pos'):
            px, py = game_state['player_pos']
            world_w = game_state.get('world_width', 100)
            world_h = game_state.get('world_height', 100)
            
            dot_x = map_area.x + (px / world_w) * map_area.width
            dot_y = map_area.y + (py / world_h) * map_area.height
            
            pulse_size = 4 + int(2 * self.pulse)
            pygame.draw.circle(screen, (255, 215, 0), (int(dot_x), int(dot_y)), pulse_size)
            pygame.draw.circle(screen, (255, 255, 255), (int(dot_x), int(dot_y)), 3)
            
    def _render_modern_bar(self, screen, x, y, width, height, percent, icon, color):
        """渲染现代进度条"""
        icon_text = self.font_large.render(icon, True, color)
        screen.blit(icon_text, (x, y - 2))
        
        bar_x = x + 30
        bar_rect = pygame.Rect(bar_x, y + 2, width - 40, height - 4)
        pygame.draw.rect(screen, (40, 45, 55), bar_rect, border_radius=height//2)
        
        fill_width = int((width - 40) * max(0, min(1, percent)))
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, y + 2, fill_width, height - 4)
            
            for i in range(fill_width):
                gradient = i / fill_width
                r = int(color[0] * (0.7 + 0.3 * gradient))
                g = int(color[1] * (0.7 + 0.3 * gradient))
                b = int(color[2] * (0.7 + 0.3 * gradient))
                pygame.draw.line(screen, (r, g, b), 
                               (bar_x + i, y + 2), 
                               (bar_x + i, y + height - 6))
                               
            highlight_rect = pygame.Rect(bar_x, y + 2, fill_width, 3)
            pygame.draw.rect(screen, 
                           (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60)),
                           highlight_rect, border_radius=2)
            
        value_text = self.font.render(f"{int(percent * 100)}", True, self.theme['text'])
        screen.blit(value_text, (bar_x + width - 35, y + 1))
        
    def _get_energy_color(self, energy):
        """根据能量值获取颜色"""
        if energy > 60:
            return self.theme['energy_high']
        elif energy > 30:
            return self.theme['energy_mid']
        else:
            return self.theme['energy_low']
