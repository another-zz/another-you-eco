"""
AnotherYou ECO - 主版本 v0.7
现代UI + 智能AI移动
"""

import pygame
import asyncio
import random
import math
from typing import Dict, List, Tuple

import sys
sys.path.insert(0, '/root/.openclaw/workspace/another-you-eco')

from core.sprite_loader import TilesetManager, CharacterSprite, SpriteSheet
from core.camera import GameCamera
from core.animation import AnimationManager, EnvironmentEffects
from core.agent_core import AgentCore
from core.control_switcher import ControlSwitcher, ControlMode
from core.pathfinder import AStarPathfinder, SmoothMovement
from core.event_manager import EventManager, Season
from core.agent_survival import SurvivalSystem
from ui.modern_hud import ModernHUD

# 配置
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60
TILE_SIZE = 32


class WorldMap:
    """游戏世界地图"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = []
        self.tileset = TilesetManager(TILE_SIZE)
        self.obstacles = []  # 障碍物列表
        self._generate()
        
    def _generate(self):
        """生成地图"""
        center_x, center_y = self.width // 2, self.height // 2
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                if dist > min(self.width, self.height) * 0.42:
                    tile_type = 'mountain'
                    self.obstacles.append((x, y))
                elif abs(y - center_y) < 4 and random.random() > 0.2:
                    tile_type = 'water'
                    self.obstacles.append((x, y))
                elif dist < 10 and random.random() > 0.4:
                    tile_type = 'water'
                    self.obstacles.append((x, y))
                elif random.random() < 0.22:
                    tile_type = 'forest'
                elif random.random() < 0.08:
                    tile_type = 'sand'
                else:
                    tile_type = 'grass'
                    
                variant = random.randint(0, 2)
                row.append((tile_type, variant))
            self.tiles.append(row)
            
    def get_tile(self, x: int, y: int):
        """获取瓦片"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return ('grass', 0)
        
    def render(self, screen: pygame.Surface, camera: GameCamera, animation_time: float):
        """渲染地图"""
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
    """游戏AI角色（带A*路径寻找和平滑移动）"""
    
    SHIRT_COLORS = [
        (220, 80, 80), (80, 120, 220), (80, 180, 80),
        (220, 180, 60), (180, 100, 200), (255, 140, 80),
    ]
    
    def __init__(self, agent_id: str, name: str, x: float, y: float, color_idx: int):
        self.id = agent_id
        self.name = name
        
        # AI核心大脑
        self.brain = AgentCore(agent_id, name)
        self.brain.x = x
        self.brain.y = y
        
        # 生存系统
        self.survival = SurvivalSystem(self.brain)
        self.survival.set_home(int(x), int(y))
        
        # 控制切换器
        self.control = ControlSwitcher(self.brain)
        
        # 路径寻找和平滑移动
        self.pathfinder: AStarPathfinder = None
        self.movement = SmoothMovement(speed=2.5)
        self.path_recalc_timer = 0
        self.target_pos = None
        
        # 视觉
        self.sprite = self._create_sprite(color_idx)
        self.color_idx = color_idx
        
    def set_pathfinder(self, pathfinder: AStarPathfinder):
        """设置路径寻找器"""
        self.pathfinder = pathfinder
        
    def _create_sprite(self, color_idx: int):
        """创建角色精灵"""
        color = self.SHIRT_COLORS[color_idx % len(self.SHIRT_COLORS)]
        sheet_size = 64
        sheet = pygame.Surface((sheet_size, sheet_size), pygame.SRCALPHA)
        
        for direction in range(4):
            for frame in range(4):
                x = frame * 16
                y = direction * 16
                pygame.draw.rect(sheet, color, (x + 4, y + 6, 8, 8))
                pygame.draw.circle(sheet, (255, 220, 180), (x + 8, y + 5), 3)
                leg_offset = (frame % 2) * 2
                pygame.draw.rect(sheet, (60, 40, 30), (x + 4 + leg_offset, y + 14, 2, 2))
                pygame.draw.rect(sheet, (60, 40, 30), (x + 10 - leg_offset, y + 14, 2, 2))
                
        sprite_sheet = SpriteSheet.from_surface(sheet, 16, 16)
        return CharacterSprite(sprite_sheet, None)
        
    def update(self, dt: float, world_map: WorldMap, animation: AnimationManager):
        """更新角色"""
        # 更新控制切换器
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        
        self.control.update(dt, {
            'up': keys[pygame.K_w] or keys[pygame.K_UP],
            'down': keys[pygame.K_s] or keys[pygame.K_DOWN],
            'left': keys[pygame.K_a] or keys[pygame.K_LEFT],
            'right': keys[pygame.K_d] or keys[pygame.K_RIGHT],
            'action': keys[pygame.K_e],
        }, {
            'left': mouse_buttons[0],
            'right': mouse_buttons[2],
        }, pygame.mouse.get_pos())
        
        if self.control.is_player_control():
            # 玩家控制模式
            self._update_player_control(dt, world_map, animation)
        else:
            # AI自主模式
            self._update_ai_control(dt, world_map, animation)
            
    def _update_player_control(self, dt: float, world_map: WorldMap, animation: AnimationManager):
        """玩家控制更新"""
        move_speed = 4 * dt
        dx, dy = 0, 0
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -move_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = move_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -move_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = move_speed
            
        if dx != 0 or dy != 0:
            new_x = self.brain.x + dx
            new_y = self.brain.y + dy
            
            if 0 <= new_x < 100 and 0 <= new_y < 100:
                tile_type, _ = world_map.get_tile(int(new_x), int(new_y))
                if tile_type not in ['water', 'mountain']:
                    self.brain.x = new_x
                    self.brain.y = new_y
                    self.sprite.update(dt, dx*10, dy*10)
                    
                    if random.random() < 0.3:
                        animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
                        
    def _update_ai_control(self, dt: float, world_map: WorldMap, animation: AnimationManager):
        """AI控制更新（使用A*和平滑移动）"""
        # 构建世界上下文
        world_context = {
            'time': '12:00',
            'location': (self.brain.x, self.brain.y),
            'nearby': [],
            'energy': self.brain.energy,
            'mood': self.brain.mood,
            'money': self.brain.money,
        }
        
        # AI决策
        result = self.brain.update(dt, world_context)
        
        # 如果正在移动，继续平滑移动
        if self.movement.is_moving:
            new_x, new_y = self.movement.update(dt)
            
            # 检查边界和障碍物
            if 0 <= new_x < 100 and 0 <= new_y < 100:
                tile_type, _ = world_map.get_tile(int(new_x), int(new_y))
                if tile_type not in ['water', 'mountain']:
                    dx = new_x - self.brain.x
                    dy = new_y - self.brain.y
                    self.brain.x = new_x
                    self.brain.y = new_y
                    self.sprite.update(dt, dx*10, dy*10)
                    
                    # 添加尘土效果
                    if self.movement.is_moving and random.random() < 0.2:
                        animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
                else:
                    # 遇到障碍，停止移动
                    self.movement.is_moving = False
        else:
            # 需要新路径
            self.path_recalc_timer += dt
            
            if self.path_recalc_timer > 2.0 and self.pathfinder:  # 每2秒重新规划
                self.path_recalc_timer = 0
                
                # 根据AI决策选择目标
                if result['action']['type'] == 'move':
                    # 随机选择一个方向走一段距离
                    dx = result['action'].get('dx', 0) * 10
                    dy = result['action'].get('dy', 0) * 10
                    target_x = max(0, min(99, self.brain.x + dx))
                    target_y = max(0, min(99, self.brain.y + dy))
                    
                    # A*寻路
                    path = self.pathfinder.find_path(
                        self.brain.x, self.brain.y, target_x, target_y
                    )
                    
                    if path and len(path) > 1:
                        self.movement.set_path(path, (self.brain.x, self.brain.y))
                    else:
                        # 无法找到路径，原地等待
                        self.sprite.update(dt, 0, 0)
                else:
                    self.sprite.update(dt, 0, 0)
                    
    def render(self, screen: pygame.Surface, camera: GameCamera, is_player: bool = False):
        """渲染角色"""
        sx, sy = camera.world_to_screen(self.brain.x, self.brain.y)
        
        if -50 < sx < screen.get_width() + 50 and -50 < sy < screen.get_height() + 50:
            # 玩家高亮（脉冲效果）
            if is_player:
                pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
                radius = 22 + int(pulse * 3)
                alpha = int(150 + 50 * pulse)
                pygame.draw.circle(screen, (255, 215, 0, alpha), (sx, sy), radius, 3)
                
            # 渲染精灵
            self.sprite.render(screen, sx, sy, scale=2.0)
            
            # 名字标签（现代风格）
            font = pygame.font.SysFont('microsoftyahei', 11, bold=True)
            name_text = font.render(self.name, True, (255, 255, 255))
            name_x = sx - name_text.get_width() // 2
            
            # 名字背景
            name_bg = pygame.Rect(name_x - 4, sy - 30, name_text.get_width() + 8, 16)
            pygame.draw.rect(screen, (0, 0, 0, 150), name_bg, border_radius=4)
            screen.blit(name_text, (name_x, sy - 28))
            
            # 思考气泡（AI模式，仅玩家角色）
            if not self.control.is_player_control() and is_player:
                thought = self.brain.thought_bubble
                if thought and thought != "...":
                    self._render_thought_bubble(screen, sx, sy - 50, thought)
            
            # 能量条（现代风格）
            self._render_energy_bar(screen, sx, sy + 20, self.brain.energy)
            
    def _render_thought_bubble(self, screen: pygame.Surface, x: int, y: int, text: str):
        """渲染思考气泡"""
        bubble_font = pygame.font.SysFont('microsoftyahei', 10)
        thought_text = bubble_font.render(text[:25], True, (220, 230, 255))
        
        bubble_w = thought_text.get_width() + 12
        bubble_h = thought_text.get_height() + 8
        bubble_x = x - bubble_w // 2
        bubble_y = y
        
        # 气泡背景（圆角）
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
        pygame.draw.rect(screen, (40, 50, 80, 230), bubble_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 150, 200, 200), bubble_rect, 2, border_radius=8)
        
        # 小三角
        pygame.draw.polygon(screen, (40, 50, 80), [
            (x, bubble_y + bubble_h + 4),
            (x - 6, bubble_y + bubble_h - 2),
            (x + 6, bubble_y + bubble_h - 2)
        ])
        
        screen.blit(thought_text, (bubble_x + 6, bubble_y + 4))
        
    def _render_energy_bar(self, screen: pygame.Surface, x: int, y: int, energy: float):
        """渲染现代能量条"""
        bar_w = 36
        bar_h = 5
        bar_x = x - bar_w // 2
        
        # 背景
        pygame.draw.rect(screen, (40, 40, 50), (bar_x, y, bar_w, bar_h), border_radius=3)
        
        # 填充
        fill_w = int(bar_w * max(0, min(1, energy / 100)))
        if fill_w > 0:
            if energy > 60:
                color = (100, 255, 100)
            elif energy > 30:
                color = (255, 220, 80)
            else:
                color = (255, 80, 80)
            pygame.draw.rect(screen, color, (bar_x, y, fill_w, bar_h), border_radius=3)


