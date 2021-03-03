import random
from pprint import pprint

import pygame
import os
import sys

pygame.init()
size = width, height = 1000, 800
screen = pygame.display.set_mode(size)
BG = (206,249,101)
screen.fill(BG)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Border(pygame.sprite.Sprite):
    # строго вертикальный или строго горизонтальный отрезок
    def __init__(self, x1, y1, x2, y2):
        super().__init__(all_sprites)
        if x1 == x2:  # вертикальная стенка
            self.add(vertical_borders)
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)
        else:  # горизонтальная стенка
            self.add(horizontal_borders)
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


class SubTile(pygame.sprite.Sprite):
    def __init__(self, img, x, y, w, h):
        super().__init__(all_sprites, up_layers_group)
        self.image = img
        self.rect = pygame.Rect(x, y, w, h)


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type != 'empty':
            params = tiles_group, all_sprites, rigid_group
        else:
            params = tiles_group, all_sprites
        super().__init__(*params)
        self.type = tile_type

        if self.type == 'empty':
            self.image = pygame.transform.rotate(tile_images[tile_type],
                                                 random.choice([0, 90, 180, 270]))
        else:
            self.image = tile_images[tile_type]

        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        if self.type != 'empty' and self.type != 'tree':
            self.mask = pygame.mask.from_surface(self.image)
            self.cropped = self.image.subsurface(0, 0, self.rect.width, self.rect.height // 2)
            SubTile(self.cropped, self.rect.x, self.rect.y, self.rect.width, self.rect.height // 2)
        elif self.type == 'tree':
            s = pygame.Surface((self.rect.width,
                                self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, pygame.Color("red"),
                             (self.rect.width // 3, self.rect.height // 2,
                              self.rect.width // 3, self.rect.height // 2))
            self.mask = pygame.mask.from_surface(s)
            self.cropped = self.image.subsurface(0, 0, self.rect.width, self.rect.height * 3 // 4)
            SubTile(self.cropped, self.rect.x, self.rect.y, self.rect.width, self.rect.height * 3 // 4)

    def update(self, img=None):
        if self.type == 'campfire':
            self.image = img


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, pygame.Color("red"),
                         (0, self.rect.height // 2, self.rect.width, 5))
        self.mask = pygame.mask.from_surface(s)

class Wolf(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(wolf_group, all_sprites)
        self.image = wolf_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.mask = pygame.mask.from_surface(self.image)


def generate_level(level):
    new_player, x, y = None, None, None
    # Сначала заполняем поле травой
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.' or level[y][x] == '_':
                Tile('empty', x, y)
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Tile('empty', x, y)
                Tile('well', x, y)

            elif level[y][x] == 'X':
                Tile('empty', x, y)
                Tile('campfire', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
            elif level[y][x] == 'T':
                Tile('empty', x, y)
                Tile('tree', x, y)
            elif level[y][x] == 'H':
                Tile('empty', x, y)
                Tile('house', x, y)

    # вернем игрока, а также размер поля в клетках
    return new_player, x, y


def terminate():
    pygame.quit()
    sys.exit()


def process_large(lvl, shape, symb):
    # Если мы ввели размерность меньше или равно 1х1 - возвращаемся
    if shape[0] + shape[1] < 3:
        return lvl
    # Ищем различные варианты координат клеток вокруг заданной
    inds = []
    for i in range(shape[0]):
        for j in range(shape[1]):
            if i == j == 0:
                continue
            inds.append((i, j))

    pass_inds = []
    for y in range(len(lvl)):
        for x in range(len(lvl[y])):
            if lvl[y][x] == symb:
                if all(y + add_1st < len(lvl) and x + add_2nd < len(lvl[y])
                       for add_1st, add_2nd in inds) and \
                        all(all(x == '.' for x in lvl[y + add_1st][x + add_2nd])
                            for add_1st, add_2nd in inds):
                    for add_1st, add_2nd in inds:
                        pass_inds.append((y + add_1st, x + add_2nd))
    if pass_inds:
        for i in range(len(lvl)):
            for j in range(len(lvl[i])):
                if (i, j) in pass_inds:
                    lvl[i] = lvl[i][:j] + '_' + lvl[i][j + 1:]
    for i in range(len(lvl)):
        for j in range(len(lvl[i])):
            if lvl[i][j] == symb and lvl[i][j + 1] != '_':
                lvl[i] = lvl[i][:j] + '.' + lvl[i][j + 1:]
    return lvl


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    lvl = list(map(lambda x: x.ljust(max_width, '.'), level_map))
    # Обработка больших объектов
    lvl = process_large(lvl, (2, 2), 'T')
    lvl = process_large(lvl, (3, 3), 'H')
    pprint(lvl)
    return lvl


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    # fon = pygame.transform.scale(load_image('fon.jpg'), (width, height))
    # screen.blit(BG, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)





if __name__ == '__main__':
    FPS = 60
    tile_images = {
        'well': load_image('well.png'),
        'empty': load_image('grass1.png'),
        'tree': load_image('Btree.png'),
        'campfire': load_image('anim/images/cf1.png'),
        'house': load_image('house_1.png')
    }
    anim_folder = 'anim/images/'
    player_image = load_image(anim_folder + 'pixman_d1.png')
    wolf_image = load_image(anim_folder + 'wolfs_d1.png')
    up_images = list(map(load_image, [anim_folder + 'pixman_t1.png',
                                      anim_folder + 'pixman_t2.png',
                                      anim_folder + 'pixman_t3.png',
                                      anim_folder + 'pixman_t4.png']))
    dw_images = list(map(load_image, [anim_folder + 'pixman_d1.png',
                                      anim_folder + 'pixman_d2.png',
                                      anim_folder + 'pixman_d3.png',
                                      anim_folder + 'pixman_d4.png']))
    rg_images = list(map(load_image, [anim_folder + 'pixman_r1.png',
                                      anim_folder + 'pixman_r2.png',
                                      anim_folder + 'pixman_r3.png',
                                      anim_folder + 'pixman_r4.png']))
    lf_images = list(map(load_image, [anim_folder + 'pixman_l1.png',
                                      anim_folder + 'pixman_l2.png',
                                      anim_folder + 'pixman_l3.png',
                                      anim_folder + 'pixman_l4.png']))
    cf_images = list(map(load_image, map(lambda x: anim_folder + x, ['cf1.png', 'cf2.png',
                                                                     'cf3.png', 'cf4.png'])))
    lcounter, rcounter, ucounter, dcounter = 0, 0, 0, 0
    tile_width = tile_height = 96
    camera = Camera()

    # группы спрайтов
    all_sprites = pygame.sprite.Group()
    tiles_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    rigid_group = pygame.sprite.Group()
    up_layers_group = pygame.sprite.Group()
    wolf_group = pygame.sprite.Group()

    clock = pygame.time.Clock()
    start_screen()
    player, level_x, level_y = generate_level(load_level('map.txt'))
    #
    horizontal_borders = pygame.sprite.Group()
    vertical_borders = pygame.sprite.Group()

    Border(0, 0, (level_x + 1) * tile_width, 0)
    Border(0, (level_y + 1) * tile_height, (level_x + 1) * tile_width, (level_y + 1) * tile_height)
    Border(0, 0, 0, (level_y + 1) * tile_height)
    Border((level_x + 1) * tile_width, 0, (level_x + 1) * tile_width, (level_y + 1) * tile_height)

    wolf_start_pos = random.choice([(1, random.randint(1, level_y - 1)),
                              (level_x - 1, random.randint(1, level_y - 1))])
    wolf = Wolf(*wolf_start_pos)

    #
    motion = 'stop'
    step = 4
    ctr, fire_ctr = 0, 0
    transi_step = 6
    cfcounter = 0
    stop = 'disable'
    prev_x, prev_y = player.rect.x, player.rect.y

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    motion = 'left'
                    if stop == motion:
                        stop = 'disable'
                if event.key == pygame.K_RIGHT:
                    motion = 'right'
                    if stop == motion:
                        stop = 'disable'
                if event.key == pygame.K_UP:
                    motion = 'up'
                    if stop == motion:
                        stop = 'disable'
                if event.key == pygame.K_DOWN:
                    motion = 'down'
                    if stop == motion:
                        stop = 'disable'
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    stop = 'left'
                if event.key == pygame.K_RIGHT:
                    stop = 'right'
                if event.key == pygame.K_UP:
                    stop = 'up'
                if event.key == pygame.K_DOWN:
                    stop = 'down'
        if motion == 'left' and stop != 'left':
            ctr = (ctr + 1) % transi_step
            if ctr == 0:
                player.image = lf_images[lcounter]
                lcounter = (lcounter + 1) % len(lf_images)
            if not pygame.sprite.spritecollideany(player, vertical_borders) and \
                    not any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                prev_x, prev_y = player.rect.x, player.rect.y
                player.rect.x -= step
                if pygame.sprite.spritecollideany(player, vertical_borders) or \
                        any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                    player.rect.x, player.rect.y = prev_x, prev_y
            else:
                motion = 'stop'

        if motion == 'right' and stop != 'right':
            ctr = (ctr + 1) % transi_step
            if ctr == 0:
                player.image = rg_images[rcounter]
                rcounter = (rcounter + 1) % len(rg_images)
            if not pygame.sprite.spritecollideany(player, vertical_borders) and \
                    not any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                prev_x, prev_y = player.rect.x, player.rect.y
                player.rect.x += step
                if pygame.sprite.spritecollideany(player, vertical_borders) or \
                        any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                    player.rect.x, player.rect.y = prev_x, prev_y
            else:
                motion = 'stop'

        if motion == 'up' and stop != 'up':
            ctr = (ctr + 1) % transi_step
            if ctr == 0:
                player.image = up_images[ucounter]
                ucounter = (ucounter + 1) % len(up_images)
            if not pygame.sprite.spritecollideany(player, horizontal_borders) and \
                    not any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                prev_x, prev_y = player.rect.x, player.rect.y
                player.rect.y -= step
                if pygame.sprite.spritecollideany(player, horizontal_borders) or \
                        any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                    player.rect.x, player.rect.y = prev_x, prev_y
            else:
                motion = 'stop'

        if motion == 'down' and stop != 'down':
            ctr = (ctr + 1) % transi_step
            if ctr == 0:
                player.image = dw_images[dcounter]
                dcounter = (dcounter + 1) % len(dw_images)
            if not pygame.sprite.spritecollideany(player, horizontal_borders) and \
                    not any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                prev_x, prev_y = player.rect.x, player.rect.y
                player.rect.y += step
                if pygame.sprite.spritecollideany(player, horizontal_borders) or \
                        any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                    player.rect.x, player.rect.y = prev_x, prev_y
            else:
                motion = 'stop'

        # в главном игровом цикле
        screen.fill(BG)
        camera.update(player)
        # # обновляем положение всех спрайтов
        for sprite in all_sprites:
            camera.apply(sprite)
        all_sprites.draw(screen)

        fire_ctr = (fire_ctr + 1) % transi_step
        if fire_ctr == 0:
            all_sprites.update(cf_images[cfcounter])
            cfcounter = (cfcounter + 1) % len(cf_images)

        player_group.draw(screen)
        wolf_group.draw(screen)
        up_layers_group.draw(screen)


        clock.tick(FPS)
        pygame.display.flip()
