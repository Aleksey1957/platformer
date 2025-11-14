import json

import pygame as pg
import pytmx
from PIL.ImageChops import offset
from Tools.scripts.highlight import html_highlight
from matplotlib.pyplot import title

pg.init()

SCREEN_WIDTH = 1020
SCREEN_HEIGHT = 760
FPS = 80
TILE_SCALE = 1
GRAVITY = 1.5
MOVE_SPEED = 10
JUMP_SPEED = -20
MAX_FALL_SPEED = 14

font = pg.font.Font(None, 40)


class Platform(pg.sprite.Sprite):
    def __init__(self, image, x, y, width, height):
        super(Platform, self).__init__()

        self.image = pg.transform.scale(image.convert_alpha(), (width * TILE_SCALE, height * TILE_SCALE))
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SCALE
        self.rect.y = y * TILE_SCALE
        self.mask = pg.mask.from_surface(self.image)



class Player(pg.sprite.Sprite):
    def __init__(self, map_width, map_height):
        super(Player, self).__init__()
        self.load_animations()  # Загрузка анимаций
        self.current_animation = self.idle_animation_right
        self.image = self.current_animation[0].convert_alpha()
        self.current_image = 0
        self.rect = self.image.get_rect()
        self.rect.center = (72, 832)

        self.mask = pg.mask.from_surface(self.image)

        self.direction = 'right'
        # Начальные параметры движения и положения
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = GRAVITY
        self.is_jumping = False
        self.map_width = map_width * TILE_SCALE
        self.map_height = map_height * TILE_SCALE

        self.timer = pg.time.get_ticks()
        self.interval = 200

        self.hp = 10  # Здоровье игрока
        self.damage_timer = pg.time.get_ticks()
        self.damage_interval = 1000

    def get_damage(self):
        if pg.time.get_ticks() - self.damage_timer > self.damage_interval:
            self.hp -= 5
            self.damage_timer = pg.time.get_ticks()

    def load_animations(self):
        tile_size = 32
        tile_scale = 2

        self.idle_animation_right = []

        num_images = 4
        sptitesheet = pg.image.load('sprites/Sprite Pack 3/4 - Tommy/Idle_Poses (32 x 32).png')

        for i in range(num_images):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = sptitesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.move_animation_right = []

        num_images = 8
        sptitesheet = pg.image.load('sprites/Sprite Pack 3/4 - Tommy/Running (32 x 32).png')

        for i in range(num_images):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = sptitesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.move_animation_right.append(image)

        self.move_animation_left = [pg.transform.flip(image, True, False) for image in self.move_animation_right]

    def update(self, platforms):
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE] and not self.is_jumping:
            self.jump()

        if keys[pg.K_a]:
            self.direction = 'left'
            self.velocity_x = -MOVE_SPEED
            self.switch_animation(self.move_animation_left)
        elif keys[pg.K_d]:
            self.direction = 'right'
            self.velocity_x = MOVE_SPEED
            self.switch_animation(self.move_animation_right)
        else:
            self.velocity_x = 0
            self.switch_to_idle()

        # Обработка горизонтального движения
        self.rect.x += self.velocity_x
        self.handle_horizontal_collisions(platforms)

        # Обработка вертикального движения и гравитации
        self.velocity_y += self.gravity
        self.velocity_y = min(self.velocity_y, MAX_FALL_SPEED)  # Ограничение скорости падения
        self.rect.y += self.velocity_y
        self.is_jumping = True
        self.handle_vertical_collisions(platforms)

        self.animate()

        # Ограничение перемещения по карте
        self.constrain_to_map()

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = JUMP_SPEED
            self.is_jumping = True

    def switch_animation(self, new_animation):
        # Переключение анимации персонажа, если текущая анимация отличается от новой
        if self.current_animation != new_animation:
            self.current_animation = new_animation
            self.current_image = 0

    def switch_to_idle(self):
        # Переключение на анимацию покоя, если персонаж не двигается
        if self.current_animation in [self.move_animation_right, self.move_animation_left]:
            self.current_animation = self.idle_animation_right if self.current_animation == self.move_animation_right else self.idle_animation_left
            self.current_image = 0

    def handle_horizontal_collisions(self, platforms):
        # Обработка горизонтальных столкновений с платформами
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # offset = (platform.rect.x - self.rect.x, platform.rect.y - self.rect.y)
                # if self.mask.overlap(platform.mask, offset):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right

    def handle_vertical_collisions(self, platforms):
        # Обработка вертикальных столкновений с платформами
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # offset = (platform.rect.x - self.rect.x, platform.rect.y - self.rect.y)
                # if self.mask.overlap(platform.mask, offset):

                if self.velocity_y > 0:  # Падение
                    self.rect.bottom = platform.rect.top
                    self.is_jumping = False
                elif self.velocity_y < 0:  # Прыжок
                    self.rect.top = platform.rect.bottom
                self.velocity_y = 0

    def animate(self):
        # Обработка анимации персонажа
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image = (self.current_image + 1) % len(self.current_animation)
            self.image = self.current_animation[self.current_image].convert_alpha()
            self.timer = pg.time.get_ticks()
            self.mask = pg.mask.from_surface(self.image)

    def constrain_to_map(self):
        # Ограничение перемещения игрока в пределах карты
        self.rect.right = min(self.rect.right, self.map_width)
        self.rect.left = max(self.rect.left, 0)
        self.rect.bottom = min(self.rect.bottom, self.map_height)
        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity_y = 0

        if self.rect.right > self.map_width:
            self.rect.right = self.map_width - 20


