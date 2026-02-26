"""
Collision Pathfinder - 碰撞感知A*寻路
绕树、避水、遵守世界规则
"""

import heapq
from typing import List, Tuple, Optional, Dict

class CollisionPathfinder:
    """碰撞感知路径寻找器"""
    
    def __init__(self, chunk_manager):
        self.chunk_manager = chunk_manager
        
    def find_path(self, start_x: float, start_y: float, 
                  end_x: float, end_y: float, max_distance: int = 50) -> List[Tuple[int, int]]:
        """A*寻路，避开障碍和水域"""
        start = (int(start_x), int(start_y))
        end = (int(end_x), int(end_y))
        
        # 如果目标不可行走，找附近可行走点
        if not self._is_walkable(end[0], end[1]):
            end = self._find_nearby_walkable(end[0], end[1])
            if end is None:
                return []
                
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == end:
                return self._reconstruct_path(came_from, current)
                
            if g_score[current] > max_distance:
                continue
                
            # 8方向邻居
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # 检查是否可行走
                if not self._is_walkable(neighbor[0], neighbor[1]):
                    continue
                    
                # 对角线移动检查
                if abs(dx) == 1 and abs(dy) == 1:
                    if not self._is_walkable(current[0] + dx, current[1]) or \
                       not self._is_walkable(current[0], current[1] + dy):
                        continue
                        
                # 移动代价
                move_cost = 1.414 if abs(dx) == abs(dy) else 1.0
                
                # 水域附近增加代价（AI倾向于远离水）
                if self._is_near_water(neighbor[0], neighbor[1]):
                    move_cost += 0.5
                    
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, neighbor))
                    
        return []
        
    def _is_walkable(self, x: int, y: int) -> bool:
        return self.chunk_manager.is_walkable(x, y)
        
    def _is_near_water(self, x: int, y: int, radius: int = 2) -> bool:
        """检查是否靠近水"""
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if self.chunk_manager.is_water(x + dx, y + dy):
                    return True
        return False
        
    def _find_nearby_walkable(self, x: int, y: int, radius: int = 5) -> Optional[Tuple[int, int]]:
        """找附近可行走的点"""
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx, ny = x + dx, y + dy
                    if self._is_walkable(nx, ny):
                        return (nx, ny)
        return None
        
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """启发函数（切比雪夫距离）"""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + 0.414 * min(dx, dy)
        
    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))
