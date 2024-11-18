from openai import OpenAI
import base64
import json
import requests
from io import BytesIO
from PIL import Image
from threading import Thread
import cv2
import numpy as np

IMAGE_SIZE = (32, 32)

VISION_PROMPT = """
You are creating an object out of the image provided which will be used to simulate a battle another object later on.

1. Figure out what is in the image and give it a short name and create a short yet detailed description of it (max 20 words)
2. Heavily influenced by the specific item's traits, determine the health (out of 100), speed (1 to 5, inclusive), and strength (out of 50) of the character
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
                    "description": "Set the character's attributes based on the description, health, and strength.",
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
        self.set_info(function_args["name"], function_args["description"], function_args["health"], function_args["speed"], function_args["strength"])

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

        # convert to opencv format
        open_cv_img = np.array(image)
        open_cv_img = cv2.cvtColor(open_cv_img, cv2.COLOR_RGB2BGR) # convert to bgr

        hsv = cv2.cvtColor(open_cv_img, cv2.COLOR_BGR2HSV) # convert to hsv

        # make a range for background
        lower = np.array((0, 0, 200))
        upper = np.array((180, 30, 255))

        # detect background mask
        mask = cv2.inRange(hsv, lower, upper)
        
        # invert to get the foreground
        mask_inv = cv2.bitwise_not(mask)
        
        # apply mask to get the foreground (and)
        result = cv2.bitwise_and(open_cv_img, open_cv_img, mask=mask_inv)
        
        # add an alpha channel for transparency
        result_with_alpha = cv2.cvtColor(result, cv2.COLOR_BGR2RGBA)
        result_with_alpha[:, :, 3] = mask_inv # set alpha to 0 for bg of all rows & columns

        # convert back to pil
        result_image = Image.fromarray(result_with_alpha, 'RGBA')
        
        # Resize the image as per the desired size
        scaled_image = result_image.resize(IMAGE_SIZE, Image.NEAREST)

        scaled_image.save(self.icon, "PNG")
        print("Image saved")

    def wait_for_thread(self):
       self.thread.join()

    def set_info(self, name, description, health, speed, strength):
        self.icon = f"characters/{name}.png"
        self.description = description
        self.health = health
        self.speed = speed
        self.strength = strength

    def get_info(self):
       return self.icon, self.description, self.health, self.speed, self.strength
    