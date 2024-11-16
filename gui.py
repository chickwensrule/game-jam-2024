import pyxel

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 200

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# make centered rectangle on the coords given
def center_aligned_rect(center_x, center_y, w, h, color):
    left = center_x - w // 2
    top = center_y - h // 2

    pyxel.rect(left, top, w, h, color)

    # return bounds if it's a button
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
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="hi")
        pyxel.mouse(True)

        self.page = Page.MENU

        # bounds
        self.character_selection_button = (0, 0, 0, 0)
        self.game_start_button = (0, 0, 0, 0)

        pyxel.run(self.update, self.draw)

    def update_menu(self):

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if pressed(self.character_selection_button):
                self.page = Page.CHARACTER_SELECTION  # Switch to the game page
            elif pressed(self.game_start_button):
                self.page = Page.GAME  # Switch to the game page

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
        pass

    def draw_game(self):
        pass

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
        