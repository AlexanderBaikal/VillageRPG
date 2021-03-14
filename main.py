import random
from pprint import pprint

import pygame
import os
import sys

pygame.init()
size = width, height = 1000, 800
screen = pygame.display.set_mode(size)
BG = (206, 249, 101)
screen.fill(BG)


# Загрузка изображения
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


# Границы поля
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


# Верхний слой изображения для имитации 3D пространства
# (Перекрывает игрока, если игрок находится "за объектом")
class SubTile(pygame.sprite.Sprite):
    def __init__(self, img, x, y, w, h):
        super().__init__(all_sprites, up_layers_group)
        self.image = img
        self.rect = pygame.Rect(x, y, w, h)


# Фрагмент (клетка) поля
class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type != 'empty':  # Если тип - пустая клетка
            params = tiles_group, all_sprites, rigid_group
        else:
            params = tiles_group, all_sprites
        super().__init__(*params)
        self.type = tile_type

        if self.type == 'empty':  # Если тип - пустая клетка
            self.image = pygame.transform.rotate(tile_images[tile_type],
                                                 random.choice([0, 90, 180, 270]))
        else:
            self.image = tile_images[tile_type]

        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        if self.type != 'empty' and self.type != 'tree':  # Если тип - пустая клетка или дерево
            # Маска, по которой происходит столкновение с игроком
            self.mask = pygame.mask.from_surface(self.image)
            self.cropped = self.image.subsurface(0, 0, self.rect.width, self.rect.height // 2)
            # Верхний слой объекта
            SubTile(self.cropped, self.rect.x, self.rect.y, self.rect.width, self.rect.height // 2)
        elif self.type == 'tree':  # Если тип - дерево
            s = pygame.Surface((self.rect.width,
                                self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, pygame.Color("red"),
                             (self.rect.width // 3, self.rect.height // 2,
                              self.rect.width // 3, self.rect.height // 2))
            # Маска, по которой происходит столкновение с игроком
            self.mask = pygame.mask.from_surface(s)
            self.cropped = self.image.subsurface(0, 0, self.rect.width, self.rect.height * 3 // 4)
            # Верхний слой объекта
            SubTile(self.cropped, self.rect.x, self.rect.y, self.rect.width, self.rect.height * 3 // 4)

    def update(self, img=None):
        # Анимация костра
        if self.type == 'campfire':
            self.image = img


# Игрок
class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        # По умолчанию у игрока нет ранений
        self.blood = False
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, pygame.Color("red"),
                         (0, self.rect.height // 2, self.rect.width, 5))
        # Маска, по которой происходит столкновение с объектами
        self.mask = pygame.mask.from_surface(s)


# Волк
class Wolf(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(wolf_group, all_sprites)
        self.image = wolf_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        # Маска, по которой происходит столкновение с объектами
        self.mask = pygame.mask.from_surface(self.image)


# Генерация уровня
def generate_level(level):
    new_player, x, y = None, None, None
    # Сначала заполняем поле травой
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.' or level[y][x] == '_':
                Tile('empty', x, y)
    for y in range(len(level)):
        for x in range(len(level[y])):
            # Обработчики #X@TH символов
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


# Создает объект произвольного размера (используется, если
# нужно разместить дом размером 3x3 клетки на поле)
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
    # Если в окрестности нет других объектов, то размещаем на ней наш объект
    pass_inds = []
    for y in range(len(lvl)):
        for x in range(len(lvl[y])):
            if lvl[y][x] == symb:
                # Проверяем, что все клетки в крестности - пустые ( . )
                if all(y + add_1st < len(lvl) and x + add_2nd < len(lvl[y])
                       for add_1st, add_2nd in inds) and \
                        all(all(x == '.' for x in lvl[y + add_1st][x + add_2nd])
                            for add_1st, add_2nd in inds):
                    for add_1st, add_2nd in inds:
                        pass_inds.append((y + add_1st, x + add_2nd))
    # Если все клетки оказались пустыми, то заполняем их символами _
    if pass_inds:
        for i in range(len(lvl)):
            for j in range(len(lvl[i])):
                if (i, j) in pass_inds:
                    lvl[i] = lvl[i][:j] + '_' + lvl[i][j + 1:]
    # Модифицируем уровень
    for i in range(len(lvl)):
        for j in range(len(lvl[i])):
            if lvl[i][j] == symb and lvl[i][j + 1] != '_':
                lvl[i] = lvl[i][:j] + '.' + lvl[i][j + 1:]
    return lvl


# Загружаем уровень
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
    # pprint(lvl) строка для отладки
    return lvl


# Заставка
def start_screen():
    intro_text = ["ЖИЗНЬ В ДЕРЕВНЕ", "",
                  "Правила игры",
                  "Перемещайтесь по полю,",
                  "но избегайте столкновения с волком"]

    # fon = pygame.transform.scale(load_image('fon.jpg'), (width, height))
    # screen.blit(BG, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('white'))
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


# Обработчик движений игрока
def motion_handler(motion_dir):
    global motion, ctr, lcounter, rcounter, dcounter, ucounter
    if motion == motion_dir and stop != motion_dir:
        ctr = (ctr + 1) % transi_step
        if ctr == 0:
            if motion_dir == 'left':
                player.image = lf_images[lcounter]
                lcounter = (lcounter + 1) % len(lf_images)
            elif motion_dir == 'right':
                player.image = rg_images[rcounter]
                rcounter = (rcounter + 1) % len(rg_images)
            elif motion_dir == 'up':
                player.image = up_images[ucounter]
                ucounter = (ucounter + 1) % len(up_images)
            elif motion_dir == 'down':
                player.image = dw_images[dcounter]
                dcounter = (dcounter + 1) % len(dw_images)
            if player.blood:
                player.image.blit(blood_img, (0, 0))

        if motion_dir == 'left' or motion_dir == 'right':
            borders = vertical_borders
        else:
            borders = horizontal_borders
        if not pygame.sprite.spritecollideany(player, borders) and \
                not any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
            prev_x, prev_y = player.rect.x, player.rect.y
            if motion_dir == 'left':
                player.rect.x -= step
            elif motion_dir == 'right':
                player.rect.x += step
            elif motion_dir == 'down':
                player.rect.y += step
            elif motion_dir == 'up':
                player.rect.y -= step
            if pygame.sprite.spritecollideany(player, borders) or \
                    any(pygame.sprite.collide_mask(player, spr) for spr in rigid_group.sprites()):
                player.rect.x, player.rect.y = prev_x, prev_y
        else:
            motion = 'stop'


# Изменение положения игрока
def change_player_position(events):
    global motion, stop, ctr, lcounter, rcounter, dcounter, ucounter
    for event in events:
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
    motion_handler('left')
    motion_handler('right')
    motion_handler('down')
    motion_handler('up')


# Обработчик движений волка
def wolf_motion_handler():
    global w_direct, w_ctr, wrcounter ,wlcounter, wucounter, wdcounter, w_prev_x, w_prev_y
    if w_direct == 'L' or w_direct == 'R':
        borders = vertical_borders
    else:
        borders = horizontal_borders
    if not pygame.sprite.spritecollideany(wolf, borders) and \
            not any(pygame.sprite.collide_mask(wolf, spr) for spr in rigid_group.sprites()):
        w_prev_x, w_prev_y = wolf.rect.x, wolf.rect.y

        if w_direct == 'L':
            wolf.rect.x -= step
        elif w_direct == 'R':
            wolf.rect.x += step
        elif w_direct == 'D':
            wolf.rect.y += step
        elif w_direct == 'U':
            wolf.rect.y -= step

        w_ctr = (w_ctr + 1) % transi_step
        if w_ctr == 0:
            if w_direct == 'R':
                wolf.image = wr_images[wrcounter]
                wrcounter = (wrcounter + 1) % len(wr_images)
            elif w_direct == 'L':
                wolf.image = wl_images[wlcounter]
                wlcounter = (wlcounter + 1) % len(wl_images)
            elif w_direct == 'D':
                wolf.image = wd_images[wdcounter]
                wdcounter = (wdcounter + 1) % len(wd_images)
            elif w_direct == 'U':
                wolf.image = wu_images[wucounter]
                wucounter = (wucounter + 1) % len(wu_images)
        if pygame.sprite.spritecollideany(wolf, borders) or \
                any(pygame.sprite.collide_mask(wolf, spr) for spr in rigid_group.sprites()):
            wolf.rect.x, wolf.rect.y = w_prev_x, w_prev_y
            if w_direct == 'R':
                w_direct = 'L'
            elif w_direct == 'L':
                w_direct = 'R'
            elif w_direct == 'D':
                w_direct = 'U'
            elif w_direct == 'U':
                w_direct = 'D'
        if pygame.sprite.collide_mask(wolf, player):
            player.blood = True


# Изменение положения волка
def change_wolf_position():
    global w_dir_ctr, w_transi_step, wrcounter, wlcounter, \
        wucounter, wdcounter, w_direct, w_ctr, wr_images
    w_dir_ctr = (w_dir_ctr + 1) % w_transi_step
    if w_dir_ctr == 0:
        w_direct = random.choice(['L', 'R', 'U', 'D'])
        w_transi_step = random.randint(50, 80)
        w_ctr = 0
    wolf_motion_handler()


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

    # Анимация игрока
    player_image = load_image(anim_folder + 'pixman_d1.png')
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
    # Анимация волка
    wolf_image = load_image(anim_folder + 'wolfs_d1.png')
    wl_images = list(map(load_image, [anim_folder + 'wolfs_l1.png',
                                      anim_folder + 'wolfs_l2.png',
                                      anim_folder + 'wolfs_l3.png'
                                      ]))
    wr_images = list(map(load_image, [anim_folder + 'wolfs_r1.png',
                                      anim_folder + 'wolfs_r2.png',
                                      anim_folder + 'wolfs_r3.png'
                                      ]))
    wu_images = list(map(load_image, [anim_folder + 'wolfs_u1.png',
                                      anim_folder + 'wolfs_u2.png',
                                      anim_folder + 'wolfs_u3.png'
                                      ]))
    wd_images = list(map(load_image, [anim_folder + 'wolfs_d1.png',
                                      anim_folder + 'wolfs_d2.png',
                                      anim_folder + 'wolfs_d3.png'
                                      ]))

    blood_img = load_image('blood.png')  # Ранения игрока
    tile_width = tile_height = 96  # Размер клетки (рх)
    camera = Camera()

    # группы спрайтов
    all_sprites = pygame.sprite.Group()
    tiles_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    rigid_group = pygame.sprite.Group()  # Твердые предметы
    up_layers_group = pygame.sprite.Group()
    wolf_group = pygame.sprite.Group()
    horizontal_borders = pygame.sprite.Group()
    vertical_borders = pygame.sprite.Group()

    clock = pygame.time.Clock()
    start_screen()
    player, level_x, level_y = generate_level(load_level('map.txt'))

    Border(0, 0, (level_x + 1) * tile_width, 0)
    Border(0, (level_y + 1) * tile_height, (level_x + 1) * tile_width, (level_y + 1) * tile_height)
    Border(0, 0, 0, (level_y + 1) * tile_height)
    Border((level_x + 1) * tile_width, 0, (level_x + 1) * tile_width, (level_y + 1) * tile_height)

    # Спавн волка
    while True:
        wolf_start_pos = random.choice([(1, random.randint(1, level_y - 1)),
                                        (level_x - 1, random.randint(1, level_y - 1))])
        wolf = Wolf(*wolf_start_pos)
        if not any(pygame.sprite.collide_mask(wolf, spr) for spr in rigid_group.sprites()):
            break
        else:
            wolf.kill()

    motion = 'stop'  # Направление игрока
    step = 4  # Шаг игрока
    ctr, w_ctr, w_dir_ctr, fire_ctr = 0, 0, 0, 0
    w_direct = 'D'  # Направление волка
    transi_step = 6  # Скорость игрока
    w_transi_step = 30  # Скорость волка
    cfcounter = 0  # Счетчик костра
    stop = 'disable'  # Остановить движение
    lcounter, rcounter, ucounter, dcounter = 0, 0, 0, 0  # Счетчик по направлениям для игрока
    wlcounter, wrcounter, wucounter, wdcounter = 0, 0, 0, 0  # Счетчик по направлениям для волка
    prev_x, prev_y = player.rect.x, player.rect.y  # Предыдущие координаты игрока
    # ( для блокировки движения в стену )

    # Главный игровой цикл
    while True:
        # Изменение положения игрока
        change_player_position(pygame.event.get())
        # Изменение положения волка
        change_wolf_position()
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
