import numpy as np
from itertools import product
import pygame
import base64
import io
import argparse

parser = argparse.ArgumentParser(description="Play some Minesweeper!")
parser.add_argument("-a", "--atlas" , help="Set Atlas")
parser.add_argument("-x", "--width" , help="Set Board Width")
parser.add_argument("-y", "--height", help="Set Board Height")
parser.add_argument("-z", "--zoom"  , help="Set Board Scale")
parser.add_argument("-d", "--dist"  , help="Set Bomb Distribution")
parser.add_argument("-f", "--fps"   , help="Set Frames Per Second")

args = parser.parse_args()

atlases = [
    ["iVBORw0KGgoAAAANSUhEUgAAAMAAAAAQCAYAAABA4nAoAAACH0lEQVRoge2aUZaCMAxFg8eF4SLIzpxFtIuQneGHpw7WSfpIq40O90eRpi2YvKSFYVmWhYzEGOkyz1bzJvycz2ZbD/Pf6cvRarh2ntM4midwmecqeyte5r/b97W/B0CMcfPA74CZKYRQbOd1/ju+MWeAj4D59gkEUKsuOLJ6PkxKR6zbohNh/hWDEKanY4mIjE9EkzIHLghRmOTxGRxfE8SSsOXZ4gCN+EbSTWBm8TvQCeZMQDeb2hecH22jd1B/Xa+i5PyvBsnqeRt3GSCEIDo5VA41cpDabnKlhxxfuzZwQqjal9BUHkFTetFGyywb/5Bc6aXgcBcA6ULT5tQwDE/n1SAIodp7reZqebPjEncB0IQUIEZPrjR/IFd+OEikwVWVjOpx+g3JDNJ6AM0MUjlkyQxr9dfE7zSOd6WXFN/tGmBd5xPdlD9Xf6mtSAjUq2LmyHbndwy6UJbovU7IcZMBUmQjjo1si/bir1rf5Pj5Nab7wixmAUnZ0XWBpu5bHT9Xeqvjo+pP9Kj60hogf27gJgBas75x6LOE6jG/UPG/HXcBoO0CpfMa2g4SYn9rK/+2JY6knR8xMDpvcdaWN2talDpb1D8HfdDpZg2Q0NS6FBz/gs7ln1YmIQtcyyIYBXklIm/jMgOsP/OAKClBi1LH2kV1yfMi50afB9Tu/RO1dXDLf7n1vaAj0ee/Ffnp89/px8G785RUwPv8d3xzBbSmLlijvxKAAAAAAElFTkSuQmCC", 16],
    ["iVBORw0KGgoAAAANSUhEUgAAAMAAAAAQCAYAAABA4nAoAAACIElEQVRoge2aUZaCMAxFg8eF4SLaRYw7C4uQneGHpw7WSfpIq40O90eRpi2YvKSFgYgWMhJCoNM4Ws2b8HM+m209zH+nL0er4dp5LvNsnsBpHKvsrXiZ/27f1/4eACGEzQO/A2amGGOxndf57/jGnAE+AubbJxBArbrgwOr5OCkdsW6LToT5VwxinJ6OJQIyPhFNyhy4IERxksdncHxNEEvClmeLAzTiG0k3gZnF70AnmDMB3WxqX3B+tI3eQf11vYqS878aJKvnbdxlgBij6ORQOdTIQWq7yZUecnzt2sAJoWpfQlN5BE3pRRsts2z8Q3Kll4LDXQCkCx2GgYiIlmV5Oq8GQYzV3ms1V8ubHZe4C4AmpAAxenKl+QO58sNBIg2uqmRQj9NvSGaQ1gNoZpDKIUtmWKu/Jn6Xeb4rvaT4btcA6zqf6Kb8ufpLbUVipF4VMwe2O79j0IWyRO91Qo6bDJAiG3FsZFu0F3/V+ibHz68x3RdmMQtIyo6uCzR13+r4udJbHR9Vf6JH1ZfWAPlzAzcB0Jr1jUOfJVSP+YWK/+24CwBtFyid19B2kBD7W1v5ty1xJO38iIHReYuztrxZ06LU2aL+OeiDTjdrgISm1qXg+Bd0Lv+0MglZ4FoWwSjIKxF5G5cZYP2ZB0RJCVqUOtYuqkueFzk3+jygdu+fqK2DW/7Lre8FHYk+/63IT5//Tj8O3p2npALe57/jmyvcoCItbSShiAAAAABJRU5ErkJggg==", 16],
]

