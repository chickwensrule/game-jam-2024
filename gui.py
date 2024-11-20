import pyxel
import json
import random
from time import time
import textwrap
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget
from character import Character
from threading import Thread
from datetime import datetime, timezone
from PIL import Image
import os

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
    fp, _ = QFileDialog.getOpenFileName(window, "Select a JPEG file", "", "JPEG Files (*.jpeg *.jpg)")

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
        w = r-l
        h = b-t

        if check_barrier(new_x, y, l + w//4, r - w//4, t + h//4, b - h//4):
            final_x = x # block x axis

        if check_barrier(x, new_y, l + w//4, r - w//4, t + h//4, b - h//4):
            final_y = y # block y axis

    # bounded to walls
    return (
        max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, final_x)), 
        max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, final_y))
    )

def notify_round(text):
    pyxel.rect(0, 10, pyxel.FONT_WIDTH * len(text) + 8, pyxel.FONT_HEIGHT + 8, pyxel.COLOR_BROWN)
    pyxel.text(4, 14, text, pyxel.COLOR_WHITE)

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

        # self.title = pyxel.load("assets/imgs/title.png")

        self.page = Page.MENU
        self.notification = ""
        self.notification_start_time = 0

        # button bounds (l, r, t, b)
        self.character_selection_button_bounds = (0, 0, 0, 0)
        self.game_start_button_bounds = (0, 0, 0, 0)

        self.character_1_change_button_bounds = (0, 0, 0, 0)
        self.character_2_change_button_bounds = (0, 0, 0, 0)
        self.character_1_flip_button_bounds = (0, 0, 0, 0)
        self.character_2_flip_button_bounds = (0, 0, 0, 0)

        self.game_back_button_bounds = (0, 0, 0, 0)
        self.character_selection_back_button_bounds = (0, 0, 0, 0)

        # game backgrounds
        pyxel.images[0].load(0, 0, "assets/imgs/floor2.png")
        pyxel.images[0].load(50, 80, "assets/imgs/stars1.png")
        pyxel.images[0].load(100, 80, "assets/imgs/stars2.png")
        pyxel.images[0].load(150, 80, "assets/imgs/stars3.png")
        pyxel.images[0].load(200, 80, "assets/imgs/stars4.png")
        pyxel.images[0].load(250, 80, "assets/imgs/stars4.png") # more chance of it happening again

        self.update_stars_bg()

        # title
        pyxel.images[0].load(50, 0, "assets/imgs/title2.png")

        # setup characters
        self.characters_info = {}
        with open("characters/info.json", 'r') as f:
            self.characters_info = json.load(f)

        pyxel.images[1].load(0, 0, self.characters_info["character_1"]["icon"])
        pyxel.images[1].load(32, 0, self.characters_info["character_2"]["icon"])

        # barriers
        pyxel.images[2].load(0, 0, "assets/imgs/cone.png")
        # pyxel.images[2].load(16, 0, "assets/imgs/spike2.png")

        # sounds
        pyxel.sounds[0].set(
            "c2c3",
            "p",
            "77",
            "n",
            5
        )

        pyxel.sounds[1].set(
            "e2e3",
            "p",
            "77",
            "n",
            5
        )

        # bg music

        pyxel.sounds[2].set( # main
            "a2b2c2",
            "t",
            "5",
            "n",
            140
        )

        pyxel.sounds[3].set(
            "a1e1g1d1e1e2",
            "p",
            "3",
            "n",
            10
        )

        pyxel.sounds[4].set(
            "a1b3c4c4c3b1",
            "p",
            "4",
            "f",
            70
        )

        pyxel.musics[0].set(
            [2, 2, 2, 2],
            [3, 4, 3, 4]
        )

        pyxel.playm(0, loop=True)


        pyxel.run(self.update, self.draw)

    def update_stars_bg(self):
        self.last_stars_time = time()
        self.stars_bg = []
        for _ in range(0, SCREEN_WIDTH, 50):
            lst = []
            for _ in range(0, SCREEN_HEIGHT, 50):
                lst.append(50*random.randint(1, 5))
            self.stars_bg.append(lst)


    def generate_barriers(self, num_barriers):
        for _ in range(num_barriers):
            while True:
                l = random.randint(0, SCREEN_WIDTH // 50 - 1) * 50
                l = max(0, min(SCREEN_WIDTH - CHARACTER_SIZE, l))

                t = random.randint(0, SCREEN_WIDTH // 50 - 1) * 50
                t = max(0, min(SCREEN_HEIGHT - CHARACTER_SIZE, t))

                r = l + 16
                b = t + 16

                barrier_type = 0#random.randint(0,1)

                # check for overlap
                if not (
                    check_barrier(self.character_1_x, self.character_1_y, l, r, t, b) or 
                    check_barrier(self.character_2_x, self.character_2_y, l, r, t, b) or 
                    barrier_overlap(l, r, t, b, self.barriers)
                    ):

                    self.barriers.append((l, r, t, b, barrier_type))
                    break

    def update_menu(self):

        # stars
        if time() - self.last_stars_time >= random.randint(1, 5):
            self.update_stars_bg()

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):

            if pressed(self.character_selection_button_bounds):
                self.page = Page.CHARACTER_SELECTION
            elif pressed(self.game_start_button_bounds):

                # round stuff
                self.start_time = time()
                self.round = 1
                self.character_1_score = 0
                self.character_2_score = 0

                self.reset_level()

                # update page
                self.page = Page.GAME
                pyxel.stop()

    def draw_menu(self):

        # stars bg
        for x in range(0, SCREEN_WIDTH, 50):
            xi = x//50
            for y in range(0, SCREEN_HEIGHT, 50):
                yi = y//50

                pyxel.blt(
                    x, y,
                    0, self.stars_bg[xi][yi], 80,
                    50, 50,
                    pyxel.COLOR_BLACK
                )

        # title
        pyxel.blt(
            CENTER_X-50, CENTER_Y-70,
            0, 50, 0, # image bank 0
            100, 60,
            pyxel.COLOR_BLACK
        )

        # character button
        self.character_selection_button_bounds = center_aligned_rect(CENTER_X, CENTER_Y+20, 84, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y+20, "Character Selection", pyxel.COLOR_WHITE)

        # game button
        self.game_start_button_bounds = center_aligned_rect(CENTER_X, CENTER_Y+42, 50, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(CENTER_X, CENTER_Y+42, "Start Game", pyxel.COLOR_WHITE)

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

            wrapped = textwrap.fill(description, width=30)

            pyxel.text(x, y+30, f"Description:\n{wrapped}", pyxel.COLOR_WHITE)
        else: # show the name thing
            pyxel.text(x, y-55, self.characters_info[key]["icon"][11:-4], pyxel.COLOR_WHITE)

    def update_character_selection(self):

        # go back
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if pressed(self.character_selection_back_button_bounds):
                self.page = Page.MENU

        # flip image
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if pressed(self.character_1_flip_button_bounds):
                fp = self.characters_info["character_1"]["icon"]

                pil_img = Image.open(fp)
                flipped = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                flipped.save(fp)

                # reload image
                pyxel.images[1].load(0, 0, self.characters_info["character_1"]["icon"])

            elif pressed(self.character_2_flip_button_bounds):
                fp = self.characters_info["character_2"]["icon"]

                pil_img = Image.open(fp)
                flipped = pil_img.transpose(Image.FLIP_LEFT_RIGHT)
                flipped.save(fp)

                # reload image
                pyxel.images[1].load(32, 0, self.characters_info["character_2"]["icon"])

        # upload
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            key = ""

            if pressed(self.character_1_change_button_bounds):
                key = "character_1"
            elif pressed(self.character_2_change_button_bounds):
                key = "character_2"
            else:
                return # exit otherwise
            
            input_image_path = open_file_picker()

            if not input_image_path:
                print("No file selected")
                return


            character = Character(input_image_path) # blocking
            self.update_character_json(character.get_info(), key)
    
    def update_character_json(self, character_info, key):

        current_icon = self.characters_info[key]["icon"]
        if os.path.exists(current_icon):
            os.remove(current_icon)
        
        # add new character
        self.characters_info[key] = {
            "icon": character_info[0],
            "description": character_info[1],
            "health": character_info[2],
            "speed": character_info[3],
            "strength": character_info[4]
        }

        with open("characters/info.json", 'w') as f:
            json.dump(self.characters_info, f, indent=4)
            print("Saved character")

        # reload images
        pyxel.images[1].load(0, 0, self.characters_info["character_1"]["icon"])
        pyxel.images[1].load(32, 0, self.characters_info["character_2"]["icon"])

        print(self.characters_info)

    # def character_selection_pressed(self, key, input_image_path):
    #     character = Character(input_image_path)
        # character.wait_for_thread()

        # print(f"{key} done")


    def draw_character_selection(self):

        # title
        center_aligned_text(CENTER_X, 20, "Character Selection", pyxel.COLOR_WHITE)

        # back button
        self.character_selection_back_button_bounds = center_aligned_rect(CENTER_X - 60, 20, 24, 10, pyxel.COLOR_RED)
        center_aligned_text(CENTER_X - 60, 20, "Back", pyxel.COLOR_WHITE)

        # characters
        self.make_character(
            "character_1",
            0, 0,
            40 - CHARACTER_SIZE, 80,
            show_description=True
        )

        self.character_1_change_button_bounds = center_aligned_rect(40, 180, 60, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(40, 180, "Upload Photo", pyxel.COLOR_WHITE)

        self.character_1_flip_button_bounds = center_aligned_rect(100, 180, 30, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(100, 180, "Flip", pyxel.COLOR_WHITE)

        self.make_character(
            "character_2",
            32, 0,
            SCREEN_WIDTH - CHARACTER_SIZE - 120, 80,
            show_description=True
        )

        self.character_2_change_button_bounds = center_aligned_rect(SCREEN_WIDTH - 120, 180, 60, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(SCREEN_WIDTH - 120, 180, "Upload Photo", pyxel.COLOR_WHITE)

        self.character_2_flip_button_bounds = center_aligned_rect(SCREEN_WIDTH - 60, 180, 30, 16, pyxel.COLOR_DARK_BLUE)
        center_aligned_text(SCREEN_WIDTH - 60, 180, "Flip", pyxel.COLOR_WHITE)


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

        # exit
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            if pressed(self.game_back_button_bounds):
                self.page = Page.MENU
                pyxel.playm(0, loop=True)

        # attack
        if pyxel.btnp(pyxel.KEY_C):
            pyxel.play(0, 0) # sound
            if check_barrier(
                self.character_1_x, self.character_1_y,
                self.character_2_x + CHARACTER_SIZE // 4, self.character_2_x + 3 * CHARACTER_SIZE // 4,
                self.character_2_y + CHARACTER_SIZE // 4, self.character_2_y + 3 * CHARACTER_SIZE // 4,
            ):
                strength = self.characters_info["character_1"]["strength"]

                self.character_2_health -= random.randint(1, strength)
        if pyxel.btnp(pyxel.KEY_SLASH):
            pyxel.play(0, 1) # sound
            if check_barrier(
                self.character_2_x, self.character_2_y,
                self.character_1_x + CHARACTER_SIZE // 4, self.character_1_x + 3 * CHARACTER_SIZE // 4,
                self.character_1_y + CHARACTER_SIZE // 4, self.character_1_y + 3 * CHARACTER_SIZE // 4,
            ):
                strength = self.characters_info["character_2"]["strength"]

                self.character_1_health -= random.randint(1, strength)

        # round over condition (death or take too long)
        if self.character_1_health <= 0 or self.character_2_health <= 0 or time() - self.start_time >= 60 or self.round > 5:
            self.notification_start_time = time()

            # update score & round
            if self.character_1_health <= 0:
                self.character_2_score += 1
                self.notification = f"{self.characters_info['character_2']['icon'][11:-4]} won round {self.round}"
            elif self.character_2_health <= 0:
                self.character_1_score += 1
                self.notification = f"{self.characters_info['character_1']['icon'][11:-4]} won round {self.round}"
            elif time() - self.start_time >= 60:
                self.notification = f"Time ran out, nobody won round {self.round}!"
            else: # 5 rounds

                winner = ""
                if self.character_1_score > self.character_2_score: # char 1 win
                    winner = self.characters_info['character_1']['icon'][11:-4]
                    self.notification = f"Game over, {winner} won {self.character_1_score} to {self.character_2_score}"
                elif self.character_2_score > self.character_1_score: # char 2 win
                    winner = self.characters_info['character_2']['icon'][11:-4]
                    self.notification = f"Game over, {winner} won {self.character_2_score} to {self.character_1_score}"
                else: # maybe a round nobody won bc time ran out
                    self.notification = "Tie, nobody won!"

                self.page = Page.MENU
                pyxel.playm(0, loop=True)

                return # exit

            self.round += 1
            self.reset_level()

            # return to prevent any changes
            return

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

    def reset_level(self):
        # reset everything
        self.character_1_x = 0
        self.character_1_y = CENTER_Y - CHARACTER_SIZE // 2
        self.character_1_flip = 1
        self.character_1_health = self.characters_info["character_1"]["health"]

        self.character_2_x = SCREEN_WIDTH - CHARACTER_SIZE
        self.character_2_y = CENTER_Y - CHARACTER_SIZE // 2
        self.character_2_flip = 1
        self.character_2_health = self.characters_info["character_2"]["health"]

        # generate barriers again
        self.barriers = []
        self.generate_barriers(10)

        # reset timer
        self.start_time = time()

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

        # back button
        self.game_back_button_bounds = center_aligned_rect(20, SCREEN_HEIGHT + 10, 24, 10, pyxel.COLOR_RED)
        center_aligned_text(20, SCREEN_HEIGHT + 10, "Exit", pyxel.COLOR_WHITE)

        # get timestamp & timer
        timestamp = datetime.fromtimestamp(time() - self.start_time, tz=timezone.utc).strftime('%M:%S')
        pyxel.text(40, SCREEN_HEIGHT - pyxel.FONT_HEIGHT // 2 + 10, timestamp, pyxel.COLOR_GREEN if time() - self.start_time < 50 else pyxel.COLOR_RED)

        # info
        pyxel.text(67, SCREEN_HEIGHT - pyxel.FONT_HEIGHT // 2 + 10, f"ROUND {self.round} / 5 | {self.characters_info['character_1']['icon'][11:-4]}: {self.character_1_score} | {self.characters_info['character_2']['icon'][11:-4]}: {self.character_2_score}", pyxel.COLOR_WHITE)

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

        # animate attack
        if pyxel.btnp(pyxel.KEY_C):
            pyxel.rect(self.character_1_x+(33 if self.character_1_flip == 1 else -6), self.character_1_y, 2, 16, pyxel.COLOR_GRAY)
        if pyxel.btnp(pyxel.KEY_SLASH):
            pyxel.rect(self.character_2_x+(33 if self.character_2_flip == 1 else -6), self.character_2_y, 2, 16, pyxel.COLOR_GRAY)

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

        # check notif time & reset accordingly
        if time() - self.notification_start_time > 5:
            self.notification = ""

    def draw(self):
        pyxel.cls(0)

        if self.page == Page.MENU:
            self.draw_menu()
        if self.page == Page.CHARACTER_SELECTION:
            self.draw_character_selection()
        elif self.page == Page.GAME:
            self.draw_game()

        # draw notif if it exists
        if self.notification:
            notify_round(self.notification)
