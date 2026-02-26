"""
Particle System - 天气粒子效果
雨、雪、雾等视觉效果
"""

import pygame
import random
import math
from typing import List, Tuple
from core.living_world import Weather

class Particle:
    """单个粒子"""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 life: int, color: Tuple[int, int, int], size: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        
    def update(self):
        """更新粒子"""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.life > 0
        
    def get_alpha(self) -> int:
        """获取透明度"""
        return int(255 * self.life / self.max_life)


class WeatherParticles:
    """天气粒子系统"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles: List[Particle] = []
        
        # 相机偏移（用于跟随）
        self.camera_x = 0
        self.camera_y = 0
        
    def set_camera(self, x: float, y: float):
        """设置相机位置"""
        self.camera_x = x
        self.camera_y = y
        
    def update(self, weather: Weather, intensity: float):
        """更新粒子系统"""
        # 根据天气生成新粒子
        spawn_count = self._get_spawn_count(weather, intensity)
        
        for _ in range(spawn_count):
            particle = self._create_particle(weather, intensity)
            if particle:
                self.particles.append(particle)
                
        # 更新现有粒子
        for p in self.particles:
            p.update()
            
        # 清理死亡粒子
        self.particles = [p for p in self.particles if p.is_alive()]
        
    def _get_spawn_count(self, weather: Weather, intensity: float) -> int:
        """获取生成数量"""
        counts = {
            Weather.SUNNY: 0,
            Weather.CLOUDY: 0,
            Weather.RAINY: int(10 * intensity),
            Weather.STORMY: int(20 * intensity),
            Weather.SNOWY: int(15 * intensity),
            Weather.FOGGY: int(5 * intensity),
        }
        return counts.get(weather, 0)
        
    def _create_particle(self, weather: Weather, intensity: float) -> Particle:
        """创建粒子"""
        # 在屏幕上方生成
        x = random.randint(-100, self.screen_width + 100) + self.camera_x
        y = -50 + self.camera_y
        
        if weather == Weather.RAINY:
            return Particle(
                x=x, y=y,
                vx=-2 + random.uniform(-1, 1),  # 风向
                vy=15 + random.uniform(0, 5),
                life=random.randint(30, 50),
                color=(150, 150, 200),
                size=2
            )
            
        elif weather == Weather.STORMY:
            return Particle(
                x=x, y=y,
                vx=-5 + random.uniform(-2, 2),  # 强风
                vy=20 + random.uniform(0, 10),
                life=random.randint(20, 40),
                color=(100, 100, 150),
                size=3
            )
            
        elif weather == Weather.SNOWY:
            return Particle(
                x=x, y=y,
                vx=random.uniform(-2, 2),
                vy=3 + random.uniform(0, 2),
                life=random.randint(100, 200),
                color=(255, 255, 255),
                size=random.uniform(2, 4)
            )
            
        elif weather == Weather.FOGGY:
            return Particle(
                x=random.randint(0, self.screen_width) + self.camera_x,
                y=random.randint(0, self.screen_height) + self.camera_y,
                vx=random.uniform(-0.5, 0.5),
                vy=random.uniform(-0.5, 0.5),
                life=random.randint(200, 400),
                color=(200, 200, 200),
                size=random.uniform(20, 50)
            )
            
        return None
        
    def render(self, screen: pygame.Surface):
        """渲染粒子"""
        for p in self.particles:
            # 转换到屏幕坐标
            screen_x = int(p.x - self.camera_x)
            screen_y = int(p.y - self.camera_y)
            
            # 检查是否在屏幕内
            if -50 < screen_x < self.screen_width + 50 and -50 < screen_y < self.screen_height + 50:
                alpha = p.get_alpha()
                
                if p.size < 5:  # 雨、雪
                    # 绘制线条或圆点
                    end_x = screen_x + int(p.vx * 2)
                    end_y = screen_y + int(p.vy * 2)
                    
                    color_with_alpha = (*p.color, alpha)
                    # Pygame不支持直接alpha线条，用圆点代替
                    pygame.draw.circle(screen, p.color, (screen_x, screen_y), int(p.size))
                else:  # 雾
                    # 绘制大圆形带透明度
                    s = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*p.color, alpha // 3), 
                                     (int(p.size), int(p.size)), int(p.size))
                    screen.blit(s, (screen_x - int(p.size), screen_y - int(p.size)))


class SeasonEffects:
    """季节视觉效果"""
    
    @staticmethod
    def get_overlay_color(season, hour: int) -> Tuple[int, int, int, int]:
        """获取季节叠加颜色"""
        from core.living_world import Season
        
        # 基础季节色调
        season_tints = {
            Season.SPRING: (200, 255, 200, 20),
            Season.SUMMER: (255, 255, 150, 30),
            Season.AUTUMN: (255, 180, 100, 40),
            Season.WINTER: (220, 240, 255, 60),
        }
        
        tint = list(season_tints.get(season, (255, 255, 255, 0)))
        
        # 夜晚加深
        if hour < 6 or hour > 20:
            tint[3] += 80
            
        return tuple(tint)
        
    @staticmethod
    def render_overlay(screen: pygame.Surface, season, hour: int):
        """渲染季节叠加效果"""
        color = SeasonEffects.get_overlay_color(season, hour)
        
        if color[3] > 0:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill(color)
            screen.blit(overlay, (0, 0))