# --- Config ---
ZOOM = 4
DIST = 0.07
W, H = 25,25
FPS = 15
ATLAS_BASE64 = atlases[0][0]
ATLAS_SCALE  = atlases[0][1]

if args.atlas:
    ATLAS_BASE64 = atlases[int(args.atlas)][0]
    ATLAS_SCALE  = atlases[int(args.atlas)][1]
if args.width: W = int(args.width)
if args.height: H = int(args.height)
if args.zoom: ZOOM = int(args.zoom)
if args.dist: DIST = float(args.dist)
if args.fps: FPS = int(args.fps)
CELL_SIZE = ATLAS_SCALE * ZOOM
SCREEN_WIDTH = H * CELL_SIZE
SCREEN_HEIGHT = W * CELL_SIZE

class Board:
    def __init__(self, rows: int, cols: int, distribution: float):
        self.rows = rows
        self.cols = cols
        self.distribution = distribution
        self.square_dtype = np.dtype([('is_mine', bool), ('is_dug', bool), ('is_flagged', bool), ('adjacent_mines', int)])
        self.board_array = np.empty((rows, cols), dtype=self.square_dtype)
        self.board_array['is_mine'] = np.random.choice([True, False], size=(rows, cols), p=[distribution, 1 - distribution])
        self.board_array['is_dug'] = False
        self.board_array['is_flagged'] = False
        self.game_over = False
        self.game_won = False
        self._calculate_all_adjacent_mines()

    def _is_valid(self, r: int, c: int):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _count_adjacent_mines_for_square(self, r: int, c: int):
        mine_count = 0
        for dr, dc in product([-1, 0, 1], repeat=2):
            if dr == 0 and dc == 0: continue
            nr, nc = r + dr, c + dc
            if self._is_valid(nr, nc) and self.board_array[nr][nc]['is_mine']: mine_count += 1
        return mine_count

    def _calculate_all_adjacent_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board_array[r][c]['is_mine']:
                    self.board_array[r][c]['adjacent_mines'] = self._count_adjacent_mines_for_square(r, c)

    def _check_win_condition(self):
        total_squares = self.rows * self.cols
        mines = np.sum(self.board_array['is_mine'])
        dug_squares = np.sum(self.board_array['is_dug'])

        if dug_squares == (total_squares - mines):
            self.game_won = True

    def dig(self, r: int, c: int):
        if self.game_over or self.game_won: return
        if not self._is_valid(r, c): return
        if self.board_array[r][c]['is_dug']: return
        if self.board_array[r][c]['is_flagged']: return

        is_first_click = not self.board_array['is_dug'].any()

        if self.board_array[r][c]['is_mine']:
            if is_first_click:
                self.board_array[r][c]['is_mine'] = False
                self._calculate_all_adjacent_mines()
            else:
                self.game_over = True
                self.board_array[r][c]['is_dug'] = True
                return

        self.board_array[r][c]['is_dug'] = True

        adjacent_mines = self.board_array[r][c]['adjacent_mines']

        if adjacent_mines == 0:
            for dr, dc in product([-1, 0, 1], repeat=2):
                if dr == 0 and dc == 0: continue
                self.dig(r + dr, c + dc)

        self._check_win_condition()

    def toggle_flag(self, r: int, c: int):
        if self.game_over or self.game_won: return
        if not self._is_valid(r, c): return
        if self.board_array[r][c]['is_dug']: return
        self.board_array[r][c]['is_flagged'] = not self.board_array[r][c]['is_flagged']

ATLAS_IMAGE = None

