"""
Chunk Manager - 无限世界区块系统（高质量版）
9宫格动态加载，保持画质一致
"""

import random
import math
from typing import Dict, Tuple, List, Set
from dataclasses import dataclass

CHUNK_SIZE = 32

@dataclass
class Chunk:
    cx: int
    cy: int
    tiles: List[List[Tuple[str, int]]]
    obstacles: Set[Tuple[int, int]]
    water: Set[Tuple[int, int]]

class ChunkManager:
    """无限世界区块管理器"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        
    def get_chunk_coord(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """获取世界坐标对应的区块坐标"""
        return (int(world_x // CHUNK_SIZE), int(world_y // CHUNK_SIZE))
        
    def get_tile_in_chunk(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """获取世界坐标在区块内的局部坐标"""
        return (int(world_x % CHUNK_SIZE), int(world_y % CHUNK_SIZE))
        
    def generate_chunk(self, cx: int, cy: int) -> Chunk:
        """生成新区块"""
        chunk_seed = self.seed + cx * 10000 + cy
        rng = random.Random(chunk_seed)
        
        tiles = []
        obstacles = set()
        water = set()
        
        # 距离中心越远，山地越多
        dist = math.sqrt(cx**2 + cy**2)
        
        for y in range(CHUNK_SIZE):
            row = []
            for x in range(CHUNK_SIZE):
                noise = rng.random()
                
                # 根据距离调整地形概率
                if dist > 5:
                    # 远离中心：更多山地
                    if noise < 0.3:
                        tile_type = 'mountain'
                        obstacles.add((x, y))
                    elif noise < 0.5:
                        tile_type = 'forest'
                        obstacles.add((x, y))
                    elif noise < 0.6:
                        tile_type = 'water'
                        water.add((x, y))
                    else:
                        tile_type = 'grass'
                else:
                    # 中心区域：更多平地
                    if noise < 0.12:
                        tile_type = 'mountain'
                        obstacles.add((x, y))
                    elif noise < 0.3:
                        tile_type = 'forest'
                        obstacles.add((x, y))
                    elif noise < 0.4:
                        tile_type = 'water'
                        water.add((x, y))
                    else:
                        tile_type = 'grass'
                        
                row.append((tile_type, rng.randint(0, 2)))
            tiles.append(row)
            
        chunk = Chunk(cx, cy, tiles, obstacles, water)
        self.chunks[(cx, cy)] = chunk
        return chunk
        
    def get_chunk(self, cx: int, cy: int) -> Chunk:
        """获取区块（不存在则生成）"""
        if (cx, cy) not in self.chunks:
            return self.generate_chunk(cx, cy)
        return self.chunks[(cx, cy)]
        
    def get_tile(self, world_x: float, world_y: float) -> Tuple[str, int]:
        """获取世界坐标的地形"""
        cx, cy = self.get_chunk_coord(world_x, world_y)
        lx, ly = self.get_tile_in_chunk(world_x, world_y)
        chunk = self.get_chunk(cx, cy)
        if 0 <= ly < CHUNK_SIZE and 0 <= lx < CHUNK_SIZE:
            return chunk.tiles[ly][lx]
        return ('grass', 0)
        
    def is_walkable(self, world_x: float, world_y: float) -> bool:
        """检查是否可行走（非障碍、非水）"""
        cx, cy = self.get_chunk_coord(world_x, world_y)
        lx, ly = self.get_tile_in_chunk(world_x, world_y)
        chunk = self.get_chunk(cx, cy)
        return (lx, ly) not in chunk.obstacles and (lx, ly) not in chunk.water
        
    def is_water(self, world_x: float, world_y: float) -> bool:
        """检查是否是水"""
        cx, cy = self.get_chunk_coord(world_x, world_y)
        lx, ly = self.get_tile_in_chunk(world_x, world_y)
        chunk = self.get_chunk(cx, cy)
        return (lx, ly) in chunk.water
        
    def update_loaded_chunks(self, center_x: float, center_y: float):
        """更新加载的区块（9宫格）"""
        center_cx, center_cy = self.get_chunk_coord(center_x, center_y)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cx, cy = center_cx + dx, center_cy + dy
                if (cx, cy) not in self.chunks:
                    self.generate_chunk(cx, cy)
                    
    def get_render_chunks(self, camera_x: float, camera_y: float, 
                         screen_width: int, screen_height: int) -> List[Chunk]:
        """获取需要渲染的区块列表"""
        start_cx = int(camera_x // (CHUNK_SIZE * 32))
        end_cx = int((camera_x + screen_width) // (CHUNK_SIZE * 32)) + 1
        start_cy = int(camera_y // (CHUNK_SIZE * 32))
        end_cy = int((camera_y + screen_height) // (CHUNK_SIZE * 32)) + 1
        
        chunks = []
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                chunks.append(self.get_chunk(cx, cy))
        return chunks
