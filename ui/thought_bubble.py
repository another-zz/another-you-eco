"""
Thought Bubble - AI内心独白气泡（清晰版）
大号字体 + 白色描边 + 深色背景
"""

import pygame
import math
import time

class ThoughtBubble:
    """AI内心独白气泡 - 清晰易读版"""
    
    def __init__(self):
        # 大号字体
        self.font = pygame.font.SysFont('microsoftyahei', 18, bold=True)
        self.text = ""
        self.color = (60, 60, 70, 220)  # 深色半透明背景
        self.alpha = 0
        self.target_alpha = 0
        self.float_offset = 0
        self.last_update = time.time()
        
    def update(self, dt: float, thought_text: str):
        """更新气泡"""
        self.text = thought_text
        
        # 淡入淡出
        if self.target_alpha > 0:
            self.alpha = min(255, self.alpha + dt * 400)
        else:
            self.alpha = max(0, self.alpha - dt * 200)
            
        # 浮动动画
        self.float_offset = math.sin(time.time() * 2.5) * 3
        
    def set_visible(self, visible: bool):
        self.target_alpha = 255 if visible else 0
        
    def render(self, screen: pygame.Surface, x: int, y: int):
        """渲染气泡 - 大号字体+白色描边+深色背景"""
        if self.alpha <= 0 or not self.text:
            return
            
        # 气泡位置：AI头顶上方50像素，带浮动
        bubble_y = y - 55 + self.float_offset
        
        # 渲染文字（带描边）
        text_surf = self._render_text_with_outline(self.text, (255, 255, 255), (0, 0, 0), 2)
        text_w = text_surf.get_width()
        text_h = text_surf.get_height()
        
        # 气泡尺寸
        padding_x = 12
        padding_y = 8
        bubble_w = text_w + padding_x * 2
        bubble_h = text_h + padding_y * 2
        bubble_x = x - bubble_w // 2
        bubble_y = bubble_y - bubble_h
        
        # 绘制气泡背景（深色半透明）
        bg_color = (40, 40, 50, int(220 * self.alpha / 255))
        bubble_surf = pygame.Surface((bubble_w, bubble_h), pygame.SRCALPHA)
        pygame.draw.rect(bubble_surf, bg_color, (0, 0, bubble_w, bubble_h), border_radius=10)
        
        # 气泡边框
        border_color = (100, 100, 120, int(150 * self.alpha / 255))
        pygame.draw.rect(bubble_surf, border_color, (0, 0, bubble_w, bubble_h), width=2, border_radius=10)
        
        # 小尾巴
        tail_color = (40, 40, 50, int(220 * self.alpha / 255))
        tail_points = [
            (bubble_w // 2 - 8, bubble_h),
            (bubble_w // 2 + 8, bubble_h),
            (bubble_w // 2, bubble_h + 10)
        ]
        pygame.draw.polygon(bubble_surf, tail_color, tail_points)
        pygame.draw.polygon(bubble_surf, border_color, tail_points, width=1)
        
        # 绘制
        screen.blit(bubble_surf, (bubble_x, bubble_y))
        screen.blit(text_surf, (bubble_x + padding_x, bubble_y + padding_y))
        
    def _render_text_with_outline(self, text: str, text_color: tuple, outline_color: tuple, outline_width: int) -> pygame.Surface:
        """渲染带描边的文字"""
        # 主文字
        text_surf = self.font.render(text, True, text_color)
        
        # 创建带描边的表面
        w, h = text_surf.get_size()
        outline_surf = pygame.Surface((w + outline_width * 2, h + outline_width * 2), pygame.SRCALPHA)
        
        # 绘制描边（8个方向）
        outline_text = self.font.render(text, True, outline_color)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_surf.blit(outline_text, (outline_width + dx, outline_width + dy))
        
        # 绘制主文字
        outline_surf.blit(text_surf, (outline_width, outline_width))
        
        return outline_surf