def load_atlas_from_base64():
    global ATLAS_IMAGE

    if ATLAS_IMAGE is None:
        atlas_bytes = base64.b64decode(ATLAS_BASE64)
        atlas_file = io.BytesIO(atlas_bytes)
        ATLAS_IMAGE = pygame.image.load(atlas_file).convert_alpha()

def get_texture_from_atlas(original_rect_width: int, original_rect_height: int, offset_x: int, offset_y: int) -> pygame.Surface:

    load_atlas_from_base64()

    x = offset_x * original_rect_width
    y = offset_y * original_rect_height

    try:
        texture = ATLAS_IMAGE.subsurface(pygame.Rect(x, y, original_rect_width, original_rect_height))
        scaled_texture = pygame.transform.scale( texture, (original_rect_width * ZOOM, original_rect_height * ZOOM))
        return scaled_texture
    except ValueError:
        raise Exception("Invalid texture atlas offset.")

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Minesweeper")
clock = pygame.time.Clock()
font = pygame.font.Font(None, SCREEN_WIDTH//10)

game_board = Board(W, H, DIST)

def draw_board(screen: pygame.Surface, board_obj: Board):
    for r in range(board_obj.rows):
        for c in range(board_obj.cols):
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            current_square = board_obj.board_array[r][c]
            dug_empty_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 1,0)

            if board_obj.game_over:
                if current_square['is_mine']:
                    mine_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 2,0)
                    screen.blit(mine_texture, rect.topleft)
                elif current_square['is_flagged'] and not current_square['is_mine']:
                    flag_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 3,0)
                    screen.blit(flag_texture, rect.topleft)
                elif current_square['is_dug']:
                    screen.blit(dug_empty_texture, rect.topleft)
                    adjacent_mines = current_square['adjacent_mines']
                    if adjacent_mines > 0:
                        number_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, [(i, 0) for i in range(4, 12)][adjacent_mines - 1][0], [(i, 0) for i in range(4, 12)][adjacent_mines - 1][1])
                        screen.blit(number_texture, rect.topleft)
                else:
                    undug_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 0,0)
                    screen.blit(undug_texture, rect.topleft)
            else:
                if current_square['is_dug']:
                    if current_square['is_mine']:
                        mine_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 2,0)
                        screen.blit(mine_texture, rect.topleft)
                    else:
                        screen.blit(dug_empty_texture, rect.topleft)
                        adjacent_mines = current_square['adjacent_mines']
                        if adjacent_mines > 0:
                            number_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, [(i, 0) for i in range(4, 12)][adjacent_mines - 1][0], [(i, 0) for i in range(4, 12)][adjacent_mines - 1][1])
                            screen.blit(number_texture, rect.topleft)
                elif current_square['is_flagged']:
                    flag_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 3,0)
                    screen.blit(flag_texture, rect.topleft)
                else:
                    undug_texture = get_texture_from_atlas(ATLAS_SCALE, ATLAS_SCALE, 0,0)
                    screen.blit(undug_texture, rect.topleft)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            clicked_col = (mouse_x // CELL_SIZE)
            clicked_row = (mouse_y // CELL_SIZE)

            if event.button == 1:
                game_board.dig(clicked_row, clicked_col)
            elif event.button == 3:
                game_board.toggle_flag(clicked_row, clicked_col)

    screen.fill("#FFFFFF")
    draw_board(screen, game_board)
    if game_board.game_over:
        game_over_text = font.render("You Lose!", True, "#AA0000")
        game_over_text_shadow = font.render("You Lose!", True, "#000000")
        text_rect_shadow = game_over_text_shadow.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.95))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(game_over_text_shadow, text_rect_shadow)
        screen.blit(game_over_text, text_rect)
    if game_board.game_won:
        game_won_text = font.render("You Win!", True, "#00AA00")
        game_won_text_shadow = font.render("You Win!", True, "#000000")
        text_rect_shadow = game_won_text_shadow.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.95))
        text_rect = game_won_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(game_won_text_shadow, text_rect_shadow)
        screen.blit(game_won_text, text_rect)
    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()