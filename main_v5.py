"""
Main Game v0.5 - 真正的游戏版本
清晰、专业、有操作感
"""

import pygame
import asyncio
import random
from typing import Dict, List

import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.tilemap import Tilemap, TileType
from core.sprites import AgentSprite, Direction
from core.camera import GameCamera
from ui.hud import HUD

# 配置
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60
TILE_SIZE = 32

# 颜色
COLORS = {
    'bg': (20, 25, 20),
}


class Agent:
    """游戏AI角色"""
    
    def __init__(self, agent_id: str, name: str, x: int, y: int, color_idx: int):
        self.id = agent_id
        self.name = name
        self.x = float(x)
        self.y = float(y)
        
        # 状态
        self.energy = 100.0
        self.mood = 50.0
        self.money = 0
        self.alive = True
        
        # 精灵
        self.sprite = AgentSprite(agent_id, name, color_idx)
        
        # 当前目标
        self.goal = "探索世界"
        self.action_timer = 0
        
    def update(self, dt: float):
        """更新AI"""
        if not self.alive:
            return
            
        # 能量消耗
        self.energy -= 0.05 * dt
        if self.energy <= 0:
            self.energy = 0
            self.alive = False
            
        # 随机移动（自主行动）
        self.action_timer += dt
        if self.action_timer > 2.0:  # 每2秒决策一次
            self.action_timer = 0
            self._decide_action()
            
        # 更新动画
        dx = random.uniform(-0.5, 0.5) if random.random() < 0.1 else 0
        dy = random.uniform(-0.5, 0.5) if random.random() < 0.1 else 0
        
        self.x = max(0, min(99, self.x + dx * dt))
        self.y = max(0, min(99, self.y + dy * dt))
        
        self.sprite.update(dx, dy)
        
    def _decide_action(self):
        """AI自主决策"""
        actions = [
            ("寻找食物", 0.3),
            ("探索", 0.4),
            ("休息", 0.2),
            ("社交", 0.1),
        ]
        
        weights = [w for _, w in actions]
        self.goal = random.choices([a for a, _ in actions], weights=weights)[0]
        
    def render(self, screen: pygame.Surface, camera: GameCamera):
        """渲染"""
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 检查是否在屏幕内
        if -50 < sx < SCREEN_WIDTH + 50 and -50 < sy < SCREEN_HEIGHT + 50:
            self.sprite.render(screen, sx, sy, self.energy, is_player=False)


class Game:
    """主游戏类"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.5")
        self.clock = pygame.time.Clock()
        
        # 世界
        self.tilemap = Tilemap(100, 100, TILE_SIZE)
        
        # AI们
        self.agents: Dict[str, Agent] = {}
        for i in range(15):
            agent = Agent(
                f"agent_{i}",
                f"AI-{i}",
                random.randint(40, 60),
                random.randint(40, 60),
                i
            )
            self.agents[agent.id] = agent
            
        # 玩家控制的AI
        self.player_agent = list(self.agents.values())[0]
        self.player_control = False  # 是否玩家控制中
        
        # 相机
        self.camera = GameCamera(100, 100, TILE_SIZE)
        self.camera.set_target(self.player_agent)
        
        # HUD
        self.hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 状态
        self.paused = False
        self.speed = 1
        self.running = True
        
    def handle_input(self):
        """处理输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                # 上帝模式
                if event.key == pygame.K_F12:
                    is_god = self.camera.toggle_god_mode()
                    print(f"{'上帝' if is_god else '玩家'}模式")
                    
                # 暂停
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    
                # 速度
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                    
                # 玩家控制切换
                elif event.key == pygame.K_c:
                    self.player_control = not self.player_control
                    if not self.player_control:
                        print("AI接管控制")
                        # TODO: AI反思
                        
            # 鼠标滚轮缩放
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.camera.zoom_in()
                elif event.button == 5:
                    self.camera.zoom_out()
                    
        # 持续按键
        keys = pygame.key.get_pressed()
        
        if self.camera.god_mode:
            # 上帝模式：移动相机
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.camera.move(0, -1)
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.camera.move(0, 1)
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera.move(-1, 0)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera.move(1, 0)
        else:
            # 玩家模式：移动AI或相机跟随
            if self.player_control:
                speed = 3 * (1/60)  # 每帧移动
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.player_agent.y -= speed
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.player_agent.y += speed
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.player_agent.x -= speed
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.player_agent.x += speed
                    
                # 限制边界
                self.player_agent.x = max(0, min(99, self.player_agent.x))
                self.player_agent.y = max(0, min(99, self.player_agent.y))
                
                # 更新动画
                dx = 0
                dy = 0
                if keys[pygame.K_w]: dy = -1
                if keys[pygame.K_s]: dy = 1
                if keys[pygame.K_a]: dx = -1
                if keys[pygame.K_d]: dx = 1
                self.player_agent.sprite.update(dx, dy)
                
    def update(self, dt: float):
        """更新游戏"""
        if self.paused:
            return
            
        # 更新相机
        self.camera.update(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 更新AI
        for agent in self.agents.values():
            if agent != self.player_agent or not self.player_control:
                agent.update(dt * self.speed)
                
    def render(self):
        """渲染"""
        self.screen.fill(COLORS['bg'])
        
        # 渲染瓦片地图
        self.tilemap.render(self.screen, self.camera.x, self.camera.y, 
                          SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 渲染AI
        for agent in self.agents.values():
            agent.render(self.screen, self.camera)
            
        # 渲染HUD
        game_state = {
            'time': f"Year 1 Spring Day 1 12:00",
            'weather': '☀️ Sunny',
            'mode': 'GOD' if self.camera.god_mode else 'PLAYER',
            'speed': self.speed,
            'paused': self.paused,
            'controls': 'WASD:移动 | F12:上帝 | C:控制切换' if not self.camera.god_mode else 'WASD:相机 | F12:退出',
            'player': {
                'name': self.player_agent.name,
                'energy': self.player_agent.energy,
                'mood': self.player_agent.mood,
                'money': self.player_agent.money,
                'goal': self.player_agent.goal,
            },
            'god_mode': self.camera.god_mode,
            'minimap': {
                'player_pos': (self.player_agent.x, self.player_agent.y),
                'world_width': 100,
                'world_height': 100,
            }
        }
        
        self.hud.render(self.screen, game_state)
        
        pygame.display.flip()
        
    async def run(self):
        """主循环"""
        print("🎮 AnotherYou ECO v0.5")
        print("=" * 40)
        print("控制:")
        print("  WASD - 移动")
        print("  F12  - 上帝模式")
        print("  C    - 切换玩家/AI控制")
        print("  空格 - 暂停")
        print("  1/2/3 - 速度")
        print("=" * 40)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # 秒
            
            self.handle_input()
            self.update(dt)
            self.render()
            
            await asyncio.sleep(0)
            
        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
