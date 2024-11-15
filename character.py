from openai import OpenAI
import base64
import json
import rembg
import requests
from io import BytesIO
from PIL import Image
from threading import Thread

VISION_PROMPT = """
You are creating an object out of the image provided which will be used to simulate a battle another object later on.

1. Figure out what is in the image and give it a short name and create a short yet detailed description of it (max 20 words)
2. Based on the item, determine the health (out of 100), and strength (out of 50) of the character
3. Update the values using the function provided
"""

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

class Character():
    def __init__(self, image_path):
        self.client = OpenAI()

        # put it in a thread to allow multiple characters to be created at the same time
        self.thread = Thread(target=self.process_img, args=(image_path, ))
        self.thread.start()
        
    def process_img(self, path):
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
                    "description": "Set the character's attributes based on the description, health, and strength.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "health": {"type": "integer", "minimum": 0, "maximum": 100},
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
        self.set_info(function_args["name"], function_args["description"], function_args["health"], function_args["strength"])

        # after updating the info, generate the image
        self.generate_img()

    def generate_img(self):

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
        image_response = requests.get(image_url)

        image = Image.open(BytesIO(image_response.content))

        # convert to bytes stream
        input_bytes = BytesIO()
        image.save(input_bytes, format='PNG')
        input_bytes = input_bytes.getvalue()

        output_bytes = rembg.remove(input_bytes)

        output_image = Image.open(BytesIO(output_bytes))

        output_image.save(f"characters/{self.icon}", "PNG")

    def wait_for_thread(self):
       self.thread.join()

    def set_info(self, name, description, health, strength):
        self.icon = f"{name}.png"
        self.description = description
        self.health = health
        self.strength = strength

    def get_icon(self):
       return f"characters/{self.icon}"

    def get_description(self):
       return self.description

    def get_health(self):
       return self.health
    
    def get_strength(self):
       return self.strength
    