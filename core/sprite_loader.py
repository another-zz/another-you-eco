"""
Sprite Sheet Loader - 精灵图加载器
参考 PyDew Valley 实现
"""

import pygame
from typing import Dict, List, Tuple
import json
import os

class SpriteSheet:
    """精灵图"""
    
    def __init__(self, image_path: str, tile_width: int = 16, tile_height: int = 16):
        self.sheet = pygame.image.load(image_path).convert_alpha()
        self.tile_width = tile_width
        self.tile_height = tile_height
        
        # 计算行列数
        self.cols = self.sheet.get_width() // tile_width
        self.rows = self.sheet.get_height() // tile_height
        
    def get_image(self, col: int, row: int, width: int = None, height: int = None) -> pygame.Surface:
        """获取单个精灵"""
        width = width or self.tile_width
        height = height or self.tile_height
        
        x = col * self.tile_width
        y = row * self.tile_height
        
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))
        return image
        
    def get_animation(self, start_col: int, row: int, frames: int) -> List[pygame.Surface]:
        """获取动画帧"""
        return [self.get_image(start_col + i, row) for i in range(frames)]


class CharacterSprite:
    """角色精灵（4方向行走动画）"""
    
    # 方向映射
    DIRECTIONS = {
        'down': 0,
        'left': 1,
        'right': 2,
        'up': 3,
    }
    
    def __init__(self, sprite_sheet: SpriteSheet, color_overlay: Tuple[int, int, int] = None):
        self.sprite_sheet = sprite_sheet
        self.color_overlay = color_overlay
        
        # 加载4方向行走动画（每方向4帧）
        self.animations = {}
        for direction, row in self.DIRECTIONS.items():
            frames = sprite_sheet.get_animation(0, row, 4)
            
            # 应用颜色叠加
            if color_overlay:
                frames = [self._apply_color(f, color_overlay) for f in frames]
                
            self.animations[direction] = frames
            
        # 当前状态
        self.current_direction = 'down'
        self.current_frame = 0
        self.animation_speed = 0.15
        self.animation_timer = 0
        self.is_moving = False
        
    def _apply_color(self, image: pygame.Surface, color: Tuple[int, int, int]) -> pygame.Surface:
        """应用颜色叠加到衣服区域"""
        # 创建副本
        colored = image.copy()
        
        # 遍历像素，替换特定颜色（假设衣服是白色/灰色区域）
        for x in range(colored.get_width()):
            for y in range(colored.get_height()):
                pixel = colored.get_at((x, y))
                # 如果是亮色系（衣服），替换为目标颜色
                if pixel.a > 0 and pixel.r > 200 and pixel.g > 200 and pixel.b > 200:
                    # 保持亮度变化
                    brightness = (pixel.r + pixel.g + pixel.b) / 3 / 255
                    new_color = (
                        min(255, int(color[0] * brightness)),
                        min(255, int(color[1] * brightness)),
                        min(255, int(color[2] * brightness)),
                        pixel.a
                    )
                    colored.set_at((x, y), new_color)
                    
        return colored
        
    def update(self, dt: float, dx: float = 0, dy: float = 0):
        """更新动画"""
        # 判断方向
        if abs(dx) > abs(dy):
            if dx > 0:
                self.current_direction = 'right'
            elif dx < 0:
                self.current_direction = 'left'
        else:
            if dy > 0:
                self.current_direction = 'down'
            elif dy < 0:
                self.current_direction = 'up'
                
        # 更新动画帧
        self.is_moving = dx != 0 or dy != 0
        
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % 4
        else:
            self.current_frame = 0
            
    def get_current_image(self) -> pygame.Surface:
        """获取当前帧"""
        return self.animations[self.current_direction][self.current_frame]
        
    def render(self, screen: pygame.Surface, x: int, y: int, scale: float = 2.0):
        """渲染"""
        image = self.get_current_image()
        
        # 缩放
        if scale != 1.0:
            new_size = (int(image.get_width() * scale), int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
            
        # 居中绘制
        draw_x = x - image.get_width() // 2
        draw_y = y - image.get_height() // 2
        
        screen.blit(image, (draw_x, draw_y))


class TilesetManager:
    """瓦片集管理器"""
    
    # 默认颜色定义（在没有外部tileset时使用）
    TILE_COLORS = {
        'grass': [(100, 160, 70), (110, 170, 80), (90, 150, 60)],
        'forest': [(40, 100, 50), (35, 90, 45), (50, 110, 60)],
        'mountain': [(120, 120, 130), (110, 110, 120), (130, 130, 140)],
        'water': [(60, 110, 200), (70, 120, 210), (55, 105, 195)],
        'sand': [(200, 180, 120), (210, 190, 130)],
        'snow': [(240, 250, 255), (250, 255, 255)],
        'house': [(150, 100, 70), (130, 80, 50)],
    }
    
    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size
        self.tiles: Dict[str, pygame.Surface] = {}
        self._generate_default_tiles()
        
    def _generate_default_tiles(self):
        """生成默认瓦片（程序生成，不依赖外部资产）"""
        import random
        
        for tile_type, colors in self.TILE_COLORS.items():
            # 为每种地形生成几个变体
            for i, base_color in enumerate(colors):
                tile = pygame.Surface((self.tile_size, self.tile_size))
                tile.fill(base_color)
                
                # 添加纹理细节
                if tile_type == 'grass':
                    self._add_grass_detail(tile, base_color)
                elif tile_type == 'forest':
                    self._add_tree_detail(tile, base_color)
                elif tile_type == 'mountain':
                    self._add_mountain_detail(tile, base_color)
                elif tile_type == 'water':
                    self._add_water_detail(tile, base_color)
                elif tile_type == 'house':
                    self._add_house_detail(tile, base_color)
                    
                self.tiles[f"{tile_type}_{i}"] = tile
                
    def _add_grass_detail(self, surface: pygame.Surface, base_color: Tuple[int, int, int]):
        """添加草地细节"""
        import random
        # 随机小点作为草叶
        for _ in range(10):
            x = random.randint(2, self.tile_size - 3)
            y = random.randint(2, self.tile_size - 3)
            color = (
                min(255, base_color[0] + 20),
                min(255, base_color[1] + 20),
                min(255, base_color[2] + 10)
            )
            pygame.draw.rect(surface, color, (x, y, 2, 2))
            
    def _add_tree_detail(self, surface: pygame.Surface, base_color: Tuple[int, int, int]):
        """添加树木细节"""
        center = self.tile_size // 2
        # 树干
        trunk_color = (80, 50, 30)
        pygame.draw.rect(surface, trunk_color, (center - 3, center + 5, 6, self.tile_size - center - 5))
        # 树冠（多层）
        leaf_colors = [(30, 80, 40), (40, 100, 50), (50, 120, 60)]
        for i, color in enumerate(leaf_colors):
            radius = self.tile_size // 2 - i * 3
            offset_y = -i * 4
            pygame.draw.circle(surface, color, (center, center + offset_y), radius)
            
    def _add_mountain_detail(self, surface: pygame.Surface, base_color: Tuple[int, int, int]):
        """添加山峰细节"""
        center = self.tile_size // 2
        # 山峰三角形
        peak_color = (140, 140, 150)
        points = [
            (center, 4),
            (self.tile_size - 4, self.tile_size - 4),
            (4, self.tile_size - 4)
        ]
        pygame.draw.polygon(surface, peak_color, points)
        # 雪顶
        snow_points = [
            (center, 4),
            (center + 6, 12),
            (center - 6, 12)
        ]
        pygame.draw.polygon(surface, (250, 250, 255), snow_points)
        
    def _add_water_detail(self, surface: pygame.Surface, base_color: Tuple[int, int, int]):
        """添加水波纹"""
        # 简单的波纹线条
        wave_color = (80, 140, 220)
        for i in range(3):
            y = 8 + i * 8
            pygame.draw.line(surface, wave_color, (4, y), (self.tile_size - 4, y), 1)
            
    def _add_house_detail(self, surface: pygame.Surface, base_color: Tuple[int, int, int]):
        """添加房屋细节"""
        # 房屋主体
        wall_color = (180, 140, 100)
        pygame.draw.rect(surface, wall_color, (4, 10, self.tile_size - 8, self.tile_size - 14))
        # 屋顶
        roof_color = (120, 60, 40)
        points = [
            (2, 10),
            (self.tile_size // 2, 2),
            (self.tile_size - 2, 10)
        ]
        pygame.draw.polygon(surface, roof_color, points)
        # 门
        pygame.draw.rect(surface, (80, 50, 30), (self.tile_size // 2 - 4, 18, 8, 14))
        
    def get_tile(self, tile_type: str, variant: int = 0) -> pygame.Surface:
        """获取瓦片"""
        key = f"{tile_type}_{variant % 3}"
        return self.tiles.get(key, self.tiles.get('grass_0'))