class Crab(pg.sprite.Sprite):
    # Параметры движения для краба
    CRAB_GRAVITY = 2
    CRAB_MOVE_SPEED = 2

    def __init__(self, map_width, map_height, start_pos, final_pos):
        super(Crab, self).__init__()
        self.load_animations()
        self.current_animation = self.animation
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.rect.bottomleft = start_pos
        self.left_edge = start_pos[0]
        self.right_edge = final_pos[0] + self.image.get_width()

        # Инициализация начальных параметров движения
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = self.CRAB_GRAVITY
        self.map_width = map_width * TILE_SCALE
        self.map_height = map_height * TILE_SCALE

        self.timer = pg.time.get_ticks()
        self.interval = 200
        self.direction = "right"

    def load_animations(self):
        tile_scale = 2
        tile_size = 32
        self.animation = []
        image = pg.image.load(
            "sprites/Sprite Pack 2/Sprite Pack 2/9 - Snip Snap Crab/Movement_(Flip_image_back_and_forth) (32 x 32).png")
        image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
        self.animation.append(image)
        self.animation.append(pg.transform.flip(image, True, False))

    def update(self, platforms):
        # Обновление направления движения краба и его положения
        if self.direction == "right":
            self.velocity_x = self.CRAB_MOVE_SPEED
            if self.rect.right >= self.right_edge:
                self.direction = "left"
        elif self.direction == "left":
            self.velocity_x = -self.CRAB_MOVE_SPEED
            if self.rect.left <= self.left_edge:
                self.direction = "right"

        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y + self.gravity

        self.handle_platform_collisions(platforms)
        self.animate()

    def handle_platform_collisions(self, platforms):
        # Обработка столкновений краба с платформами
        for platform in platforms:
            if platform.rect.collidepoint(self.rect.midbottom):
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0

            if platform.rect.collidepoint(self.rect.midtop):
                self.rect.top = platform.rect.bottom
                self.velocity_y = 0

            if platform.rect.collidepoint(self.rect.midright):
                self.rect.right = platform.rect.left

            if platform.rect.collidepoint(self.rect.midleft):
                self.rect.left = platform.rect.right

    def animate(self):
        # Анимация движения краба
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()

class Ball(pg.sprite.Sprite):
    def __init__(self, player_rect, direction):
        super(Ball, self).__init__()

        self.direction = direction
        self.speed = 10

        self.image = pg.image.load('sprites/fireball.png')
        self.image = pg.transform.scale(self.image, (30, 30))

        self.rect = self.image.get_rect()

        if self.direction == 'left':
            self.rect.x = player_rect.x - 2
        else:
            self.rect.x = player_rect.x + 2

        self.rect.y = player_rect.centery

    def update(self):
        if self.direction == 'left':
            self.rect.x -= self.speed
        else:
            self.rect.x += self.speed

        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class Coin(pg.sprite.Sprite):
    def __init__(self, x, y):
        super(Coin, self).__init__()
        self.load_animations()
        self.current_image = 0
        self.image = self.images[0]

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.timer = pg.time.get_ticks()
        self.interval = 200

    def load_animations(self):
        tile_scale = 1.5
        tile_size = 16
        self.images = []
        sptitesheet = pg.image.load(
            "Coin_Gems/MonedaD.png")


        for i in range(4):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = sptitesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.images.append(image)

    def update(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.images):
                self.current_image = 0
            self.image = self.images[self.current_image]
            self.timer = pg.time.get_ticks()

class Portal(pg.sprite.Sprite):
    def __init__(self, x, y):
        super(Portal, self).__init__()
        self.load_animations()
        self.current_image = 0
        self.image = self.images[0]

        self.mask = pg.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

        self.timer = pg.time.get_ticks()
        self.interval = 200

    def load_animations(self):
        tile_scale = 1.5
        tile_size = 64
        self.images = []
        sptitesheet = pg.image.load(
            "sprites\Green Portal Sprite Sheet.png").convert_alpha()


        for i in range(8):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = sptitesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.images.append(image)

    def update(self):
        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.images):
                self.current_image = 0
            self.image = self.images[self.current_image]
            self.timer = pg.time.get_ticks()

