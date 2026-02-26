"""
Tilemap System - 瓦片地图系统
参考 Stardew Valley 的 tile-based 渲染
"""

import pygame
from typing import Dict, Tuple, List
from enum import Enum, auto

class TileType(Enum):
    """瓦片类型"""
    GRASS = auto()      # 草地
    FOREST = auto()     # 森林
    MOUNTAIN = auto()   # 山地
    WATER = auto()      # 水
    SAND = auto()       # 沙滩
    SNOW = auto()       # 雪地
    
class Tile:
    """单个瓦片"""
    
    # 基础颜色
    COLORS = {
        TileType.GRASS: (100, 160, 70),
        TileType.FOREST: (40, 100, 50),
        TileType.MOUNTAIN: (120, 120, 130),
        TileType.WATER: (60, 110, 200),
        TileType.SAND: (200, 180, 120),
        TileType.SNOW: (240, 250, 255),
    }
    
    # 装饰颜色（更亮/更暗的变体）
    VARIANTS = {
        TileType.GRASS: [(110, 170, 80), (90, 150, 60)],
        TileType.FOREST: [(50, 110, 60), (35, 90, 45)],
        TileType.MOUNTAIN: [(130, 130, 140), (110, 110, 120)],
        TileType.WATER: [(70, 120, 210), (55, 105, 195)],
        TileType.SAND: [(210, 190, 130), (190, 170, 110)],
        TileType.SNOW: [(250, 255, 255), (230, 245, 250)],
    }
    
    def __init__(self, tile_type: TileType, x: int, y: int):
        self.type = tile_type
        self.x = x
        self.y = y
        self.variant = (x + y) % 2  # 简单的变体选择
        
        # 可行走？
        self.walkable = tile_type not in [TileType.WATER, TileType.MOUNTAIN]
        
        # 资源
        self.resources = {}
        if tile_type == TileType.FOREST:
            self.resources['wood'] = 10
        elif tile_type == TileType.MOUNTAIN:
            self.resources['stone'] = 10
            self.resources['ore'] = 5
            
    def get_color(self) -> Tuple[int, int, int]:
        """获取瓦片颜色"""
        variants = self.VARIANTS.get(self.type)
        if variants:
            return variants[self.variant % len(variants)]
        return self.COLORS.get(self.type, (100, 100, 100))
        
    def render(self, screen: pygame.Surface, x: int, y: int, size: int):
        """渲染瓦片"""
        color = self.get_color()
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, color, rect)
        
        # 绘制边框（ subtle grid）
        pygame.draw.rect(screen, (0, 0, 0, 20), rect, 1)
        
        # 特殊效果
        if self.type == TileType.WATER:
            # 水波纹效果
            import random
            if random.random() < 0.1:
                wave_color = (80, 140, 220)
                wave_rect = pygame.Rect(x + 4, y + size//2, size - 8, 2)
                pygame.draw.rect(screen, wave_color, wave_rect)
                
        elif self.type == TileType.FOREST:
            # 简单的树图标
            trunk_color = (80, 50, 30)
            leaf_color = (30, 80, 40)
            
            # 树干
            trunk = pygame.Rect(x + size//2 - 2, y + size//2, 4, size//2)
            pygame.draw.rect(screen, trunk_color, trunk)
            
            # 树冠
            pygame.draw.circle(screen, leaf_color, 
                             (x + size//2, y + size//3), size//3)
                             
        elif self.type == TileType.MOUNTAIN:
            # 山形
            mountain_color = (90, 90, 100)
            points = [
                (x + size//2, y + 4),
                (x + size - 4, y + size - 4),
                (x + 4, y + size - 4)
            ]
            pygame.draw.polygon(screen, mountain_color, points)


class Tilemap:
    """瓦片地图"""
    
    def __init__(self, width: int, height: int, tile_size: int = 32):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        
        # 2D 瓦片数组
        self.tiles: List[List[Tile]] = []
        
        # 生成地图
        self._generate()
        
    def _generate(self):
        """生成随机地图"""
        import random
        import math
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # 基于距离中心的距离决定地形
                center_x, center_y = self.width // 2, self.height // 2
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # 边缘是山地
                if dist > min(self.width, self.height) * 0.4:
                    tile_type = TileType.MOUNTAIN
                # 河流（简单的水平河流）
                elif abs(y - center_y) < 3 and random.random() > 0.3:
                    tile_type = TileType.WATER
                # 湖泊
                elif dist < 8 and random.random() > 0.5:
                    tile_type = TileType.WATER
                # 森林
                elif random.random() < 0.25:
                    tile_type = TileType.FOREST
                # 沙滩（水边）
                elif random.random() < 0.1:
                    tile_type = TileType.SAND
                else:
                    tile_type = TileType.GRASS
                    
                row.append(Tile(tile_type, x, y))
            self.tiles.append(row)
            
    def get_tile(self, x: int, y: int) -> Tile:
        """获取瓦片"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return Tile(TileType.GRASS, x, y)  # 默认草地
        
    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float, 
               screen_width: int, screen_height: int):
        """渲染可见区域的瓦片"""
        
        # 计算可见范围
        start_col = max(0, int(camera_x // self.tile_size))
        end_col = min(self.width, int((camera_x + screen_width) // self.tile_size) + 1)
        start_row = max(0, int(camera_y // self.tile_size))
        end_row = min(self.height, int((camera_y + screen_height) // self.tile_size) + 1)
        
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile = self.tiles[row][col]
                
                # 计算屏幕位置
                screen_x = int(col * self.tile_size - camera_x)
                screen_y = int(row * self.tile_size - camera_y)
                
                tile.render(screen, screen_x, screen_y, self.tile_size)
