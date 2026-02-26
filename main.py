"""
AnotherYou ECO - 主版本
持续迭代的唯一入口
当前: v0.6 专业像素版
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
from ui.pro_hud import ProfessionalHUD

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
        
        self._generate()
        
    def _generate(self):
        """生成地图"""
        import math
        
        center_x, center_y = self.width // 2, self.height // 2
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # 边缘山地
                if dist > min(self.width, self.height) * 0.42:
                    tile_type = 'mountain'
                # 河流
                elif abs(y - center_y) < 4 and random.random() > 0.2:
                    tile_type = 'water'
                # 湖泊
                elif dist < 10 and random.random() > 0.4:
                    tile_type = 'water'
                # 森林群
                elif random.random() < 0.22:
                    tile_type = 'forest'
                # 沙滩
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
                
                # 特殊动画瓦片
                if tile_type == 'water':
                    EnvironmentEffects.render_water_animation(
                        screen, x, y, TILE_SIZE, animation_time,
                        (60, 110, 200)
                    )
                elif tile_type == 'forest':
                    EnvironmentEffects.render_tree_sway(
                        screen, x, y, TILE_SIZE, animation_time,
                        (40, 100, 50)
                    )
                else:
                    # 普通瓦片
                    tile_image = self.tileset.get_tile(tile_type, variant)
                    screen.blit(tile_image, (x, y))


class GameAgent:
    """游戏AI角色"""
    
    SHIRT_COLORS = [
        (220, 80, 80), (80, 120, 220), (80, 180, 80),
        (220, 180, 60), (180, 100, 200), (255, 140, 80),
    ]
    
    def __init__(self, agent_id: str, name: str, x: float, y: float, color_idx: int):
        self.id = agent_id
        self.name = name
        self.x = x
        self.y = y
        
        self.energy = 100.0
        self.mood = 70.0
        self.money = random.randint(50, 200)
        self.alive = True
        
        # 创建精灵
        self.sprite = self._create_sprite(color_idx)
        
        self.goal = "探索世界"
        self.action_timer = 0
        self.move_cooldown = 0
        
    def _create_sprite(self, color_idx: int) -> CharacterSprite:
        """创建角色精灵"""
        # 使用程序生成的简单精灵图
        # 实际项目中应该加载外部sprite sheet
        color = self.SHIRT_COLORS[color_idx % len(self.SHIRT_COLORS)]
        
        # 创建临时sprite sheet
        sheet_size = 64  # 4x4 16x16 sprites
        sheet = pygame.Surface((sheet_size, sheet_size), pygame.SRCALPHA)
        
        # 绘制4方向x4帧的行走动画
        for direction in range(4):
            for frame in range(4):
                x = frame * 16
                y = direction * 16
                
                # 身体（衣服颜色）
                body_color = color
                pygame.draw.rect(sheet, body_color, (x + 4, y + 6, 8, 8))
                
                # 头
                pygame.draw.circle(sheet, (255, 220, 180), (x + 8, y + 5), 3)
                
                # 腿（动画）
                leg_offset = (frame % 2) * 2
                pygame.draw.rect(sheet, (60, 40, 30), (x + 4 + leg_offset, y + 14, 2, 2))
                pygame.draw.rect(sheet, (60, 40, 30), (x + 10 - leg_offset, y + 14, 2, 2))
                
        sprite_sheet = SpriteSheet.from_surface(sheet, 16, 16)
        return CharacterSprite(sprite_sheet, None)
        
    def update(self, dt: float, world_map: WorldMap, animation: AnimationManager):
        """更新AI"""
        if not self.alive:
            return
            
        # 能量消耗
        self.energy -= 0.03 * dt
        if self.energy <= 0:
            self.energy = 0
            self.alive = False
            return
            
        # AI决策
        self.action_timer += dt
        self.move_cooldown -= dt
        
        if self.action_timer > 3.0 and self.move_cooldown <= 0:
            self.action_timer = 0
            self._decide_and_move(world_map, animation)
            
        # 更新动画
        self.sprite.update(dt, 0, 0)
        
    def _decide_and_move(self, world_map: WorldMap, animation: AnimationManager):
        """决策并移动"""
        # 简单AI：随机方向移动
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        dx, dy = random.choice(directions)
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 检查边界和可行走
        if 0 <= new_x < world_map.width and 0 <= new_y < world_map.height:
            tile_type, _ = world_map.get_tile(int(new_x), int(new_y))
            if tile_type not in ['water', 'mountain']:
                self.x = new_x
                self.y = new_y
                self.move_cooldown = 0.5
                
                # 添加尘土效果
                screen_x = self.x * TILE_SIZE
                screen_y = self.y * TILE_SIZE
                animation.add_dust(screen_x, screen_y)
                
                # 更新动画方向
                if dy < 0:
                    self.sprite.current_direction = 'up'
                elif dy > 0:
                    self.sprite.current_direction = 'down'
                elif dx < 0:
                    self.sprite.current_direction = 'left'
                elif dx > 0:
                    self.sprite.current_direction = 'right'
                    
                self.sprite.is_moving = True
                
        # 更新目标
        goals = ["寻找食物", "探索森林", "采集资源", "休息", "社交"]
        self.goal = random.choice(goals)
        
    def render(self, screen: pygame.Surface, camera: GameCamera, is_player: bool = False):
        """渲染角色"""
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        if -50 < sx < screen.get_width() + 50 and -50 < sy < screen.get_height() + 50:
            # 玩家高亮
            if is_player:
                pygame.draw.circle(screen, (255, 215, 0), (sx, sy), 22, 3)
                
            # 渲染精灵
            self.sprite.render(screen, sx, sy, scale=2.0)
            
            # 名字
            font = pygame.font.SysFont('microsoftyahei', 11)
            name_text = font.render(self.name, True, (255, 255, 255))
            name_x = sx - name_text.get_width() // 2
            screen.blit(name_text, (name_x, sy - 28))
            
            # 能量条
            bar_w = 30
            bar_h = 4
            energy_pct = self.energy / 100
            bar_x = sx - bar_w // 2
            bar_y = sy + 18
            
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
            energy_color = (0, 255, 0) if energy_pct > 0.5 else (255, 200, 0) if energy_pct > 0.3 else (255, 0, 0)
            pygame.draw.rect(screen, energy_color, (bar_x, bar_y, int(bar_w * energy_pct), bar_h))


class Game:
    """主游戏"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AnotherYou ECO v0.6 - 专业版")
        self.clock = pygame.time.Clock()
        
        # 世界
        self.world = WorldMap(100, 100)
        
        # AI们
        self.agents: Dict[str, GameAgent] = {}
        for i in range(20):
            agent = GameAgent(
                f"agent_{i}", f"AI-{i}",
                random.randint(40, 60), random.randint(40, 60), i
            )
            self.agents[agent.id] = agent
            
        # 玩家
        self.player_agent = list(self.agents.values())[0]
        self.player_control = False
        
        # 系统
        self.camera = GameCamera(100, 100, TILE_SIZE)
        self.camera.set_target(self.player_agent)
        self.animation = AnimationManager()
        self.hud = ProfessionalHUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # 时间
        self.game_time = 0  # 游戏内时间（小时）
        self.day = 1
        self.season = 'Spring'
        
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
                if event.key == pygame.K_F12:
                    self.camera.toggle_god_mode()
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                elif event.key == pygame.K_c:
                    self.player_control = not self.player_control
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.camera.zoom_in()
                elif event.button == 5:
                    self.camera.zoom_out()
                    
        # 持续按键
        keys = pygame.key.get_pressed()
        
        if self.camera.god_mode:
            # 上帝模式移动相机
            speed = 15
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.camera.move(0, -speed)
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.camera.move(0, speed)
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.camera.move(-speed, 0)
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.camera.move(speed, 0)
        else:
            # 玩家模式
            if self.player_control:
                move_speed = 4 * (1/60)
                dx, dy = 0, 0
                
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    dy = -move_speed
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    dy = move_speed
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    dx = -move_speed
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    dx = move_speed
                    
                if dx != 0 or dy != 0:
                    new_x = self.player_agent.x + dx
                    new_y = self.player_agent.y + dy
                    
                    if 0 <= new_x < 100 and 0 <= new_y < 100:
                        tile_type, _ = self.world.get_tile(int(new_x), int(new_y))
                        if tile_type not in ['water', 'mountain']:
                            self.player_agent.x = new_x
                            self.player_agent.y = new_y
                            self.player_agent.sprite.update(1/60, dx*60, dy*60)
                            
                            # 添加尘土
                            self.animation.add_dust(new_x * TILE_SIZE, new_y * TILE_SIZE)
                            
    def update(self, dt: float):
        """更新"""
        if self.paused:
            return
            
        # 更新时间
        self.game_time += dt * self.speed / 60  # 1秒 = 1游戏分钟
        if self.game_time >= 24:
            self.game_time = 0
            self.day += 1
            
        # 更新相机
        self.camera.update(self.screen.get_width(), self.screen.get_height())
        
        # 更新动画
        self.animation.update(dt)
        
        # 更新AI
        for agent in self.agents.values():
            if agent != self.player_agent or not self.player_control:
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
                'status': '玩家控制' if self.player_control else 'AI自主',
                'energy': self.player_agent.energy,
                'mood': self.player_agent.mood,
                'money': self.player_agent.money,
            },
            'year': 1,
            'season': self.season,
            'day': self.day,
            'hour': hour,
            'minute': int((self.game_time % 1) * 60),
            'weather': 'Sunny',
            'goal': self.player_agent.goal,
            'speed': self.speed,
            'paused': self.paused,
            'controls': 'WASD:移动 | F12:上帝 | C:切换控制',
            'god_mode': self.camera.god_mode,
            'player_pos': (self.player_agent.x, self.player_agent.y),
            'world_width': 100,
            'world_height': 100,
        }
        
        self.hud.render(self.screen, game_state)
        
        pygame.display.flip()
        
    async def run(self):
        """主循环"""
        print("🎮 AnotherYou ECO v0.6 - 专业版")
        print("=" * 40)
        print("✨ 特性:")
        print("  • 32x32像素瓦片地形")
        print("  • 16x16角色精灵（4方向动画）")
        print("  • 水波/树摇摆动画")
        print("  • 走路尘土粒子")
        print("  • 日夜循环")
        print("  • 专业HUD界面")
        print("=" * 40)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_input()
            self.update(dt)
            self.render()
            
            await asyncio.sleep(0)
            
        pygame.quit()


# 扩展SpriteSheet支持从surface创建
@classmethod
def from_surface(cls, surface: pygame.Surface, tile_width: int, tile_height: int):
    """从surface创建sprite sheet"""
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
