import pyxel
import json
from datetime import datetime

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 200

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

CHARACTER_SIZE = 32

# make centered rectangle on the coords given
def center_aligned_rect(center_x, center_y, w, h, color):
    left = center_x - w // 2
    top = center_y - h // 2

    pyxel.rect(left, top, w, h, color)

    # return bounds (useful for buttons)
    right = left + w
    bottom = top + h

    return left, right, top, bottom

# make centered text on the coords given
def center_aligned_text(center_x, center_y, text, color):
    text_width = pyxel.FONT_WIDTH * len(text)
    text_height = pyxel.FONT_HEIGHT

    left = center_x - text_width // 2
    top = center_y - text_height // 2

    pyxel.text(left, top, text, color)

# check button bounds
def pressed(button_bounds):
    return button_bounds[0] < pyxel.mouse_x < button_bounds[1] and button_bounds[2] < pyxel.mouse_y < button_bounds[3]

# check if collided with a barrier
def check_barrier(x, y, left, right, top, bottom):
    return not (
        x + CHARACTER_SIZE <= left or  # left
        x >= right or                 # right
        y + CHARACTER_SIZE <= top or # above
        y >= bottom # below
    )

# check all barrier collisions
def check_collisions(x, y, new_x, new_y, barriers_bounds):
    for l, r, t, b in barriers_bounds:
        if check_barrier(new_x, new_y, l, r, t, b):
            return x, y # collision

    # bounded to walls
    return max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, new_x)), max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, new_y))

# enum class
class Page():
    MENU = 1
    CHARACTER_SELECTION = 2
    GAME = 3

# main class
class App():
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Picture Battles!")
        pyxel.mouse(True)

        self.page = Page.MENU

        # button bounds
        self.character_selection_button_bounds = (0, 0, 0, 0) # l, r, t, b
        self.game_start_button_bounds = (0, 0, 0, 0) # l, r, t, b

        # setup characters
        self.characters_info = {}
        with open("characters/info.json", 'r') as f:
            self.characters_info = json.load(f)

        self.character_1_x = 0
        self.character_1_y = CENTER_Y - CHARACTER_SIZE // 2

        self.character_2_x = SCREEN_WIDTH - CHARACTER_SIZE
        self.character_2_y = CENTER_Y - CHARACTER_SIZE // 2

        pyxel.images[0].load(0, 0, self.characters_info["character_1"]["icon"])
        pyxel.images[1].load(0, 0, self.characters_info["character_2"]["icon"])

        # barriers
        self.barriers = []
        self.barriers_bounds = []

        pyxel.run(self.update, self.draw)

    def update_menu(self):

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):

            if pressed(self.character_selection_button_bounds):
                self.page = Page.CHARACTER_SELECTION
            elif pressed(self.game_start_button_bounds):

                # disable mouse
                pyxel.mouse(False)

                # set page
                self.page = Page.GAME

    def draw_menu(self):

        # title
        center_aligned_text(CENTER_X, CENTER_Y-20, "Game page", pyxel.COLOR_WHITE)

        # character button
        self.character_selection_button_bounds = center_aligned_rect(CENTER_X, CENTER_Y, 90, 18, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y, "Character Selection", pyxel.COLOR_WHITE)

        # game button
        self.game_start_button_bounds = center_aligned_rect(CENTER_X, CENTER_Y+24, 60, 18, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y+24, "Start Game", pyxel.COLOR_WHITE)

    def update_character_selection(self):
        pass

    def draw_character_selection(self):
        pass

    def update_game(self):

        # new pos
        character_1_new_x = self.character_1_x
        character_1_new_y = self.character_1_y
        character_2_new_x = self.character_2_x
        character_2_new_y = self.character_2_y

        # move characters around
        character_1_speed = self.characters_info["character_1"]["speed"]
        character_2_speed = self.characters_info["character_2"]["speed"]

        if pyxel.btn(pyxel.KEY_W):
            character_1_new_y -= character_1_speed
        if pyxel.btn(pyxel.KEY_A):
            character_1_new_x -= character_1_speed
        if pyxel.btn(pyxel.KEY_S):
            character_1_new_y += character_1_speed
        if pyxel.btn(pyxel.KEY_D):
            character_1_new_x += character_1_speed

        if pyxel.btn(pyxel.KEY_UP):
            character_2_new_y -= character_2_speed
        if pyxel.btn(pyxel.KEY_LEFT):
            character_2_new_x -= character_2_speed
        if pyxel.btn(pyxel.KEY_DOWN):
            character_2_new_y += character_2_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            character_2_new_x += character_2_speed

        # update based on collisions
        self.character_1_x, self.character_1_y = check_collisions(
            self.character_1_x, self.character_1_y,
            character_1_new_x, character_1_new_y,
            self.barriers_bounds
        )

        self.character_2_x, self.character_2_y = check_collisions(
            self.character_2_x, self.character_2_y,
            character_2_new_x, character_2_new_y,
            self.barriers_bounds
        )

    def draw_game(self):

        # draw characters
        pyxel.blt(
            self.character_1_x, self.character_1_y,
            0, 0, 0, # image bank 0 @ u=0, v=0
            CHARACTER_SIZE, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        pyxel.blt(
            self.character_2_x, self.character_2_y,
            1, 0, 0, # image bank 1 @ u=0, v=0
            CHARACTER_SIZE, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        self.barriers_bounds = [center_aligned_rect(CENTER_X, CENTER_Y, 50, 50, pyxel.COLOR_BROWN)]

    def update(self):
        if self.page == Page.MENU:
            self.update_menu()
        elif self.page == Page.CHARACTER_SELECTION:
            self.update_character_selection()
        elif self.page == Page.GAME:
            self.update_game()

    def draw(self):
        pyxel.cls(0)

        if self.page == Page.MENU:
            self.draw_menu()
        if self.page == Page.CHARACTER_SELECTION:
            self.draw_character_selection()
        elif self.page == Page.GAME:
            self.draw_game()
        