"""
Admin Panel - 管理员上帝视角面板
只有项目拥有者能使用
"""

import pygame
from typing import Dict, List, Tuple, Optional
from core.living_world import LivingWorld, LivingAgent, AdminMode, Camera

class AdminPanel:
    """管理员面板 - 上帝视角"""
    
    def __init__(self, world: LivingWorld, camera: Camera):
        self.world = world
        self.camera = camera
        
        # 字体
        self.font = pygame.font.SysFont('microsoftyahei', 12)
        self.font_bold = pygame.font.SysFont('microsoftyahei', 12, bold=True)
        self.font_large = pygame.font.SysFont('microsoftyahei', 16, bold=True)
        
        # 面板状态
        self.visible = False
        self.selected_agent: Optional[LivingAgent] = None
        self.show_relationships = True
        self.show_terrain_info = True
        self.show_event_log = True
        
        # 事件日志
        self.event_log: List[str] = []
        self.max_log_lines = 20
        
    def toggle(self):
        """切换显示"""
        self.visible = not self.visible
        
    def add_log(self, message: str):
        """添加日志"""
        timestamp = f"[{self.world.time}]"
        self.event_log.append(f"{timestamp} {message}")
        if len(self.event_log) > self.max_log_lines:
            self.event_log.pop(0)
            
    def handle_click(self, screen_x: int, screen_y: int, screen_width: int, screen_height: int):
        """处理点击 - 选择AI"""
        if not self.visible or self.camera.mode != AdminMode.GOD:
            return
            
        # 转换到世界坐标
        world_x, world_y = self.camera.screen_to_world(screen_x, screen_y, screen_width, screen_height)
        
        # 查找点击位置的AI
        for agent in self.world.agents.values():
            if abs(agent.x - world_x) <= 1 and abs(agent.y - world_y) <= 1:
                self.selected_agent = agent
                return
                
        # 点击空白处，显示地形信息
        self.selected_agent = None
        
    def render(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """渲染面板"""
        if not self.visible:
            return
            
        # 左侧面板 - 世界信息
        self._render_world_panel(screen, 10, 50)
        
        # 右侧面板 - 选中AI详情或地形信息
        if self.selected_agent:
            self._render_agent_detail(screen, screen_width - 310, 50, self.selected_agent)
        else:
            self._render_terrain_info(screen, screen_width - 310, 50)
            
        # 底部面板 - 事件日志
        if self.show_event_log:
            self._render_event_log(screen, 10, screen_height - 200)
            
    def _render_world_panel(self, screen: pygame.Surface, x: int, y: int):
        """渲染世界信息面板"""
        width = 280
        height = 200
        
        # 背景
        pygame.draw.rect(screen, (30, 30, 30, 230), (x, y, width, height))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height), 2)
        
        # 标题
        title = self.font_large.render("🌍 世界状态", True, (255, 215, 0))
        screen.blit(title, (x + 10, y + 10))
        
        line_y = y + 35
        
        # 时间
        time_text = self.font.render(f"⏰ {self.world.time}", True, (255, 255, 255))
        screen.blit(time_text, (x + 10, line_y))
        line_y += 20
        
        # 天气
        weather_text = self.font.render(f"{self.world.weather}", True, (200, 200, 255))
        screen.blit(weather_text, (x + 10, line_y))
        line_y += 20
        
        # 统计
        alive_count = len([a for a in self.world.agents.values() if a.alive])
        stats = [
            f"👥 AI: {alive_count}/{len(self.world.agents)}",
            f"🏠 建筑: {len(self.world.buildings)}",
            f"🌟 活跃事件: {len(self.world.events.active_events)}",
            f"📜 历史事件: {len(self.world.events.event_history)}",
        ]
        
        for stat in stats:
            text = self.font.render(stat, True, (200, 200, 200))
            screen.blit(text, (x + 10, line_y))
            line_y += 18
            
    def _render_agent_detail(self, screen: pygame.Surface, x: int, y: int, agent: LivingAgent):
        """渲染AI详情"""
        width = 300
        height = 500
        
        # 背景
        pygame.draw.rect(screen, (30, 30, 40, 240), (x, y, width, height))
        pygame.draw.rect(screen, (100, 100, 150), (x, y, width, height), 2)
        
        # 标题
        title = self.font_large.render(f"🤖 {agent.name}", True, (100, 200, 255))
        screen.blit(title, (x + 10, y + 10))
        
        line_y = y + 35
        
        # 基础状态
        status_color = (0, 255, 0) if agent.alive else (255, 0, 0)
        status = "存活" if agent.alive else "死亡"
        text = self.font.render(f"状态: {status}", True, status_color)
        screen.blit(text, (x + 10, line_y))
        line_y += 22
        
        if not agent.alive:
            return
            
        # 属性条
        bars = [
            ("能量", agent.energy, agent.max_energy, (255, 100, 100)),
            ("健康", agent.health, 100, (100, 255, 100)),
            ("心情", agent.mood, 100, (255, 200, 100)),
        ]
        
        for name, current, max_val, color in bars:
            # 标签
            label = self.font.render(f"{name}:", True, (200, 200, 200))
            screen.blit(label, (x + 10, line_y))
            
            # 条
            bar_width = 150
            bar_height = 12
            fill_width = int(bar_width * current / max_val)
            
            pygame.draw.rect(screen, (50, 50, 50), (x + 60, line_y, bar_width, bar_height))
            pygame.draw.rect(screen, color, (x + 60, line_y, fill_width, bar_height))
            
            # 数值
            value_text = self.font.render(f"{current:.0f}", True, (255, 255, 255))
            screen.blit(value_text, (x + 60 + bar_width + 5, line_y))
            
            line_y += 20
            
        line_y += 10
        
        # 位置和行动
        info = [
            f"📍 位置: ({agent.x}, {agent.y})",
            f"🎯 当前: {agent.current_action}",
            f"🏠 家: {agent.home if agent.home else '无'}",
        ]
        
        for item in info:
            text = self.font.render(item, True, (220, 220, 220))
            screen.blit(text, (x + 10, line_y))
            line_y += 18
            
        line_y += 10
        
        # 库存
        text = self.font_bold.render("📦 库存:", True, (255, 215, 0))
        screen.blit(text, (x + 10, line_y))
        line_y += 20
        
        for item, amount in list(agent.inventory.items())[:5]:
            text = self.font.render(f"  {item}: {amount:.1f}", True, (200, 200, 200))
            screen.blit(text, (x + 10, line_y))
            line_y += 16
            
        line_y += 10
        
        # 关系
        if self.show_relationships and agent.relationships:
            text = self.font_bold.render("👥 关系:", True, (255, 215, 0))
            screen.blit(text, (x + 10, line_y))
            line_y += 20
            
            for target_id, rel in list(agent.relationships.items())[:3]:
                status = rel.get_status()
                color = (100, 255, 100) if rel.friendship > 20 else (255, 100, 100) if rel.friendship < -20 else (200, 200, 200)
                text = self.font.render(f"  {target_id[:8]}: {status}", True, color)
                screen.blit(text, (x + 10, line_y))
                line_y += 16
                
        line_y += 10
        
        # 最近记忆
        text = self.font_bold.render("🧠 最近记忆:", True, (255, 215, 0))
        screen.blit(text, (x + 10, line_y))
        line_y += 20
        
        for memory in agent.memory.memories[-3:]:
            content = memory.content[:30] + "..." if len(memory.content) > 30 else memory.content
            text = self.font.render(f"  • {content}", True, (180, 180, 200))
            screen.blit(text, (x + 10, line_y))
            line_y += 16
            
    def _render_terrain_info(self, screen: pygame.Surface, x: int, y: int):
        """渲染地形信息"""
        width = 300
        height = 200
        
        pygame.draw.rect(screen, (30, 40, 30, 240), (x, y, width, height))
        pygame.draw.rect(screen, (100, 150, 100), (x, y, width, height), 2)
        
        title = self.font_large.render("🌿 地形信息", True, (100, 255, 150))
        screen.blit(title, (x + 10, y + 10))
        
        # 获取鼠标位置的地形
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # 这里需要知道屏幕尺寸来转换，简化显示提示
        
        hint = self.font.render("点击地图查看详情", True, (150, 150, 150))
        screen.blit(hint, (x + 10, y + 40))
        
    def _render_event_log(self, screen: pygame.Surface, x: int, y: int):
        """渲染事件日志"""
        width = 600
        height = 180
        
        pygame.draw.rect(screen, (20, 20, 25, 240), (x, y, width, height))
        pygame.draw.rect(screen, (80, 80, 100), (x, y, width, height), 2)
        
        title = self.font_bold.render("📜 事件日志", True, (200, 200, 255))
        screen.blit(title, (x + 10, y + 5))
        
        line_y = y + 25
        for log in self.event_log[-8:]:
            text = self.font.render(log, True, (180, 180, 180))
            screen.blit(text, (x + 10, line_y))
            line_y += 18
