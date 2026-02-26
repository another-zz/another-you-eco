"""
Control Manager - 玩家控制管理器（v0.9.1修复版）
接管控制 + 自动切回 + 流畅切换
"""

import pygame
import time
from typing import Optional, Dict, Tuple

class ControlManager:
    """玩家控制管理器"""
    
    def __init__(self, auto_switch_time: float = 30.0):
        self.player_mode = False
        self.auto_switch_time = auto_switch_time  # 30秒无操作自动切回
        self.last_input_time = 0
        self.player_agent = None
        self.camera = None
        
    def set_player_agent(self, agent):
        """设置玩家控制的AI"""
        self.player_agent = agent
        
    def set_camera(self, camera):
        """设置相机"""
        self.camera = camera
        
    def toggle_player_mode(self) -> bool:
        """切换玩家模式"""
        self.player_mode = not self.player_mode
        self.last_input_time = time.time()
        
        if self.player_mode and self.player_agent and self.camera:
            # 平滑切换到玩家视角
            self.camera.set_target(self.player_agent)
            
        return self.player_mode
        
    def enter_player_mode(self):
        """进入玩家模式"""
        if not self.player_mode:
            self.player_mode = True
            self.last_input_time = time.time()
            if self.player_agent and self.camera:
                self.camera.set_target(self.player_agent)
                
    def exit_player_mode(self):
        """退出玩家模式"""
        self.player_mode = False
        
    def handle_input(self, keys: Dict, events: list) -> Tuple[bool, Dict]:
        """
        处理输入
        返回: (是否玩家控制, 移动输入)
        """
        current_time = time.time()
        
        # 检查Esc退出玩家模式
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.player_mode:
                    self.exit_player_mode()
                    return False, {}
                    
        # 检查是否有输入
        has_input = False
        move_keys = {
            'up': keys.get(pygame.K_w) or keys.get(pygame.K_UP),
            'down': keys.get(pygame.K_s) or keys.get(pygame.K_DOWN),
            'left': keys.get(pygame.K_a) or keys.get(pygame.K_LEFT),
            'right': keys.get(pygame.K_d) or keys.get(pygame.K_RIGHT),
        }
        
        if any(move_keys.values()):
            has_input = True
            self.last_input_time = current_time
            
        # 自动切回AI模式
        if self.player_mode:
            idle_time = current_time - self.last_input_time
            if idle_time > self.auto_switch_time:
                print(f"⏰ {self.auto_switch_time}秒无操作，自动切回AI模式")
                self.exit_player_mode()
                return False, {}
                
        return self.player_mode, move_keys
        
    def handle_mouse_click(self, mouse_pos: Tuple[int, int], agents: list, camera) -> Optional[object]:
        """
        处理鼠标点击
        返回: 被点击的AI（如果有）
        """
        mx, my = mouse_pos
        
        for agent in agents:
            sx, sy = camera.world_to_screen(agent.x, agent.y)
            # 点击检测范围
            if abs(mx - sx) < 20 and abs(my - sy) < 20:
                return agent
                
        return None
