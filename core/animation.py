"""
Animation Manager - 动画管理器
处理粒子效果、环境动画
"""

import pygame
import random
import math
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Particle:
    """粒子"""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float
    
    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        
    def is_alive(self) -> bool:
        return self.life > 0
        
    def get_alpha(self) -> int:
        return int(255 * (self.life / self.max_life))


class AnimationManager:
    """动画管理器"""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.water_offset = 0
        self.time = 0
        
    def update(self, dt: float):
        """更新动画"""
        self.time += dt
        self.water_offset += dt * 2
        
        # 更新粒子
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]
        
    def add_dust(self, x: float, y: float):
        """添加走路尘土"""
        for _ in range(3):
            self.particles.append(Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-2, 2),
                vx=random.uniform(-10, 10),
                vy=random.uniform(-20, -5),
                life=random.uniform(0.3, 0.6),
                max_life=0.6,
                color=(180, 160, 140),
                size=random.uniform(2, 4)
            ))
            
    def add_leaf(self, x: float, y: float, season: str = 'autumn'):
        """添加落叶"""
        colors = {
            'spring': [(100, 200, 100), (120, 220, 120)],
            'summer': [(60, 160, 60), (80, 180, 80)],
            'autumn': [(200, 120, 40), (220, 160, 60), (180, 80, 30)],
            'winter': [(240, 250, 255)],
        }
        
        color = random.choice(colors.get(season, colors['autumn']))
        
        self.particles.append(Particle(
            x=x,
            y=y,
            vx=random.uniform(-15, 15),
            vy=random.uniform(5, 20),
            life=random.uniform(1.0, 2.0),
            max_life=2.0,
            color=color,
            size=random.uniform(3, 5)
        ))
        
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float, tile_size: int):
        """渲染粒子"""
        for p in self.particles:
            screen_x = int(p.x - camera_x)
            screen_y = int(p.y - camera_y)
            
            # 检查是否在屏幕内
            if -10 < screen_x < screen.get_width() + 10 and -10 < screen_y < screen.get_height() + 10:
                alpha = p.get_alpha()
                color = (*p.color, alpha)
                
                # 使用带alpha的表面
                s = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (int(p.size), int(p.size)), int(p.size))
                screen.blit(s, (screen_x - int(p.size), screen_y - int(p.size)))


class EnvironmentEffects:
    """环境效果"""
    
    @staticmethod
    def render_water_animation(screen: pygame.Surface, x: int, y: int, 
                               size: int, offset: float, base_color: Tuple[int, int, int]):
        """渲染水波动画"""
        # 基础色
        pygame.draw.rect(screen, base_color, (x, y, size, size))
        
        # 波纹
        wave_color = (min(255, base_color[0] + 30), 
                     min(255, base_color[1] + 30), 
                     min(255, base_color[2] + 20))
        
        wave_y = y + 8 + int(math.sin(offset + x * 0.1) * 3)
        pygame.draw.line(screen, wave_color, (x + 4, wave_y), (x + size - 4, wave_y), 2)
        
        wave_y2 = y + 18 + int(math.sin(offset + x * 0.1 + 2) * 3)
        pygame.draw.line(screen, wave_color, (x + 4, wave_y2), (x + size - 4, wave_y2), 2)
        
    @staticmethod
    def render_tree_sway(screen: pygame.Surface, x: int, y: int, 
                        size: int, offset: float, base_color: Tuple[int, int, int]):
        """渲染树摇摆动画"""
        # 树干
        trunk_color = (80, 50, 30)
        pygame.draw.rect(screen, trunk_color, 
                        (x + size//2 - 3, y + size//2, 6, size//2))
        
        # 摇摆的树冠
        sway_x = int(math.sin(offset * 2) * 2)
        
        # 多层树冠
        colors = [(30, 80, 40), (40, 100, 50), (50, 120, 60)]
        for i, color in enumerate(colors):
            radius = size//2 - i * 4
            offset_y = -i * 5
            center_x = x + size//2 + sway_x * (i + 1) // 3
            center_y = y + size//2 + offset_y
            pygame.draw.circle(screen, color, (center_x, center_y), radius)
            
    @staticmethod
    def render_day_night_overlay(screen: pygame.Surface, hour: int, minute: int):
        """渲染日夜叠加效果"""
        # 计算亮度 (0-1)
        if 6 <= hour < 18:
            # 白天
            peak = 12
            dist = abs(hour - peak)
            brightness = 0.3 + 0.7 * (1 - dist / 6)
        else:
            # 夜晚
            brightness = 0.15
            
        if brightness < 0.9:
            # 创建暗化叠加层
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            alpha = int((1 - brightness) * 150)
            overlay.fill((10, 15, 40, alpha))
            screen.blit(overlay, (0, 0))
            
        # 夜晚灯火效果
        if hour >= 19 or hour < 6:
            # 添加一些随机灯火（模拟远处的房屋）
            pass  # 可以在具体房屋位置添加
