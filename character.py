from openai import OpenAI
import base64
import json
import requests
from io import BytesIO
from PIL import Image
from threading import Thread
import rembg

IMAGE_SIZE = (32, 32)

VISION_PROMPT = """
You are creating an object out of the image provided which will be used to simulate a battle another object later on.

1. Figure out what is in the image and give it a short name (MAX 10 CHARACTERS!) and create a short yet detailed description of it (max 20 words)
2. Heavily influenced by the specific item's traits, determine the health (out of 100), speed (1 to 5, inclusive), and strength (out of 50) of the character
3. Update the values using the function provided
"""

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

class Character():
    def __init__(self, image_path):
        self.client = OpenAI()

        self.process_img(image_path)
        
    def process_img(self, path):
        print("Processing image...")
        base64_image = encode_image(path)

        # generate the info
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",

            # prompt w/ image
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": VISION_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":  f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],

            # give it the function to call
            functions=[
                {
                    "name": "set_info",
                    "description": "Set character attributes based on the description, health, speed, and strength.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "health": {"type": "integer", "minimum": 0, "maximum": 100},
                            "speed": {"type": "integer", "minimum": 1, "maximum": 5},
                            "strength": {"type": "integer", "minimum": 0, "maximum": 50},
                        },
                        "required": ["description", "health", "strength"],
                    },
                }
            ],

            function_call="auto"
        )

        # get the function call obj
        function_call = response.choices[0].message.function_call

        # convert to json
        function_args = json.loads(function_call.arguments)

        # call the method to update the info
        self.set_info(
           function_args["name"], 
           function_args["description"], 
           function_args["health"], 
           function_args["speed"], 
           function_args["strength"]
        )

        # after updating the info, generate the image
        self.generate_img()

    def generate_img(self):
        print("Generating pixelated image...")

        # generate the image
        response = self.client.images.generate(
            model="dall-e-2",
            prompt=f"{self.description}, pixel art with a white background",
            size="256x256",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        print(image_url)

        print("Removing background...")
        image_response = requests.get(image_url)

        image = Image.open(BytesIO(image_response.content))

        # convert to bytes stream
        input_bytes = BytesIO()
        image.save(input_bytes, format='PNG')
        input_bytes = input_bytes.getvalue()

        output_bytes = rembg.remove(input_bytes)
        output_image = Image.open(BytesIO(output_bytes))

        # Resizing image
        scaled_image = output_image.resize(IMAGE_SIZE, Image.NEAREST)

        scaled_image.save(self.icon, "PNG")
        print("Image saved")

    def wait_for_thread(self):
    #    self.thread.join()
        pass

    def set_info(self, name, description, health, speed, strength):
        self.icon = f"characters/{name}.png"
        self.description = description
        self.health = health
        self.speed = speed
        self.strength = strength

    def get_info(self):
       return self.icon, self.description, self.health, self.speed, self.strength