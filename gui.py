import pyxel
import json
import random
from time import time
import textwrap
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget
from character import Character
from threading import Thread

SCREEN_WIDTH = 300
SCREEN_HEIGHT = 180

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

CHARACTER_SIZE = 32

def open_file_picker():
    app = QApplication([])
    window = QWidget()
    window.hide() # hide
    
    # open file dialog
    fp, _ = QFileDialog.getOpenFileName(window, "JPEG Only", "", "JPEG Files (*.jpeg *.jpg)")

    app.quit()
    return fp

def update_json_file(new_info):
    with open("characters/info.json", 'w') as f:
        json.dump(new_info)

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

def barrier_overlap(l0, r0, t0, b0, barriers):
    for l1, r1, t1, b1, _ in barriers:
        if l0 == l1 and r0 == r1 and t0 == t1 and b0 == b1:
            return True
        
    return False

# check all barrier collisions
def check_collisions(x, y, new_x, new_y, barriers):
    final_x = new_x
    final_y = new_y

    for l, r, t, b, _ in barriers:
        if check_barrier(new_x, y, l, r, t, b):
            final_x = x # block x axis

        if check_barrier(x, new_y, l, r, t, b):
            final_y = y # block y axis

    # bounded to walls
    return (
        max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, final_x)), 
        max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, final_y))
    )

# enum class
class Page():
    MENU = 1
    CHARACTER_SELECTION = 2
    GAME = 3

