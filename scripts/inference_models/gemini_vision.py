import time
import tqdm
import pandas as pd
from PIL import Image

from typing import List

import google.generativeai as genai


do_gemini = True
genai.configure(api_key="")


class GeminiVisionInference:
    def __init__(
            self,
            sleep_time: int = 20,
            model_id: str = None,
            pre_image_prompt: str = None,
            post_image_prompt: str = None,
            pre_context: str = None,
            post_context: str = None,
            pre_q: str = None,
            post_q: str = None,
            ):
        self.pre_image_prompt = pre_image_prompt or """Provide descriptions for the following images."""
        self.post_image_prompt = post_image_prompt or """Output descriptions as a numbered list."""
        self.pre_context = pre_context or """This is the context for a mathematical problem."""
        self.post_context = post_context or """Based on the information above, answer the following question."""
        self.pre_q = pre_q or """Question instruction: """
        self.post_q = post_q or """Output only the correct answer option."""

        self.sleep_time = sleep_time
        self.model = genai.GenerativeModel(model_id or "gemini-pro-vision")  

    @staticmethod
    def print_gemini_models():
        for models_ in genai.list_models():
            print(models_.name, models_.description)

    def get_template(
            self, 
            context_paths: List, 
            img_paths: List
            ):

        img_list = []
        context_list = []

        for img_path in img_paths:
            img_list.append(Image.open(img_path))
        for context_path in context_paths:
            context_list.append(Image.open(context_path))

        template = [self.pre_context] + context_list + [self.post_context, self.pre_q] + img_list + [self.post_q]
        return template

    def gemini_response(self, context_paths, img_paths):
        template = self.get_template(context_paths=context_paths, img_paths=img_paths)
        response = self.model.generate_content(template, stream=True)
        response.resolve()
        try:
            response_text = response.text
        except: 
            response_text = response.prompt_feedback
        return response_text
