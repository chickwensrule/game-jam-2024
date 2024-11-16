from character import Character
from gui import App
import os
import json

UPDATE_CHARACTERS = False
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
    character1 = Character(ORIGINAL_PATHS[0])
    character2 = Character(ORIGINAL_PATHS[1])

    # wait before accessing anything
    character1.wait_for_thread()
    character2.wait_for_thread()

    info = {
        "character1": {
            "icon": character1.get_icon(),
            "description": character1.get_description(),
            "health": character1.get_health(),
            "strength": character1.get_strength()
        },

        "character2": {
            "icon": character2.get_icon(),
            "description": character2.get_description(),
            "health": character2.get_health(),
            "strength": character2.get_strength()
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
