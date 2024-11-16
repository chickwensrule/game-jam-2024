import pyxel
import json

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

# check bounds
def pressed(bounds):
    return bounds[0] < pyxel.mouse_x < bounds[1] and bounds[2] < pyxel.mouse_y < bounds[3]

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
        self.character_selection_button = (0, 0, 0, 0)
        self.game_start_button = (0, 0, 0, 0)

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

        pyxel.run(self.update, self.draw)

    def update_menu(self):

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):

            if pressed(self.character_selection_button):
                self.page = Page.CHARACTER_SELECTION
            elif pressed(self.game_start_button):

                # disable mouse
                pyxel.mouse(False)

                # set page
                self.page = Page.GAME

    def draw_menu(self):

        # title
        center_aligned_text(CENTER_X, CENTER_Y-20, "Game page", pyxel.COLOR_WHITE)

        # character button
        self.character_selection_button = center_aligned_rect(CENTER_X, CENTER_Y, 90, 18, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y, "Character Selection", pyxel.COLOR_WHITE)

        # game button
        self.game_start_button = center_aligned_rect(CENTER_X, CENTER_Y+24, 60, 18, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y+24, "Start Game", pyxel.COLOR_WHITE)

    def update_character_selection(self):
        pass

    def draw_character_selection(self):
        pass

    def update_game(self):

        # move characters around
        character_1_speed = self.characters_info["character_1"]["speed"]
        character_2_speed = self.characters_info["character_2"]["speed"]

        if pyxel.btn(pyxel.KEY_W):
            self.character_1_y -= character_1_speed
        if pyxel.btn(pyxel.KEY_A):
            self.character_1_x -= character_1_speed
        if pyxel.btn(pyxel.KEY_S):
            self.character_1_y += character_1_speed
        if pyxel.btn(pyxel.KEY_D):
            self.character_1_x += character_1_speed

        if pyxel.btn(pyxel.KEY_UP):
            self.character_2_y -= character_2_speed
        if pyxel.btn(pyxel.KEY_LEFT):
            self.character_2_x -= character_2_speed
        if pyxel.btn(pyxel.KEY_DOWN):
            self.character_2_y += character_2_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.character_2_x += character_2_speed

        # prevent the characters from going out of bounds
        self.character_1_x = max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, self.character_1_x))
        self.character_1_y = max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, self.character_1_y))

        self.character_2_x = max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, self.character_2_x))
        self.character_2_y = max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, self.character_2_y))

    def draw_game(self):
        # pyxel.rect(self.character_1_x, self.character_1_y, 8, 8, pyxel.COLOR_LIGHT_BLUE)
        # pyxel.rect(self.character_2_x, self.character_2_y, 8, 8, pyxel.COLOR_RED)

        pyxel.blt(
            self.character_1_x, self.character_1_y,
            0, 0, 0, # image bank 0 @ u=0, v=0
            CHARACTER_SIZE, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        pyxel.blt(
            self.character_2_x, self.character_2_y,
            1, 0, 0, # image bank 0 @ u=0, v=0
            CHARACTER_SIZE, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

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
        