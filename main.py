"""
AnotherYou ECO v0.7 - 完整修复版
现代UI + A*平滑移动 + 事件冷却 + 生存系统
"""

import pygame
import asyncio
import random
import math
from typing import Dict, List

import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.sprite_loader import TilesetManager, CharacterSprite, SpriteSheet
from core.camera import GameCamera
from core.animation import AnimationManager, EnvironmentEffects
from core.pathfinder import AStarPathfinder, SmoothMovement
from core.event_manager import EventManager, Season
from core.agent_survival import SurvivalSystem
from ui.modern_hud import ModernHUD

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60
TILE_SIZE = 32


class WorldMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = []
        self.tileset = TilesetManager(TILE_SIZE)
        self.obstacles = []
        self._generate()
        
    def _generate(self):
        center_x, center_y = self.width // 2, self.height // 2
        for y in range(self.height):
            row = []
            for x in range(self.width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                if dist > 40:
                    tile_type = 'mountain'
                    self.obstacles.append((x, y))
                elif abs(y - center_y) < 3:
                    tile_type = 'water'
                    self.obstacles.append((x, y))
                elif random.random() < 0.2:
                    tile_type = 'forest'
                else:
                    tile_type = 'grass'
                    
                row.append((tile_type, random.randint(0, 2)))
            self.tiles.append(row)
            
    def get_tile(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return ('grass', 0)
        
    def render(self, screen, camera, animation_time):
        start_col, end_col, start_row, end_row = camera.get_visible_range(
            screen.get_width(), screen.get_height()
        )
        
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_type, variant = self.tiles[row][col]
                x = col * TILE_SIZE - int(camera.x)
                y = row * TILE_SIZE - int(camera.y)
                
                if tile_type == 'water':
                    EnvironmentEffects.render_water_animation(
                        screen, x, y, TILE_SIZE, animation_time, (60, 110, 200)
                    )
                elif tile_type == 'forest':
                    EnvironmentEffects.render_tree_sway(
                        screen, x, y, TILE_SIZE, animation_time, (40, 100, 50)
                    )
                else:
                    tile_image = self.tileset.get_tile(tile_type, variant)
                    screen.blit(tile_image, (x, y))


class GameAgent:
    SHIRT_COLORS = [
        (220, 80, 80), (80, 120, 220), (80, 180, 80),
        (220, 180, 60), (180, 100, 200), (255, 140, 80),
    ]
    
    def __init__(self, agent_id: str, name: str, x: float, y: float, color_idx: int):
        self.id = agent_id
        self.name = name
        self.x = x
        self.y = y
        self.color_idx = color_idx
        
        # 生存系统
        self.survival = SurvivalSystem()
        
        # 移动系统
        self.pathfinder = None
        self.movement = SmoothMovement(speed=2.5)
        self.path_recalc_timer = 0
        
        # 视觉
        self.sprite = self._create_sprite(color_idx)
        self.is_player = False
        
    def set_pathfinder(self, pathfinder):
        self.pathfinder = pathfinder
        
    def _create_sprite(self, color_idx: int):
        color = self.SHIRT_COLORS[color_idx % len(self.SHIRT_COLORS)]
        sheet = pygame.Surface((64, 64), pygame.SRCALPHA)
        
        for direction in range(4):
            for frame in range(4):
                x = frame * 16
                y = direction * 16
                pygame.draw.rect(sheet, color, (x + 4, y + 6, 8, 8))
                pygame.draw.circle(sheet, (255, 220, 180), (x + 8, y + 5), 3)
                leg_offset = (frame % 2) * 2
                pygame.draw.rect(sheet, (60, 40, 30), (x + 4 + leg_offset, y + 14, 2, 2))
                pygame.draw.rect(sheet, (60, 40, 30), (x + 10 - leg_offset, y + 14, 2, 2))
                
        return CharacterSprite(SpriteSheet.from_surface(sheet, 16, 16), None)
        
    def update(self, dt: float, world_map: WorldMap, animation: AnimationManager, 
               hour: int, weather_effects: Dict, is_player_control: bool, keys: Dict):
        """更新AI"""
        # 更新生存
        self.survival.update(dt, weather_effects, hour)
        
        if self.survival.is_dead:
            return
            
        # 玩家控制
        if is_player_control:
            self._player_control(dt, world_map, animation, keys)
            return
            
        # AI自主控制（带生存优先级）
        priority = self.survival.get_priority()
        
        if priority == 'critical':
            # 濒死：找食物或睡觉
            if self.survival.should_sleep(hour):
                self.survival.is_sleeping = True
                return
            else:
                self._seek_food(world_map, animation)
                return
        elif priority == 'low_energy':
            if self.survival.eat():
                return
            self._seek_food(world_map, animation)
            return
        elif priority == 'hungry':
            if self.survival.eat():
                return
        elif priority == 'wake_up':
            self.survival.is_sleeping = False
            
        # 正常移动
        self._normal_movement(dt, world_map, animation)
        
    def _player_control(self, dt, world_map, animation, keys):
        """玩家控制"""
        move_speed = 4 * dt
        dx = dy = 0
        
        if keys.get('up'): dy = -move_speed
        if keys.get('down'): dy = move_speed
        if keys.get('left'): dx = -move_speed
        if keys.get('right'): dx = move_speed
            
        if dx != 0 or dy != 0:
            new_x = self.x + dx
            new_y = self.y + dy
            
            if 0 <= new_x < 100 and 0 <= new_y < 100:
                tile_type, _ = world_map.get_tile(int(new_x), int(new_y))
                if tile_type not in ['water', 'mountain']:
                    self.x = new_x
                    self.y = new_y
                    self.sprite.update(dt, dx*10, dy*10)
                    if random.random() < 0.3:
                        animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
                        
    def _seek_food(self, world_map, animation):
        """寻找食物"""
        tile_type, _ = world_map.get_tile(int(self.x), int(self.y))
        if self.survival.gather_food(tile_type):
            animation.add_dust(self.x * TILE_SIZE, self.y * TILE_SIZE)
            
    def _normal_movement(self, dt, world_map, animation):
        """正常移动"""
        if self.survival.is_sleeping:
            self.sprite.update(dt, 0, 0)
            return
            
        if self.movement.is_moving:
            new_x, new_y = self.movement.update(dt)
            tile_type, _ = world_map.get_tile(int(new_x), int(new_y))
            
            if tile_type not in ['water', 'mountain']:
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
            self.path_recalc_timer += dt
            if self.path_recalc_timer > 3.0 and self.pathfinder:
                self.path_recalc_timer = 0
                target_x = max(0, min(99, self.x + random.randint(-15, 15)))
                target_y = max(0, min(99, self.y + random.randint(-15, 15)))
                
                path = self.pathfinder.find_path(self.x, self.y, target_x, target_y)
                if path and len(path) > 1:
                    self.movement.set_path(path, (self.x, self.y))
                else:
                    self.sprite.update(dt, 0, 0)
                    
    def render(self, screen, camera):
        """渲染"""
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        if -50 < sx < screen.get_width() + 50 and -50 < sy < screen.get_height() + 50:
            # 玩家高亮
            if self.is_player:
                pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
                radius = 22 + int(pulse * 3)
                pygame.draw.circle(screen, (255, 215, 0), (sx, sy), radius, 3)
                
            # 死亡状态
            if self.survival.is_dead:
                pygame.draw.circle(screen, (100, 100, 100), (sx, sy), 15)
                return
                
            # 精灵
            self.sprite.render(screen, sx, sy, scale=2.0)
            
            # 名字
            font = pygame.font.SysFont('microsoftyahei', 11, bold=True)
            name_text = font.render(self.name, True, (255, 255, 255))
            name_x = sx - name_text.get_width() // 2
            name_bg = pygame.Rect(name_x - 4, sy - 30, name_text.get_width() + 8, 16)
            pygame.draw.rect(screen, (0, 0, 0, 150), name_bg, border_radius=4)
            screen.blit(name_text, (name_x, sy - 28))
            
            # 能量条（颜色编码）
            bar_w = 36
            bar_h = 5
            bar_x = sx - bar_w // 2
            bar_y = sy + 20
            
            energy = self.survival.energy
            energy_pct = energy / 100
            
            pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            
            fill_w = int(bar_w * energy_pct)
            if fill_w > 0:
                if energy > 60:
                    color = (100, 255, 100)
                elif energy > 30:
                    color = (255, 220, 80)
                else:
                    color = (255, 80, 80)
                pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.7 - 修复版")
        self.clock = pygame.time.Clock()
        
        # 世界
        self.world = WorldMap(100, 100)
        
        # 路径寻找
        self.pathfinder = AStarPathfinder(100, 100)
        self.pathfinder.set_obstacles(self.world.obstacles)
        
        # AI们
        self.agents: List[GameAgent] = []
        for i in range(15):
            agent = GameAgent(f"agent_{i}", f"AI-{i}",
                            random.randint(40, 60), random.randint(40, 60), i)
            agent.set_pathfinder(self.pathfinder)
            self.agents.append(agent)
            
        # 玩家
        self.player_agent = self.agents[0]
        self.player_agent.is_player = True
        self.player_control = False
        
        # 系统
        self.camera = GameCamera(100, 100, TILE_SIZE)
        self.camera.set_target(self.player_agent)
        self.animation = AnimationManager()
        self.hud = ModernHUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.event_manager = EventManager()
        
        # 时间
        self.game_time = 12.0
        self.day = 1
        self.season = Season.SPRING
        
        # 状态
        self.paused = False
        self.speed = 1
        self.running = True
        
    def handle_input(self):
        """处理输入"""
        keys = pygame.key.get_pressed()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player_control = not self.player_control
                    mode = "玩家" if self.player_control else "AI"
                    print(f"🎮 切换到{mode}控制")
                elif event.key == pygame.K_F12:
                    self.camera.toggle_god_mode()
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.camera.zoom_in()
                elif event.button == 5:
                    self.camera.zoom_out()
                    
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
                
        return {
            'up': keys[pygame.K_w] or keys[pygame.K_UP],
            'down': keys[pygame.K_s] or keys[pygame.K_DOWN],
            'left': keys[pygame.K_a] or keys[pygame.K_LEFT],
            'right': keys[pygame.K_d] or keys[pygame.K_RIGHT],
        }
        
    def update(self, dt: float, input_keys: Dict):
        """更新"""
        if self.paused:
            return
            
        # 更新时间
        self.game_time += dt * self.speed / 60
        if self.game_time >= 24:
            self.game_time = 0
            self.day += 1
            
        hour = int(self.game_time)
        
        # 更新事件
        self.event_manager.update(dt, self.season, hour, self.day, len(self.agents))
        weather_effects = self.event_manager.get_active_effects()
        
        # 更新相机
        self.camera.update(self.screen.get_width(), self.screen.get_height())
        self.animation.update(dt)
        self.hud.update(dt)
        
        # 更新AI
        for agent in self.agents:
            is_player = (agent == self.player_agent and self.player_control)
            agent.update(dt * self.speed, self.world, self.animation, 
                        hour, weather_effects, is_player, input_keys)
            
    def render(self):
        """渲染"""
        self.screen.fill((20, 25, 20))
        
        # 世界
        self.world.render(self.screen, self.camera, self.animation.time)
        
        # AI
        for agent in self.agents:
            agent.render(self.screen, self.camera)
            
        # 粒子
        self.animation.render(self.screen, self.camera.x, self.camera.y, TILE_SIZE)
        
        # 日夜
        hour = int(self.game_time)
        EnvironmentEffects.render_day_night_overlay(self.screen, hour, 0)
        
        # HUD
        game_state = {
            'player': {
                'name': self.player_agent.name,
                'status': '🎮 玩家控制' if self.player_control else '🤖 AI自主',
                'energy': self.player_agent.survival.energy,
                'mood': 70.0,
                'money': 100,
                'goal': '探索世界',
            },
            'year': 1,
            'season': self.season.value.title(),
            'day': self.day,
            'hour': hour,
            'minute': int((self.game_time % 1) * 60),
            'weather': 'Sunny',
            'speed': self.speed,
            'paused': self.paused,
            'controls': 'WASD:移动 | 空格:切换 | F12:上帝',
            'god_mode': self.camera.god_mode,
            'player_pos': (self.player_agent.x, self.player_agent.y),
            'world_width': 100,
            'world_height': 100,
        }
        
        self.hud.render(self.screen, game_state)
        pygame.display.flip()
        
    async def run(self):
        print("🎮 AnotherYou ECO v0.7 - 修复版")
        print("=" * 50)
        print("✨ 修复内容:")
        print("  • A*路径寻找 + Bezier平滑移动")
        print("  • 现代UI（圆角+图标+动画）")
        print("  • 事件冷却系统（防重复）")
        print("  • AI生存系统（防集体死亡）")
        print("=" * 50)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            input_keys = self.handle_input()
            self.update(dt, input_keys)
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