class Game:
    """主游戏"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.7 - 现代版")
        self.clock = pygame.time.Clock()
        
        # 世界
        self.world = WorldMap(100, 100)
        
        # 路径寻找器
        self.pathfinder = AStarPathfinder(100, 100)
        self.pathfinder.set_obstacles(self.world.obstacles)
        
        # AI们
        self.agents: Dict[str, GameAgent] = {}
        for i in range(20):
            agent = GameAgent(
                f"agent_{i}", f"AI-{i}",
                random.randint(40, 60), random.randint(40, 60), i
            )
            agent.set_pathfinder(self.pathfinder)
            self.agents[agent.id] = agent
            
        # 玩家
        self.player_agent = list(self.agents.values())[0]
        
        # 系统
        self.camera = GameCamera(100, 100, TILE_SIZE)
        self.camera.set_target(self.player_agent)
        self.animation = AnimationManager()
        self.hud = ModernHUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 时间
        self.game_time = 0
        self.day = 1
        self.season = 'Spring'
        
        # 状态
        self.paused = False
        self.speed = 1
        self.running = True
        
        # 每日反思计时
        self.last_reflection_day = 0
        
    def handle_input(self):
        """处理输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if self.player_agent.control.handle_input(event):
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    self.camera.toggle_god_mode()
                elif event.key == pygame.K_SPACE:
                    if self.player_agent.control.mode == ControlMode.AI_MODE:
                        self.player_agent.control.switch_to_player()
                    else:
                        self.player_agent.control.switch_to_ai()
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
        keys = pygame.key.get_pressed()
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
                
    def update(self, dt: float):
        """更新"""
        if self.paused:
            return
            
        # 更新时间
        self.game_time += dt * self.speed / 60
        if self.game_time >= 24:
            self.game_time = 0
            self.day += 1
            
        # 每日反思
        if self.day != self.last_reflection_day:
            self.last_reflection_day = self.day
            for agent in self.agents.values():
                agent.brain.daily_reflection()
                
        # 更新相机
        self.camera.update(self.screen.get_width(), self.screen.get_height())
        
        # 更新动画
        self.animation.update(dt)
        self.hud.update(dt)
        
        # 更新AI
        for agent in self.agents.values():
            agent.update(dt * self.speed, self.world, self.animation)
            
    def render(self):
        """渲染"""
        self.screen.fill((20, 25, 20))
        
        # 渲染世界
        self.world.render(self.screen, self.camera, self.animation.time)
        
        # 渲染AI
        for agent in self.agents.values():
            is_player = (agent == self.player_agent)
            agent.render(self.screen, self.camera, is_player)
            
        # 渲染粒子
        self.animation.render(self.screen, self.camera.x, self.camera.y, TILE_SIZE)
        
        # 日夜效果
        hour = int(self.game_time)
        EnvironmentEffects.render_day_night_overlay(self.screen, hour, 0)
        
        # HUD
        game_state = {
            'player': {
                'name': self.player_agent.name,
                'status': self.player_agent.control.get_mode_display(),
                'energy': self.player_agent.brain.energy,
                'mood': self.player_agent.brain.mood,
                'money': self.player_agent.brain.money,
                'goal': self.player_agent.brain.planner.current_goal or "探索世界",
            },
            'year': 1,
            'season': self.season,
            'day': self.day,
            'hour': hour,
            'minute': int((self.game_time % 1) * 60),
            'weather': 'Sunny',
            'speed': self.speed,
            'paused': self.paused,
            'controls': 'WASD:移动 | 空格:切换AI/玩家 | F12:上帝模式',
            'god_mode': self.camera.god_mode,
            'player_pos': (self.player_agent.brain.x, self.player_agent.brain.y),
            'world_width': 100,
            'world_height': 100,
        }
        
        self.hud.render(self.screen, game_state)
        
        pygame.display.flip()
        
    async def run(self):
        """主循环"""
        print("🎮 AnotherYou ECO v0.7 - 现代版")
        print("=" * 50)
        print("✨ 新特性:")
        print("  • A*智能路径寻找")
        print("  • 平滑移动（无抖动）")
        print("  • 现代UI（圆角面板+动画）")
        print("  • 颜色编码+图标")
        print("=" * 50)
        print("控制:")
        print("  空格 - 切换玩家控制/AI自主")
        print("  WASD - 移动")
        print("  ESC  - 释放控制（切回AI）")
        print("  F12  - 上帝模式")
        print("=" * 50)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_input()
            self.update(dt)
            self.render()
            
            await asyncio.sleep(0)
            
        pygame.quit()


# 扩展SpriteSheet
@classmethod
def from_surface(cls, surface: pygame.Surface, tile_width: int, tile_height: int):
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
