"""
AnotherYou ECO v0.9 - 高质量像素版
基于v0.7稳定版本 + 无限世界 + 碰撞规则 + 清晰气泡
"""

import pygame
import asyncio
import random
import math
from typing import List, Dict

import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.sprite_loader import SpriteSheet, CharacterSprite
from core.quality_tileset import QualityTileset, TILE_SIZE
from core.camera import GameCamera
from core.animation import AnimationManager, EnvironmentEffects
from core.chunk_manager import ChunkManager, CHUNK_SIZE
from core.collision_pathfinder import CollisionPathfinder
from core.agent_survival import SurvivalSystem
from core.pathfinder import SmoothMovement
from core.event_manager import EventManager, Season
from core.control_manager import ControlManager
from ui.modern_hud import ModernHUD
from ui.thought_bubble import ThoughtBubble

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60


class GameAgent:
    """游戏AI角色（v0.9高质量版）"""
    
    SHIRT_COLORS = [
        (220, 80, 80), (80, 120, 220), (80, 180, 80),
        (220, 180, 60), (180, 100, 200), (255, 140, 80),
    ]
    
    def __init__(self, agent_id: str, name: str, x: float, y: float, color_idx: int):
        self.id = agent_id
        self.name = name
        self.x = x
        self.y = y
        
        # 系统
        self.survival = SurvivalSystem()
        self.movement = SmoothMovement(speed=2.5)
        self.thought_bubble = ThoughtBubble()
        
        # 内心独白
        self.thought_text = ""
        self.thought_timer = 0
        self.thoughts_pool = [
            "今天天气真好！", "有点饿了...", "想去探索新地方",
            "好累啊，想休息", "这里风景真美", "继续前进吧",
            "感觉充满活力！", "想找个地方坐下"
        ]
        
        # 视觉
        self.sprite = self._create_sprite(color_idx)
        self.is_player = False
        
        # 路径寻找
        self.pathfinder = None
        
    def set_pathfinder(self, pathfinder):
        self.pathfinder = pathfinder
        
    def _create_sprite(self, color_idx: int):
        """创建高质量角色精灵（32x32带行走动画）"""
        color = self.SHIRT_COLORS[color_idx % len(self.SHIRT_COLORS)]
        sheet = pygame.Surface((128, 128), pygame.SRCALPHA)
        
        # 4方向 x 4帧 = 16个精灵
        for direction in range(4):
            for frame in range(4):
                x = frame * 32
                y = direction * 32
                
                # 身体（衣服）
                pygame.draw.rect(sheet, color, (x + 10, y + 12, 12, 14))
                
                # 头
                pygame.draw.circle(sheet, (255, 220, 180), (x + 16, y + 8), 5)
                
                # 腿（行走动画）
                leg_offset = (frame % 2) * 4
                pygame.draw.rect(sheet, (60, 40, 30), (x + 10 + leg_offset, y + 26, 4, 6))
                pygame.draw.rect(sheet, (60, 40, 30), (x + 18 - leg_offset, y + 26, 4, 6))
                
                # 手臂
                arm_offset = (frame % 2) * 2
                pygame.draw.rect(sheet, color, (x + 6, y + 14 + arm_offset, 4, 8))
                pygame.draw.rect(sheet, color, (x + 22, y + 14 - arm_offset, 4, 8))
                
        return CharacterSprite(SpriteSheet.from_surface(sheet, 32, 32), None)
        
    def update(self, dt: float, chunk_manager, animation, hour: int,
               is_player_control: bool, input_keys: Dict):
        """更新AI"""
        # 更新生存
        weather = {}
        self.survival.update(dt, weather, hour)
        
        # 内心独白
        self.thought_timer += dt
        if self.thought_timer > 6:  # 每6秒更新想法
            self.thought_timer = 0
            self.thought_text = random.choice(self.thoughts_pool)
            
        self.thought_bubble.update(dt, self.thought_text)
        self.thought_bubble.set_visible(not is_player_control and self.thought_text)
        
        if self.survival.is_dead:
            return
            
        # 玩家控制
        if is_player_control:
            self._player_control(dt, chunk_manager, animation, input_keys)
            return
            
        # AI控制
        self._ai_control(dt, chunk_manager, animation, hour)
        
    def _player_control(self, dt, chunk_manager, animation, keys):
        """玩家控制（遵守碰撞）"""
        move_speed = 4 * dt
        dx = dy = 0
        
        if keys.get('up'): dy = -move_speed
        if keys.get('down'): dy = move_speed
        if keys.get('left'): dx = -move_speed
        if keys.get('right'): dx = move_speed
            
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            
            # 检查碰撞
            if chunk_manager.is_walkable(new_x, new_y):
                self.x = new_x
                self.y = new_y
                self.sprite.update(dt, dx*10, dy*10)
                if random.random() < 0.3:
                    animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
            else:
                # 碰到障碍物停止动画
                self.sprite.update(dt, 0, 0)
        else:
            self.sprite.update(dt, 0, 0)
                    
    def _ai_control(self, dt, chunk_manager, animation, hour):
        """AI控制（智能避障）"""
        priority = self.survival.get_priority()
        
        if priority == 'critical':
            if self.survival.should_sleep(hour):
                self.survival.is_sleeping = True
                return
        elif priority == 'wake_up':
            self.survival.is_sleeping = False
            
        if self.survival.is_sleeping:
            self.sprite.update(dt, 0, 0)
            return
            
        # 智能移动
        if self.movement.is_moving:
            new_x, new_y = self.movement.update(dt)
            
            if chunk_manager.is_walkable(new_x, new_y):
                dx = new_x - self.x
                dy = new_y - self.y
                self.x = new_x
                self.y = new_y
                self.sprite.update(dt, dx*10, dy*10)
                
                if self.movement.is_moving and random.random() < 0.2:
                    animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
            else:
                self.movement.is_moving = False
        else:
            # 重新寻路（使用碰撞感知路径）
            if self.pathfinder and random.random() < 0.02:
                for _ in range(5):
                    target_x = self.x + random.randint(-25, 25)
                    target_y = self.y + random.randint(-25, 25)
                    
                    if chunk_manager.is_walkable(target_x, target_y):
                        path = self.pathfinder.find_path(self.x, self.y, target_x, target_y)
                        if path and len(path) > 1:
                            self.movement.set_path(path, (self.x, self.y))
                            break
                            
    def render(self, screen, camera):
        """渲染AI"""
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        if -50 < sx < screen.get_width() + 50 and -50 < sy < screen.get_height() + 50:
            # 玩家高亮
            if self.is_player:
                pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
                radius = 24 + int(pulse * 4)
                pygame.draw.circle(screen, (255, 215, 0), (sx, sy), radius, 3)
                
            # 内心独白气泡
            self.thought_bubble.render(screen, sx, sy)
            
            # 昵称（带描边）
            font = pygame.font.SysFont('microsoftyahei', 12, bold=True)
            name_text = font.render(self.name, True, (255, 255, 255))
            name_x = sx - name_text.get_width() // 2
            
            # 描边
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                outline = font.render(self.name, True, (0, 0, 0))
                screen.blit(outline, (name_x + dx, sy - 32 + dy))
            screen.blit(name_text, (name_x, sy - 32))
            
            # 精灵（高质量32x32）
            if not self.survival.is_dead:
                self.sprite.render(screen, sx, sy, scale=1.5)
                
            # 能量条
            bar_w = 32
            bar_h = 4
            bar_x = sx - bar_w // 2
            bar_y = sy + 20
            
            pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
            
            energy = self.survival.energy
            fill_w = int(bar_w * max(0, min(1, energy / 100)))
            if fill_w > 0:
                if energy > 60:
                    color = (100, 255, 100)
                elif energy > 30:
                    color = (255, 220, 80)
                else:
                    color = (255, 80, 80)
                pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.9 - 高质量像素版")
        self.clock = pygame.time.Clock()
        
        # 高质量瓦片集
        self.tileset = QualityTileset()
        
        # 无限世界
        self.chunk_manager = ChunkManager(seed=42)
        
        # 碰撞感知路径寻找
        self.pathfinder = CollisionPathfinder(self.chunk_manager)
        
        # AI们
        self.agents: List[GameAgent] = []
        for i in range(15):
            agent = GameAgent(f"agent_{i}", f"AI-{i}", 50.0, 50.0, i)
            agent.set_pathfinder(self.pathfinder)
            self.agents.append(agent)
            
        # 玩家
        self.player_agent = self.agents[0]
        self.player_agent.is_player = True
        
        # 控制管理器（v0.9.1修复）
        self.control_manager = ControlManager(auto_switch_time=30.0)
        self.control_manager.set_player_agent(self.player_agent)
        
        # 系统
        self.camera = GameCamera(1000, 1000, TILE_SIZE)
        self.camera.set_target(self.player_agent)
        self.control_manager.set_camera(self.camera)
        self.animation = AnimationManager()
        self.hud = ModernHUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 时间
        self.game_time = 12.0
        self.day = 1
        self.season = Season.SPRING
        
        # 状态
        self.paused = False
        self.speed = 1
        self.running = True
        
        print("🎮 AnotherYou ECO v0.9 - 高质量像素版")
        print("=" * 50)
        print("✨ 特性:")
        print("  • 高质量32x32像素瓦片（草叶、树叶、岩石纹理）")
        print("  • 无限世界（chunk动态加载）")
        print("  • AI遵守碰撞规则（绕树、不站水）")
        print("  • 清晰内心独白气泡")
        print("  • 接管控制修复（空格/点击接管，Esc切回，30秒自动）")
        print("=" * 50)
        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        events = list(pygame.event.get())
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # 空格键切换控制
                    is_player = self.control_manager.toggle_player_mode()
                    print(f"🎮 {'玩家' if is_player else 'AI'}控制")
                elif event.key == pygame.K_F12:
                    self.camera.toggle_god_mode()
                    print(f"👁️ 上帝模式: {'开启' if self.camera.god_mode else '关闭'}")
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击AI
                    clicked_agent = self.control_manager.handle_mouse_click(
                        event.pos, self.agents, self.camera
                    )
                    if clicked_agent:
                        self.player_agent = clicked_agent
                        self.control_manager.set_player_agent(clicked_agent)
                        self.camera.set_target(clicked_agent)
                        self.control_manager.enter_player_mode()
                        print(f"🎮 接管控制: {clicked_agent.name}")
                elif event.button == 4:  # 滚轮上
                    self.camera.zoom_in()
                elif event.button == 5:  # 滚轮下
                    self.camera.zoom_out()
                    
        # 处理控制输入（v0.9.1修复）
        is_player, move_keys = self.control_manager.handle_input(keys, events)
        
        # 上帝模式相机移动
        if self.camera.god_mode:
            speed = 15
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.camera.move(0, -speed)
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.camera.move(0, speed)
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera.move(-speed, 0)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera.move(speed, 0)
                
        return is_player, move_keys
        
    def render_world(self, screen):
        """渲染世界（chunk系统 + 高质量瓦片）"""
        # 更新加载的区块
        self.chunk_manager.update_loaded_chunks(self.camera.x / TILE_SIZE, 
                                                self.camera.y / TILE_SIZE)
        
        # 获取需要渲染的区块
        chunks = self.chunk_manager.get_render_chunks(
            self.camera.x, self.camera.y, screen.get_width(), screen.get_height()
        )
        
        # 渲染每个区块
        for chunk in chunks:
            chunk_pixel_x = chunk.cx * CHUNK_SIZE * TILE_SIZE - int(self.camera.x)
            chunk_pixel_y = chunk.cy * CHUNK_SIZE * TILE_SIZE - int(self.camera.y)
            
            for y, row in enumerate(chunk.tiles):
                for x, (tile_type, variant) in enumerate(row):
                    pixel_x = chunk_pixel_x + x * TILE_SIZE
                    pixel_y = chunk_pixel_y + y * TILE_SIZE
                    
                    # 只渲染屏幕内的瓦片
                    if -TILE_SIZE < pixel_x < screen.get_width() + TILE_SIZE and \
                       -TILE_SIZE < pixel_y < screen.get_height() + TILE_SIZE:
                        
                        tile_image = self.tileset.get_tile(tile_type, variant)
                        screen.blit(tile_image, (pixel_x, pixel_y))
                            
    def update(self, dt: float, is_player: bool, input_keys: Dict):
        if self.paused:
            return
            
        # 时间
        self.game_time += dt * self.speed / 60
        if self.game_time >= 24:
            self.game_time = 0
            self.day += 1
        hour = int(self.game_time)
        
        # 更新系统
        self.camera.update(self.screen.get_width(), self.screen.get_height())
        self.animation.update(dt)
        self.hud.update(dt)
        
        # 更新AI
        for agent in self.agents:
            is_this_player = (agent == self.player_agent and is_player)
            agent.update(dt * self.speed, self.chunk_manager, self.animation,
                        hour, is_this_player, input_keys)
            
    def render(self):
        self.screen.fill((20, 25, 20))
        
        # 渲染世界（高质量chunk）
        self.render_world(self.screen)
        
        # 渲染AI
        for agent in self.agents:
            agent.render(self.screen, self.camera)
            
        # 粒子
        self.animation.render(self.screen, self.camera.x, self.camera.y, TILE_SIZE)
        
        # 日夜
        EnvironmentEffects.render_day_night_overlay(self.screen, int(self.game_time), 0)
        
        # HUD
        game_state = {
            'player': {
                'name': self.player_agent.name,
                'status': '🎮 玩家控制' if self.control_manager.player_mode else '🤖 AI自主',
                'energy': self.player_agent.survival.energy,
                'mood': 70,
                'money': 100,
                'goal': '探索无限世界',
            },
            'year': 1,
            'season': self.season.value.title(),
            'day': self.day,
            'hour': int(self.game_time),
            'minute': int((self.game_time % 1) * 60),
            'weather': 'Sunny',
            'speed': self.speed,
            'paused': self.paused,
            'controls': 'WASD:移动 | 空格:切换 | 点击AI:接管 | 滚轮:缩放 | Esc:切回AI',
            'god_mode': self.camera.god_mode,
            'player_pos': (self.player_agent.x, self.player_agent.y),
            'world_width': 1000,
            'world_height': 1000,
        }
        
        self.hud.render(self.screen, game_state)
        pygame.display.flip()
        
    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            is_player, input_keys = self.handle_input()
            self.update(dt, is_player, input_keys)
            self.render()
            await asyncio.sleep(0)
            
        pygame.quit()


# 扩展SpriteSheet
@classmethod
def from_surface(cls, surface, tile_width, tile_height):
    sheet = cls.__new__(cls)
    sheet.sheet = surface
    sheet.tile_width = tile_width
    sheet.tile_height = tile_height
    sheet.cols = surface.get_width() // tile_width
    sheet.rows = surface.get_height() // tile_height
    return sheet

SpriteSheet.from_surface = from_surface


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
