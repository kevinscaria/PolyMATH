import base64
import json
import mimetypes
import os
import requests
import sys
from dotenv import load_dotenv
os.chdir("../../")
# os.getcwd()

load_dotenv(".env")


class GPTinference :
    def __init__(
            self,
            folders,
            model = "gpt-4-vision-preview",
    ) :
        self.model = model
        self.folders = folders
        self.all_contexts = self.get_context_images()
        self.all_questions = self.get_question_images()
        self.context_map = dict()
        for q_image in self.all_questions :
            context = q_image.split('_')