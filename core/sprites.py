"""
Sprites - AI角色精灵系统
带行走动画的像素小人
"""

import pygame
import math
from typing import Tuple, Dict
from enum import Enum, auto

class Direction(Enum):
    """方向"""
    DOWN = 0
    LEFT = 1
    RIGHT = 2
    UP = 3

class AgentSprite:
    """AI角色精灵"""
    
    # 衣服颜色（区分不同AI）
    SHIRT_COLORS = [
        (220, 80, 80),   # 红
        (80, 120, 220),  # 蓝
        (80, 180, 80),   # 绿
        (220, 180, 60),  # 黄
        (180, 100, 200), # 紫
        (255, 140, 80),  # 橙
        (100, 200, 200), # 青
        (200, 120, 100), # 棕
    ]
    
    def __init__(self, agent_id: str, name: str, color_idx: int = 0):
        self.agent_id = agent_id
        self.name = name
        self.color_idx = color_idx % len(self.SHIRT_COLORS)
        self.shirt_color = self.SHIRT_COLORS[self.color_idx]
        
        # 动画
        self.direction = Direction.DOWN
        self.frame = 0
        self.animation_timer = 0
        self.is_moving = False
        
        # 大小
        self.size = 24  # 像素大小
        
    def update(self, dx: float = 0, dy: float = 0):
        """更新动画"""
        # 判断方向
        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = Direction.RIGHT
            elif dx < 0:
                self.direction = Direction.LEFT
        else:
            if dy > 0:
                self.direction = Direction.DOWN
            elif dy < 0:
                self.direction = Direction.UP
                
        # 更新动画帧
        self.is_moving = dx != 0 or dy != 0
        if self.is_moving:
            self.animation_timer += 1
            if self.animation_timer >= 8:  # 每8帧切换
                self.animation_timer = 0
                self.frame = (self.frame + 1) % 4
        else:
            self.frame = 0
            
    def render(self, screen: pygame.Surface, x: int, y: int, 
               energy: float = 100, is_player: bool = False):
        """渲染角色"""
        
        size = self.size
        
        # 玩家高亮圈
        if is_player:
            pygame.draw.circle(screen, (255, 215, 0), (x, y), size + 4, 3)
            
        # 阴影
        shadow_rect = pygame.Rect(x - size//2 + 2, y + size//3, size - 4, 6)
        pygame.draw.ellipse(screen, (0, 0, 0, 50), shadow_rect)
        
        # 身体摆动（行走动画）
        bob = 0
        if self.is_moving:
            bob = math.sin(self.frame * math.pi / 2) * 2
            
        body_y = y - size//3 + bob
        
        # 腿（根据方向）
        leg_color = (60, 40, 30)
        if self.direction in [Direction.LEFT, Direction.RIGHT]:
            # 侧面腿
            leg_offset = math.sin(self.frame * math.pi / 2) * 3 if self.is_moving else 0
            pygame.draw.rect(screen, leg_color, 
                           (x - 4 + leg_offset, y, 3, size//2))
            pygame.draw.rect(screen, leg_color, 
                           (x + 1 - leg_offset, y, 3, size//2))
        else:
            # 正面/背面腿
            leg_offset = math.sin(self.frame * math.pi / 2) * 2 if self.is_moving else 0
            pygame.draw.rect(screen, leg_color, (x - 5, y + leg_offset, 4, size//2))
            pygame.draw.rect(screen, leg_color, (x + 1, y - leg_offset, 4, size//2))
            
        # 身体（衣服）
        body_rect = pygame.Rect(x - size//3, body_y, size*2//3, size//2)
        pygame.draw.rect(screen, self.shirt_color, body_rect)
        pygame.draw.rect(screen, (0, 0, 0), body_rect, 1)  # 边框
        
        # 头
        head_size = size // 2
        head_y = body_y - head_size + 4
        pygame.draw.circle(screen, (255, 220, 180), (x, head_y), head_size//2)
        pygame.draw.circle(screen, (0, 0, 0), (x, head_y), head_size//2, 1)
        
        # 眼睛（根据方向）
        eye_color = (50, 30, 20)
        if self.direction == Direction.DOWN:
            pygame.draw.circle(screen, eye_color, (x - 2, head_y), 1)
            pygame.draw.circle(screen, eye_color, (x + 2, head_y), 1)
        elif self.direction == Direction.UP:
            pass  # 背面不画眼睛
        elif self.direction == Direction.LEFT:
            pygame.draw.circle(screen, eye_color, (x - 2, head_y), 1)
        elif self.direction == Direction.RIGHT:
            pygame.draw.circle(screen, eye_color, (x + 2, head_y), 1)
            
        # 名字标签
        font = pygame.font.SysFont('microsoftyahei', 10)
        name_text = font.render(self.name, True, (255, 255, 255))
        name_x = x - name_text.get_width() // 2
        name_y = y - size - 12
        
        # 名字背景
        bg_rect = pygame.Rect(name_x - 2, name_y - 1, 
                            name_text.get_width() + 4, name_text.get_height() + 2)
        pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
        screen.blit(name_text, (name_x, name_y))
        
        # 能量条（小）
        bar_width = 20
        bar_height = 3
        energy_pct = energy / 100
        bar_x = x - bar_width // 2
        bar_y = y + size//2 + 2
        
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        energy_color = (0, 255, 0) if energy_pct > 0.5 else (255, 200, 0) if energy_pct > 0.3 else (255, 0, 0)
        pygame.draw.rect(screen, energy_color, 
                        (bar_x, bar_y, int(bar_width * energy_pct), bar_height))
