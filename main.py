from character import Character
from gui import App
import os
import json

UPDATE_CHARACTERS = True
ORIGINAL_PATHS = ("assets/fish.JPG", "assets/bottles.jpeg")

def generate_characters():

    # create a characters folder if it doesn't exist already
    os.makedirs("characters", exist_ok=True)

    # clear the characters folder
    for filename in os.listdir("characters"):
        file_path = os.path.join("characters", filename)

        if os.path.isfile(file_path):
            os.remove(file_path)

    # generate the characters
    character_1 = Character(ORIGINAL_PATHS[0])
    character_2 = Character(ORIGINAL_PATHS[1])

    # wait before accessing anything
    character_1.wait_for_thread()
    character_2.wait_for_thread()

    character_1_info = character_1.get_info()
    character_2_info = character_2.get_info()

    info = {
        "character_1": {
            "icon": character_1_info[0],
            "description": character_1_info[1],
            "health": character_1_info[2],
            "speed": character_1_info[3],
            "strength": character_1_info[4]
        },

        "character_2": {
            "icon": character_2_info[0],
            "description": character_2_info[1],
            "health": character_2_info[2],
            "speed": character_2_info[3],
            "strength": character_2_info[4]
        }
    }

    # add the info to the JSON
    with open("characters/info.json", 'w') as f:
        json.dump(info, f, indent=4)
        print("Generated and saved characters")

def verify_characters():
    if not os.path.exists("characters/info.json"):
        raise Exception("The character information file is missing, please regenerate the characters")

if __name__ == "__main__":
    # character_1 = Character(ORIGINAL_PATHS[0])
    # character_1.wait_for_thread()
    # print(character_1.get_info())
    # if UPDATE_CHARACTERS:
    #     print("Generating characters...")
    #     generate_characters()
    # else:
    #     print("Reusing characters...")
    #     verify_characters()
    
    app = App()



### open
    # with open("characters/info.json", 'r') as f:
    #     info = json.load(f)
    #     print(info)
