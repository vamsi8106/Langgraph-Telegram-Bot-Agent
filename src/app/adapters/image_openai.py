# src/app/adapters/image_openai.py
import base64
import uuid
from openai import OpenAI
from ..config.settings import settings


def build_image_gen():
    """
    Build an OpenAI image generation client.

    Returns
    -------
    Callable[[str, str], str]
        A function `_generate(prompt, size)` that generates an image from a text prompt
        using the configured OpenAI image model and returns the saved image path.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _generate(prompt: str, size: str = "1024x1024") -> str:
        """
        Generate an image using OpenAI's image API.

        Parameters
        ----------
        prompt : str
            Text prompt describing the desired image.
        size : str, optional
            Image resolution (default is "1024x1024").

        Returns
        -------
        str
            Local file path of the generated PNG image.
        """
        response = client.images.generate(
            model=settings.openai_image_model,
            prompt=prompt,
            size=size,
            quality="high",
        )

        # Decode base64 → bytes → PNG
        image_b64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)

        # Save image to disk with UUID filename
        file_path = f"{uuid.uuid4()}.png"
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return file_path

    return _generate