class Game:
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Платформер")
        self.level = 1

        self.setup()

    # noinspection PyAttributeOutsideInit

    def setup(self):

        self.mode = 'game'
        self.clock = pg.time.Clock()
        self.is_running = False

        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()

        self.tmx_map = pytmx.load_pygame(f'maps/map{self.level}.tmx')

        self.money = 0
        self.coins = pg.sprite.Group()

        self.portals = pg.sprite.Group()

        self.load_map()

        self.player = Player(self.map_pixel_width, self.map_pixel_height)
        self.all_sprites.add(self.player)

        self.enemies = pg.sprite.Group()

        self.fireballs = pg.sprite.Group()


        with open(f'crab_rect{self.level}.json', 'r') as j:
            data = json.load(j)

        for enemy in data['enemies']:
            if enemy["name"] == 'Crab':
                x1 = enemy["start_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y1 = enemy["start_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth

                x2 = enemy["final_pos"][0] * TILE_SCALE * self.tmx_map.tilewidth
                y2 = enemy["final_pos"][1] * TILE_SCALE * self.tmx_map.tilewidth
                print(x1, x2, y1, y2)
                crab = Crab(self.map_pixel_width, self.map_pixel_height, [x1, y1], [x2, y2])
                self.enemies.add(crab)
                self.all_sprites.add(crab)

        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 4

        self.run()

    def load_map(self):
        self.map_pixel_width = self.tmx_map.width * self.tmx_map.tilewidth * TILE_SCALE
        self.map_pixel_height = self.tmx_map.height * self.tmx_map.tileheight * TILE_SCALE

        for layer in self.tmx_map:
            if layer.name == 'platforms':
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight,
                                            self.tmx_map.tilewidth, self.tmx_map.tileheight)
                        self.all_sprites.add(platform)
                        self.platforms.add(platform)
            elif layer.name == 'decorations':
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        platform = Platform(tile, x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight,
                                            self.tmx_map.tilewidth, self.tmx_map.tileheight)
                        self.all_sprites.add(platform)
            elif layer.name == 'coin':
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        coin = Coin(x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight)
                        self.all_sprites.add(coin)
                        self.coins.add(coin)
                    self.coins_amount = len(self.coins.sprites())  # новая строка

            elif layer.name == 'portal':
                for x, y, gid in layer:
                    tile = self.tmx_map.get_tile_image_by_gid(gid)
                    if tile:
                        portal = Portal(x * self.tmx_map.tilewidth, y * self.tmx_map.tileheight)
                        self.all_sprites.add(portal)
                        self.portals.add(portal)

    def run(self):
        self.is_running = True
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pg.quit()
        quit()

    def event(self):
        for event in pg.event.get():
            keys = pg.key.get_pressed()
            if event.type == pg.QUIT:
                self.is_running = False

            if self.mode == 'game over':
                if event.type == pg.KEYDOWN:
                    self.setup()

            if keys[pg.K_LSHIFT]:
                self.fireball = Ball(self.player.rect, self.player.direction)
                self.fireballs.add(self.fireball)
                self.all_sprites.add(self.fireball)

        collisions = pg.sprite.groupcollide(self.fireballs, self.enemies, True, True)
        collisions = pg.sprite.groupcollide(self.fireballs, self.platforms, True, False)

    def update(self):
        if self.player.hp <= 0:
            self.mode = 'game over'
            return

        for enemy in self.enemies.sprites():
            enemy.update(self.platforms)
            if pg.sprite.collide_mask(self.player, enemy):
                self.player.get_damage()

        for coin in self.coins.sprites():
            #coin.update(self.platforms)
            if pg.sprite.collide_mask(self.player, coin):
                coin.kill()
                self.money += 1

        hits = pg.sprite.spritecollide(self.player, self.portals, False, pg.sprite.collide_mask)
        for hit in hits:
            self.level += 1
            if self.level == 3:
                quit()
            self.setup()

        self.player.update(self.platforms)

        self.coins.update()

        self.portals.update()

        self.fireballs.update()

        self.camera_x = self.player.rect.x - SCREEN_WIDTH // 2
        self.camera_y = self.player.rect.y - SCREEN_HEIGHT // 2

        self.camera_x = max(0, min(self.camera_x, self.map_pixel_width - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, self.map_pixel_height - SCREEN_HEIGHT))

    def draw(self):
        self.screen.fill('light blue')

        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))


        pg.draw.rect(self.screen, "black", (21, 19, self.player.hp * 10, 22))
        pg.draw.rect(self.screen, "red", (20, 20, self.player.hp * 10, 20))

        text_money = font.render(f'Количество монет: {self.money}', True, (0, 0, 0))
        text_money_rect = text_money.get_rect(center=(SCREEN_WIDTH // 2, 15))
        self.screen.blit(text_money, text_money_rect)

        if self.mode == 'game over':
            text = font.render('Вы проиграли', True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)

        pg.display.flip()


if __name__ == "__main__":
    game = Game()
