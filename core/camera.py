"""
Camera - 游戏相机系统
平滑跟随 + 边界限制
"""

import pygame
from typing import Tuple

class GameCamera:
    """游戏相机"""
    
    def __init__(self, world_width: int, world_height: int, tile_size: int):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        
        self.world_width = world_width
        self.world_height = world_height
        self.tile_size = tile_size
        
        # 跟随目标
        self.target = None
        self.smooth_speed = 0.1
        
        # 上帝模式
        self.god_mode = False
        self.min_zoom = 0.3
        self.max_zoom = 2.0
        self.god_max_zoom = 0.1  # 上帝模式可以缩得更小
        
    def set_target(self, target):
        """设置跟随目标"""
        self.target = target
        
    def toggle_god_mode(self):
        """切换上帝模式"""
        self.god_mode = not self.god_mode
        if not self.god_mode:
            # 退出上帝模式，恢复正常缩放
            self.zoom = min(self.zoom, self.max_zoom)
        return self.god_mode
        
    def update(self, screen_width: int, screen_height: int):
        """更新相机位置"""
        
        if self.target and not self.god_mode:
            # 平滑跟随目标
            target_x = self.target.x * self.tile_size - screen_width // 2
            target_y = self.target.y * self.tile_size - screen_height // 2
            
            self.x += (target_x - self.x) * self.smooth_speed
            self.y += (target_y - self.y) * self.smooth_speed
        
        # 限制边界
        max_x = self.world_width * self.tile_size - screen_width
        max_y = self.world_height * self.tile_size - screen_height
        
        self.x = max(0, min(max_x, self.x))
        self.y = max(0, min(max_y, self.y))
        
    def move(self, dx: float, dy: float):
        """移动相机（上帝模式）"""
        if self.god_mode:
            self.x += dx * 20 / self.zoom  # 缩放越小移动越快
            self.y += dy * 20 / self.zoom
            
    def zoom_in(self):
        """放大"""
        max_z = self.god_max_zoom if self.god_mode else self.max_zoom
        self.zoom = min(max_z, self.zoom * 1.1)
        
    def zoom_out(self):
        """缩小"""
        min_z = self.min_zoom
        self.zoom = max(min_z, self.zoom / 1.1)
        
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """世界坐标转屏幕坐标"""
        screen_x = int(world_x * self.tile_size - self.x)
        screen_y = int(world_y * self.tile_size - self.y)
        return screen_x, screen_y
        
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """屏幕坐标转世界坐标"""
        world_x = int((screen_x + self.x) / self.tile_size)
        world_y = int((screen_y + self.y) / self.tile_size)
        return world_x, world_y
        
    def get_visible_range(self, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
        """获取可见范围（用于优化渲染）"""
        start_col = max(0, int(self.x // self.tile_size))
        end_col = min(self.world_width, 
                     int((self.x + screen_width) // self.tile_size) + 1)
        start_row = max(0, int(self.y // self.tile_size))
        end_row = min(self.world_height, 
                     int((self.y + screen_height) // self.tile_size) + 1)
        return start_col, end_col, start_row, end_row
