import asyncio
import base64
import concurrent.futures
import time
from concurrent import ThreadPoolExecutor
from io import BytesIO
from typing import List, Optional, Tuple

import requests
from ABC import abstractmethod
from PIL import Image


class BaseMultiModalModel:
    def __init__(
        self,
        model_name: Optional[str],
        temperature: Optional[int] = 0.5,
        max_tokens: Optional[int] = 500,
        max_workers: Optional[int] = 10,
        top_p: Optional[int] = 1,
        top_k: Optional[int] = 50,
        beautify: Optional[bool] = False,
        device: Optional[str] = "cuda",
        max_new_tokens: Optional[int] = 500,
        retries: Optional[int] = 3,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_workers = max_workers
        self.top_p = top_p
        self.top_k = top_k
        self.beautify = beautify
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.retries = retries
        self.chat_history = []

    
    @abstractmethod
    def __call__(self, text: str, img: str):
        """Run the model"""
        pass

    def run(self, task: str, img: str):
        """Run the model"""
        pass

    async def arun(self, task: str, img: str):
        """Run the model asynchronously"""
        pass

    def get_img_from_web(self, img: str):
        """Get the image from the web"""
        try:
            response = requests.get(img)
            response.raise_for_status()
            image_pil = Image.open(BytesIO(response.content))
            return image_pil
        except requests.RequestException as error:
            print(f"Error fetching image from {img} and error: {error}")
            return None
        
    def encode_img(self, img: str):
        """Encode the image to base64"""
        with open(img, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def get_img(self, img: str):
        """Get the image from the path"""
        image_pil = Image.open(img)
        return image_pil
    
    def clear_chat_history(self):
        """Clear the chat history"""
        self.chat_history = []

    def run_many(
        self,
        tasks: List[str],
        imgs: List[str],
    ):
        """
        Run the model on multiple tasks and images all at once using concurrent

        Args:
            tasks (List[str]): List of tasks
            imgs (List[str]): List of image paths
        
        Returns:
            List[str]: List of responses
            
        
        """
        # Instantiate the thread pool executor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = executor.map(self.run, tasks, imgs)

        # Print the results for debugging
        for result in results:
            print(result)


    def run_batch(self, tasks_images: List[Tuple[str, str]]) -> List[str]:
        """Process a batch of tasks and images"""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.run, task, img)
                for task, img in tasks_images
            ]
            results = [future.result() for future in futures]
        return results

    async def run_batch_async(
        self, tasks_images: List[Tuple[str, str]]
    ) -> List[str]:
        """Process a batch of tasks and images asynchronously"""
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(None, self.run, task, img)
            for task, img in tasks_images
        ]
        return await asyncio.gather(*futures)

    async def run_batch_async_with_retries(
        self, tasks_images: List[Tuple[str, str]]
    ) -> List[str]:
        """Process a batch of tasks and images asynchronously with retries"""
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(None, self.run_with_retries, task, img)
            for task, img in tasks_images
        ]
        return await asyncio.gather(*futures)
    
    def unique_chat_history(self):
        """Get the unique chat history"""
        return list(set(self.chat_history))
    
    def run_with_retries(self, task: str, img: str):
        """Run the model with retries"""
        for i in range(self.retries):
            try:
                return self.run(task, img)
            except Exception as error:
                print(f"Error with the request {error}")
                continue
    
    def run_batch_with_retries(self, tasks_images: List[Tuple[str, str]]):
        """Run the model with retries"""
        for i in range(self.retries):
            try:
                return self.run_batch(tasks_images)
            except Exception as error:
                print(f"Error with the request {error}")
                continue

    def _tokens_per_second(self) -> float:
        """Tokens per second"""
        elapsed_time = self.end_time - self.start_time
        if elapsed_time == 0:
            return float("inf")
        return self._num_tokens() / elapsed_time

    def _time_for_generation(self, task: str) -> float:
        """Time for Generation"""
        self.start_time = time.time()
        self.run(task)
        self.end_time = time.time()
        return self.end_time - self.start_time

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        """Generate Summary"""
        pass

    def set_temperature(self, value: float):
        """Set Temperature"""
        self.temperature = value

    def set_max_tokens(self, value: int):
        """Set new max tokens"""
        self.max_tokens = value

    def get_generation_time(self) -> float:
        """Get generation time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    def get_chat_history(self):
        """Get the chat history"""
        return self.chat_history
    
    def get_unique_chat_history(self):
        """Get the unique chat history"""
        return list(set(self.chat_history))
    
    def get_chat_history_length(self):
        """Get the chat history length"""
        return len(self.chat_history)
    
    def get_unique_chat_history_length(self):
        """Get the unique chat history length"""
        return len(list(set(self.chat_history)))
    
    def get_chat_history_tokens(self):
        """Get the chat history tokens"""
        return self._num_tokens()
    
    def print_beautiful(self, content: str, color: str = "cyan"):
        """Print Beautifully with termcolor"""
        content = colored(content, color)
        print(content)