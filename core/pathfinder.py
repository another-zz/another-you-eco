"""
Pathfinder - A* 路径寻找 + 平滑移动
参考 KidsCanCode + PyDew Valley
"""

import heapq
import math
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import pygame

@dataclass
class Node:
    """A*节点"""
    x: int
    y: int
    g: float = 0  # 从起点到当前节点的代价
    h: float = 0  # 启发式估计到终点的代价
    parent: Optional['Node'] = None
    
    @property
    def f(self) -> float:
        return self.g + self.h
        
    def __lt__(self, other):
        return self.f < other.f
        
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
        
    def __hash__(self):
        return hash((self.x, self.y))


class AStarPathfinder:
    """A*路径寻找器"""
    
    def __init__(self, world_width: int, world_height: int):
        self.width = world_width
        self.height = world_height
        self.obstacles: set = set()  # 障碍物集合 (x, y)
        
    def set_obstacles(self, obstacles: List[Tuple[int, int]]):
        """设置障碍物"""
        self.obstacles = set(obstacles)
        
    def is_walkable(self, x: int, y: int) -> bool:
        """检查是否可行走"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return (x, y) not in self.obstacles
        
    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """启发式函数（对角线距离）"""
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        return max(dx, dy) + 0.414 * min(dx, dy)  # 对角线距离
        
    def find_path(self, start_x: float, start_y: float, 
                  end_x: float, end_y: float) -> List[Tuple[int, int]]:
        """寻找路径"""
        start = Node(int(start_x), int(start_y))
        end = Node(int(end_x), int(end_y))
        
        # 如果终点不可行走，找最近的可行走点
        if not self.is_walkable(end.x, end.y):
            end = self._find_nearest_walkable(end.x, end.y)
            if end is None:
                return []
                
        open_set = []
        heapq.heappush(open_set, start)
        
        closed_set: Dict[Tuple[int, int], Node] = {}
        open_dict: Dict[Tuple[int, int], Node] = {(start.x, start.y): start}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if current.x == end.x and current.y == end.y:
                # 找到路径，重建
                return self._reconstruct_path(current)
                
            closed_set[(current.x, current.y)] = current
            
            # 检查8个方向
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx, ny = current.x + dx, current.y + dy
                
                # 跳过已在关闭列表的
                if (nx, ny) in closed_set:
                    continue
                    
                # 检查是否可行走
                if not self.is_walkable(nx, ny):
                    continue
                    
                # 对角线移动时检查角落
                if abs(dx) == 1 and abs(dy) == 1:
                    if not self.is_walkable(current.x + dx, current.y) or \
                       not self.is_walkable(current.x, current.y + dy):
                        continue
                        
                # 计算代价
                move_cost = 1.414 if abs(dx) == 1 and abs(dy) == 1 else 1.0
                new_g = current.g + move_cost
                
                # 检查是否已在开放列表
                neighbor = open_dict.get((nx, ny))
                if neighbor is None:
                    neighbor = Node(nx, ny)
                    neighbor.g = new_g
                    neighbor.h = self.heuristic(nx, ny, end.x, end.y)
                    neighbor.parent = current
                    heapq.heappush(open_set, neighbor)
                    open_dict[(nx, ny)] = neighbor
                elif new_g < neighbor.g:
                    neighbor.g = new_g
                    neighbor.parent = current
                    # 重新排序堆
                    heapq.heapify(open_set)
                    
        return []  # 无路径
        
    def _find_nearest_walkable(self, x: int, y: int) -> Optional[Node]:
        """找到最近的可行走点"""
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = x + dx, y + dy
                    if self.is_walkable(nx, ny):
                        return Node(nx, ny)
        return None
        
    def _reconstruct_path(self, end_node: Node) -> List[Tuple[int, int]]:
        """重建路径"""
        path = []
        current: Optional[Node] = end_node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        return list(reversed(path))


class SmoothMovement:
    """平滑移动系统 - Bezier曲线插值"""
    
    def __init__(self, speed: float = 3.0):
        self.speed = speed
        self.path: List[Tuple[float, float]] = []
        self.current_index = 0
        self.progress = 0.0
        self.target_pos = pygame.math.Vector2(0, 0)
        self.current_pos = pygame.math.Vector2(0, 0)
        self.is_moving = False
        
    def set_path(self, path: List[Tuple[int, int]], start_pos: Tuple[float, float]):
        """设置路径并平滑化"""
        if len(path) < 2:
            self.path = []
            self.is_moving = False
            return
            
        # 将整数路径点转换为浮点，并添加贝塞尔曲线平滑
        self.path = self._smooth_path(path, start_pos)
        self.current_index = 0
        self.progress = 0.0
        self.current_pos = pygame.math.Vector2(start_pos)
        self.is_moving = len(self.path) >= 2
        
    def _smooth_path(self, path: List[Tuple[int, int]], 
                    start_pos: Tuple[float, float]) -> List[Tuple[float, float]]:
        """使用Catmull-Rom样条平滑路径"""
        if len(path) <= 2:
            return [start_pos] + [(float(p[0]), float(p[1])) for p in path[1:]]
            
        smoothed = [start_pos]
        
        # 在每对点之间插值
        for i in range(len(path) - 1):
            p0 = pygame.math.Vector2(path[i] if i == 0 else path[i-1])
            p1 = pygame.math.Vector2(path[i])
            p2 = pygame.math.Vector2(path[i+1])
            p3 = pygame.math.Vector2(path[i+2] if i+2 < len(path) else path[i+1])
            
            # Catmull-Rom插值
            for t in [0.25, 0.5, 0.75]:
                point = self._catmull_rom(p0, p1, p2, p3, t)
                smoothed.append((point.x, point.y))
                
        smoothed.append((float(path[-1][0]), float(path[-1][1])))
        return smoothed
        
    def _catmull_rom(self, p0: pygame.math.Vector2, p1: pygame.math.Vector2,
                    p2: pygame.math.Vector2, p3: pygame.math.Vector2, 
                    t: float) -> pygame.math.Vector2:
        """Catmull-Rom样条插值"""
        t2 = t * t
        t3 = t2 * t
        
        return 0.5 * (
            (2 * p1) +
            (-p0 + p2) * t +
            (2*p0 - 5*p1 + 4*p2 - p3) * t2 +
            (-p0 + 3*p1 - 3*p2 + p3) * t3
        )
        
    def update(self, dt: float) -> Tuple[float, float]:
        """更新移动，返回新位置"""
        if not self.is_moving or not self.path:
            return (self.current_pos.x, self.current_pos.y)
            
        # 移动到下一个路径点
        if self.current_index < len(self.path) - 1:
            target = pygame.math.Vector2(self.path[self.current_index + 1])
            direction = target - self.current_pos
            distance = direction.length()
            
            if distance > 0.1:
                direction = direction.normalize()
                move_distance = self.speed * dt
                
                if move_distance >= distance:
                    self.current_pos = target
                    self.current_index += 1
                else:
                    self.current_pos += direction * move_distance
            else:
                self.current_index += 1
        else:
            self.is_moving = False
            
        return (self.current_pos.x, self.current_pos.y)
        
    def get_direction(self) -> Tuple[float, float]:
        """获取当前移动方向"""
        if not self.is_moving or self.current_index >= len(self.path) - 1:
            return (0, 0)
            
        target = pygame.math.Vector2(self.path[self.current_index + 1])
        direction = target - self.current_pos
        
        if direction.length() > 0:
            direction = direction.normalize()
            return (direction.x, direction.y)
        return (0, 0)
