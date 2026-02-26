"""
Quality Tileset - 高质量瓦片集（NEAREST缩放 + 32x32像素艺术）
"""

import pygame
import random
from typing import Dict, Tuple

TILE_SIZE = 32

class QualityTileset:
    """高质量瓦片集 - 程序生成Stardew风格"""
    
    def __init__(self):
        self.tiles: Dict[str, pygame.Surface] = {}
        self._generate_all_tiles()
        
    def _generate_all_tiles(self):
        """生成所有高质量瓦片"""
        # 草地（3种变体，带纹理细节）
        for i in range(3):
            self.tiles[f'grass_{i}'] = self._create_grass(i)
            
        # 树（3种变体，带树叶层次）
        for i in range(3):
            self.tiles[f'forest_{i}'] = self._create_tree(i)
            
        # 山（3种变体，带岩石纹理）
        for i in range(3):
            self.tiles[f'mountain_{i}'] = self._create_mountain(i)
            
        # 水（3种变体，带波纹）
        for i in range(3):
            self.tiles[f'water_{i}'] = self._create_water(i)
            
        # 沙地
        self.tiles['sand_0'] = self._create_sand()
        
    def _create_grass(self, variant: int) -> pygame.Surface:
        """创建草地瓦片 - 带草叶纹理"""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # 基础绿色（3种变体）
        base_colors = [(100, 160, 70), (110, 170, 80), (90, 150, 60)]
        base = base_colors[variant]
        tile.fill(base)
        
        # 添加草叶细节
        for _ in range(15):
            x = random.randint(2, TILE_SIZE - 4)
            y = random.randint(2, TILE_SIZE - 4)
            # 草叶颜色（稍亮）
            grass_color = (
                min(255, base[0] + random.randint(10, 30)),
                min(255, base[1] + random.randint(10, 30)),
                min(255, base[2] + random.randint(5, 15))
            )
            # 小草叶（1-2像素）
            pygame.draw.rect(tile, grass_color, (x, y, random.randint(1, 2), random.randint(2, 4)))
            
        # 添加一些暗色草叶增加层次
        for _ in range(8):
            x = random.randint(2, TILE_SIZE - 4)
            y = random.randint(2, TILE_SIZE - 4)
            dark_color = (
                max(0, base[0] - random.randint(10, 25)),
                max(0, base[1] - random.randint(10, 25)),
                max(0, base[2] - random.randint(5, 15))
            )
            pygame.draw.rect(tile, dark_color, (x, y, 1, random.randint(2, 3)))
            
        return tile
        
    def _create_tree(self, variant: int) -> pygame.Surface:
        """创建树瓦片 - 带树叶层次"""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # 树干（底部居中）
        trunk_color = (80, 50, 30)
        trunk_width = 6
        trunk_x = (TILE_SIZE - trunk_width) // 2
        pygame.draw.rect(tile, trunk_color, (trunk_x, TILE_SIZE - 12, trunk_width, 12))
        
        # 树叶层次（3层，从大到小）
        leaf_colors = [
            (30, 100, 40),   # 底层深色
            (45, 130, 55),   # 中层
            (60, 160, 70),   # 顶层亮色
        ]
        
        center_x = TILE_SIZE // 2
        base_y = TILE_SIZE - 10
        
        # 底层树冠（最大）
        pygame.draw.circle(tile, leaf_colors[0], (center_x, base_y - 8), 12)
        # 中层
        pygame.draw.circle(tile, leaf_colors[1], (center_x, base_y - 14), 9)
        # 顶层（最小）
        pygame.draw.circle(tile, leaf_colors[2], (center_x, base_y - 18), 6)
        
        # 添加树叶纹理点
        for _ in range(8):
            angle = random.uniform(0, 3.14)
            dist = random.randint(4, 10)
            px = center_x + int(math.cos(angle) * dist)
            py = base_y - 12 + int(math.sin(angle) * dist * 0.5)
            if 0 <= px < TILE_SIZE and 0 <= py < TILE_SIZE:
                highlight = (80, 180, 90)
                tile.set_at((px, py), highlight)
                
        return tile
        
    def _create_mountain(self, variant: int) -> pygame.Surface:
        """创建山瓦片 - 带岩石纹理"""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # 基础岩石色
        rock_colors = [(100, 100, 110), (110, 110, 120), (90, 90, 100)]
        base = rock_colors[variant]
        tile.fill(base)
        
        # 山峰形状（三角形）
        peak_color = (130, 130, 140)
        points = [
            (TILE_SIZE // 2, 4),
            (TILE_SIZE - 4, TILE_SIZE - 4),
            (4, TILE_SIZE - 4)
        ]
        pygame.draw.polygon(tile, peak_color, points)
        
        # 雪顶
        snow_points = [
            (TILE_SIZE // 2, 4),
            (TILE_SIZE // 2 + 8, 14),
            (TILE_SIZE // 2 - 8, 14)
        ]
        pygame.draw.polygon(tile, (240, 250, 255), snow_points)
        
        # 岩石纹理（随机暗色斑点）
        for _ in range(12):
            x = random.randint(4, TILE_SIZE - 5)
            y = random.randint(10, TILE_SIZE - 5)
            rock_dark = (70, 70, 80)
            pygame.draw.rect(tile, rock_dark, (x, y, random.randint(2, 4), random.randint(2, 3)))
            
        # 岩石高光
        for _ in range(8):
            x = random.randint(4, TILE_SIZE - 5)
            y = random.randint(10, TILE_SIZE - 5)
            rock_light = (150, 150, 160)
            pygame.draw.rect(tile, rock_light, (x, y, 1, 1))
            
        return tile
        
    def _create_water(self, variant: int) -> pygame.Surface:
        """创建水瓦片 - 带波纹基础"""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        
        # 基础水色（3种变体）
        water_colors = [(50, 100, 180), (55, 110, 190), (45, 95, 175)]
        base = water_colors[variant]
        tile.fill(base)
        
        # 波纹线条（水平）
        wave_colors = [(70, 130, 210), (80, 140, 220)]
        for i in range(3):
            y = 8 + i * 10 + variant * 2  # 变体偏移
            wave_color = wave_colors[i % 2]
            pygame.draw.line(tile, wave_color, (4, y), (TILE_SIZE - 4, y), 1)
            
        # 高光点（模拟反光）
        for _ in range(5):
            x = random.randint(4, TILE_SIZE - 5)
            y = random.randint(4, TILE_SIZE - 5)
            highlight = (100, 160, 240)
            tile.set_at((x, y), highlight)
            
        return tile
        
    def _create_sand(self) -> pygame.Surface:
        """创建沙地瓦片"""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        base = (210, 190, 130)
        tile.fill(base)
        
        # 沙粒纹理
        for _ in range(20):
            x = random.randint(0, TILE_SIZE - 1)
            y = random.randint(0, TILE_SIZE - 1)
            grain_color = (
                base[0] + random.randint(-15, 15),
                base[1] + random.randint(-15, 15),
                base[2] + random.randint(-10, 10)
            )
            tile.set_at((x, y), grain_color)
            
        return tile
        
    def get_tile(self, tile_type: str, variant: int = 0) -> pygame.Surface:
        """获取瓦片（NEAREST缩放保证像素清晰）"""
        key = f"{tile_type}_{variant % 3}"
        tile = self.tiles.get(key, self.tiles.get('grass_0'))
        return tile


import math
