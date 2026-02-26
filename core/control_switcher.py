"""
Control Switcher - 控制切换系统
AI_MODE / PLAYER_MODE 状态机
"""

import pygame
from typing import List, Optional
from enum import Enum, auto

class ControlMode(Enum):
    """控制模式"""
    AI_MODE = auto()      # AI完全自主
    PLAYER_MODE = auto()  # 玩家控制
    TRANSITION = auto()   # 过渡状态

class ControlSwitcher:
    """控制切换器"""
    
    def __init__(self, agent_core):
        self.agent = agent_core
        self.mode = ControlMode.AI_MODE
        
        # 玩家控制状态
        self.player_actions: List[str] = []
        self.last_input_time = 0
        self.idle_threshold = 30.0  # 30秒无操作自动切回AI
        
        # 切换冷却
        self.switch_cooldown = 0
        
    def can_switch(self) -> bool:
        """检查是否可以切换"""
        return self.switch_cooldown <= 0
        
    def switch_to_player(self) -> bool:
        """切换到玩家控制"""
        if not self.can_switch():
            return False
            
        if self.mode == ControlMode.AI_MODE:
            self.mode = ControlMode.PLAYER_MODE
            self.player_actions = []
            self.agent.on_player_takeover()
            self.switch_cooldown = 1.0  # 1秒冷却
            print(f"🎮 {self.agent.name} - 玩家接管控制")
            return True
        return False
        
    def switch_to_ai(self) -> bool:
        """切换到AI控制"""
        if not self.can_switch():
            return False
            
        if self.mode == ControlMode.PLAYER_MODE:
            self.mode = ControlMode.AI_MODE
            self.agent.on_player_release(self.player_actions)
            self.player_actions = []
            self.switch_cooldown = 1.0
            print(f"🤖 {self.agent.name} - AI接管控制")
            return True
        return False
        
    def update(self, dt: float, keys: dict, mouse_buttons: dict, mouse_pos: tuple):
        """更新控制状态"""
        self.switch_cooldown -= dt
        
        if self.mode == ControlMode.PLAYER_MODE:
            # 检查输入
            has_input = any(keys.values()) or any(mouse_buttons.values())
            
            if has_input:
                self.last_input_time = 0
                # 记录玩家行动
                if keys.get(pygame.K_w) or keys.get(pygame.K_UP):
                    self.player_actions.append("向北移动")
                if keys.get(pygame.K_s) or keys.get(pygame.K_DOWN):
                    self.player_actions.append("向南移动")
                if keys.get(pygame.K_a) or keys.get(pygame.K_LEFT):
                    self.player_actions.append("向西移动")
                if keys.get(pygame.K_d) or keys.get(pygame.K_RIGHT):
                    self.player_actions.append("向东移动")
                if keys.get(pygame.K_e):
                    self.player_actions.append("交互")
                    
                # 限制记录数量
                if len(self.player_actions) > 10:
                    self.player_actions.pop(0)
            else:
                self.last_input_time += dt
                
            # 长时间无操作，自动切回AI
            if self.last_input_time > self.idle_threshold:
                self.switch_to_ai()
                
    def handle_input(self, event: pygame.event.Event) -> bool:
        """处理输入事件，返回是否消耗了事件"""
        if self.mode != ControlMode.PLAYER_MODE:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to_ai()
                return True
            elif event.key == pygame.K_SPACE:
                self.switch_to_ai()
                return True
                
        return False
        
    def get_mode_display(self) -> str:
        """获取模式显示文本"""
        if self.mode == ControlMode.AI_MODE:
            return "🤖 AI自主"
        elif self.mode == ControlMode.PLAYER_MODE:
            return "🎮 玩家控制"
        return "..."
        
    def is_player_control(self) -> bool:
        """是否玩家控制中"""
        return self.mode == ControlMode.PLAYER_MODE