# main class
class App():
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, 200, title="Item Battle!", )
        pyxel.mouse(True)

        self.page = Page.MENU
        # self.round = 0
        # self.start_time = int(time())

        # button bounds
        self.character_selection_button_bounds = (0, 0, 0, 0) # l, r, t, b
        self.game_start_button_bounds = (0, 0, 0, 0) # l, r, t, b

        self.character_1_change_button_bounds = (0, 0, 0, 0)
        self.character_2_change_button_bounds = (0, 0, 0, 0)

        # game background
        pyxel.images[0].load(0, 0, "assets/imgs/floor2.png")

        # setup characters
        self.characters_info = {}
        with open("characters/info.json", 'r') as f:
            self.characters_info = json.load(f)

        self.character_1_x = 0
        self.character_1_y = CENTER_Y - CHARACTER_SIZE // 2
        self.character_1_flip = 1
        self.character_1_health = self.characters_info["character_1"]["health"]

        self.character_2_x = SCREEN_WIDTH - CHARACTER_SIZE
        self.character_2_y = CENTER_Y - CHARACTER_SIZE // 2
        self.character_2_flip = 1
        self.character_2_health = self.characters_info["character_2"]["health"]

        pyxel.images[1].load(0, 0, self.characters_info["character_1"]["icon"])
        pyxel.images[1].load(32, 0, self.characters_info["character_2"]["icon"])

        # barriers
        self.barriers = []
        self.generate_barriers(10)

        pyxel.images[2].load(0, 0, "assets/imgs/cone.png")
        pyxel.images[2].load(16, 0, "assets/imgs/rock.png")

        self.barriers_bounds = []

        pyxel.run(self.update, self.draw)

    def generate_barriers(self, num_barriers):
        for _ in range(num_barriers):
            while True:
                l = random.randint(0, SCREEN_WIDTH // 50 - 1) * 50
                l = max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, l))

                t = random.randint(0, SCREEN_WIDTH // 50 - 1) * 50
                t = max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, t))

                r = l + 16
                b = t + 16

                barrier_type = 0 #random.randint(0, 1)

                # check for overlap
                if not (
                    check_barrier(self.character_1_x, self.character_1_y, l, r, t, b) or 
                    check_barrier(self.character_2_x, self.character_2_y, l, r, t, b) or 
                    barrier_overlap(l, r, t, b, self.barriers)
                    ):

                    self.barriers.append((l, r, t, b, barrier_type))
                    break

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

        # characters
        self.make_character(
            "character_1",
            0, 0,
            50 - CHARACTER_SIZE, SCREEN_HEIGHT - 20
        )

        self.make_character(
            "character_2",
            32, 0,
            SCREEN_WIDTH - 70, SCREEN_HEIGHT - 20
        )

    def make_character(self, key, u, v, x, y, show_description=False):
        character_info = self.characters_info[key]
        health = character_info["health"]
        speed = character_info["speed"]
        strength = character_info["strength"]

        pyxel.text(x, y, f"Health: {health}", pyxel.COLOR_WHITE)
        pyxel.text(x, y+10, f"Speed: {speed}", pyxel.COLOR_WHITE)
        pyxel.text(x, y+20, f"Strength: {strength}", pyxel.COLOR_WHITE)

        pyxel.blt(
            x, y-40,
            1, u, v, # image bank 1
            CHARACTER_SIZE, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        if show_description:
            description = character_info["description"]

            wrapped = textwrap.fill(description, width=20)

            pyxel.text(x, y+30, f"[Description]\n{wrapped}", pyxel.COLOR_WHITE)
        else: # show the wasd/arrow thing
            if key == "character_1":
                pyxel.text(x, y-55, "Left (WASD)", pyxel.COLOR_WHITE)
            elif key == "character_2":
                pyxel.text(x, y-55, "Right (Arrows)", pyxel.COLOR_WHITE)

    def update_character_selection(self):

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            key = ""

            if pressed(self.character_1_change_button_bounds):
                key = "character_1"
            elif pressed(self.character_2_change_button_bounds):
                key = "character_2"
            else:
                return # exit otherwise
            
            input_image_path = open_file_picker()

            # put in thread so the player can do stuff while it's processing
            thread = Thread(target=self.character_selection_pressed, args=(key, input_image_path))
            thread.start()

    def character_selection_pressed(self, key, input_image_path):
        character = Character(input_image_path)
        character.wait_for_thread()

        print(f"{key} done")


    def draw_character_selection(self):

        center_aligned_text(CENTER_X, 20, "Character Selection", pyxel.COLOR_WHITE)

        # characters
        self.make_character(
            "character_1",
            0, 0,
            80 - CHARACTER_SIZE, 80,
            show_description=True
        )

        self.character_1_change_button_bounds = center_aligned_rect(80, 165, 60, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(80, 165, "Upload Photo", pyxel.COLOR_WHITE)

        self.make_character(
            "character_2",
            32, 0,
            SCREEN_WIDTH - CHARACTER_SIZE - 80, 80,
            show_description=True
        )

        self.character_2_change_button_bounds = center_aligned_rect(SCREEN_WIDTH - 80, 165, 60, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(SCREEN_WIDTH - 80, 165, "Upload Photo", pyxel.COLOR_WHITE)

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
            self.character_1_flip = -1
        if pyxel.btn(pyxel.KEY_S):
            character_1_new_y += character_1_speed
        if pyxel.btn(pyxel.KEY_D):
            character_1_new_x += character_1_speed
            self.character_1_flip = 1

        if pyxel.btn(pyxel.KEY_UP):
            character_2_new_y -= character_2_speed
        if pyxel.btn(pyxel.KEY_LEFT):
            character_2_new_x -= character_2_speed
            self.character_2_flip = -1
        if pyxel.btn(pyxel.KEY_DOWN):
            character_2_new_y += character_2_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            character_2_new_x += character_2_speed
            self.character_2_flip = 1

        # update based on collisions
        self.character_1_x, self.character_1_y = check_collisions(
            self.character_1_x, self.character_1_y,
            character_1_new_x, character_1_new_y,
            self.barriers
        )

        self.character_2_x, self.character_2_y = check_collisions(
            self.character_2_x, self.character_2_y,
            character_2_new_x, character_2_new_y,
            self.barriers
        )

    def draw_game(self):

        # draw bg
        for x in range(0, SCREEN_WIDTH, 50):
            for y in range(0, SCREEN_HEIGHT, 50):
                pyxel.blt(
                    x, y,
                    0, 0, 0,
                    50, 50,
                    pyxel.COLOR_BLACK
                )
        
        # draw menu bar

        pyxel.rect(0, SCREEN_HEIGHT, SCREEN_WIDTH, 20, pyxel.COLOR_BLACK)
        center_aligned_text(3* SCREEN_WIDTH/4, SCREEN_HEIGHT + 10, f"ROUND 1 | WASD: 10 | Arrows: 10", pyxel.COLOR_WHITE)
        center_aligned_text(SCREEN_WIDTH/4, SCREEN_HEIGHT + 10, "00:00", pyxel.COLOR_GREEN)


        # draw barriers
        for l, _, t, _, barrier_type in self.barriers:
            pyxel.blt(
                l, t,
                2, 16*barrier_type, 0, # image bank 2
                16, 16,
                pyxel.COLOR_BLACK
            )

        # draw characters
        animate = int(time() * 2) % 2

        pyxel.blt(
            self.character_1_x, self.character_1_y,
            1, 0, 2*animate, # image bank 0 @ u=0, v=0
            CHARACTER_SIZE*self.character_1_flip, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        pyxel.blt(
            self.character_2_x, self.character_2_y,
            1, 32, 2*animate, # image bank 1 @ u=0, v=0
            CHARACTER_SIZE*self.character_2_flip, CHARACTER_SIZE,
            pyxel.COLOR_BLACK
        )

        self.character_1_health = 20
        self.character_2_health = 20

        character_1_original_health = self.characters_info["character_1"]["health"]
        character_2_original_health = self.characters_info["character_2"]["health"]

        # draw health (back + health) for each
        pyxel.rect( # 100
            self.character_1_x, self.character_1_y - 6,
            32, 4,
            pyxel.COLOR_BLACK
        )
        pyxel.rect( # max
            self.character_1_x, self.character_1_y - 6,
            character_1_original_health * 32/100, 4,
            pyxel.COLOR_GRAY
        )
        pyxel.rect( # curr
            self.character_1_x, self.character_1_y - 6,
            self.character_1_health * 32/100, 4,
            pyxel.COLOR_GREEN
        )

        pyxel.rect( # 100
            self.character_2_x, self.character_2_y - 6,
            32, 4,
            pyxel.COLOR_BLACK
        )
        pyxel.rect( # max
            self.character_2_x, self.character_2_y - 6,
            character_2_original_health * 32/100, 4,
            pyxel.COLOR_GRAY
        )
        pyxel.rect( # curr
            self.character_2_x, self.character_2_y - 6,
            self.character_2_health * 32/100, 4,
            pyxel.COLOR_GREEN
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
        