from character import Character
import os

UPDATE_CHARACTERS = True
ORIGINAL_PATHS = ("assets/fish.JPG", "assets/larry.JPG")

def get_characters():
    character1_path = ""
    character2_path = ""

    if UPDATE_CHARACTERS:
        print("Generating characters...")

        # create a characters folder if it doesn't exist already
        os.makedirs("characters", exist_ok=True)

        # clear the character items
        for filename in os.listdir("characters"):
            file_path = os.path.join("characters", filename)

            if os.path.isfile(file_path):
                os.remove(file_path)

        # generate the characters
        char1 = Character(ORIGINAL_PATHS[0])
        char2 = Character(ORIGINAL_PATHS[1])

        # wait before accessing anything
        char1.wait_for_thread()
        char2.wait_for_thread()

        character1_path = char1.get_icon()
        character2_path = char2.get_icon()
    else:
        print("Reusing characters...")

        character_paths = []
        for filename in os.listdir("characters"):
            character_paths.append(f"characters/{filename}")

        if len(character_paths) != 2:
            raise Exception("Not enough characters (<2) available, please generate more")

        character1_path = character_paths[0]
        character2_path = character_paths[1]
    
    return character1_path, character2_path

if __name__ == "__main__":
    print(get_characters())
