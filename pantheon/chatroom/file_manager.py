import io
import base64

from PIL import Image
import pymupdf
from magique.ai.tools.file_manager import FileManagerToolSet as _FileManagerToolSet
from magique.ai.toolset import tool


def path_to_image_url(path: str) -> str:
    img = Image.open(path)
    with io.BytesIO() as buffer:
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


class FileManagerToolSet(_FileManagerToolSet):
    @tool
    async def view_images(self, __agent_run__, question: str, image_paths: list[str]) -> str:
        """View images and answer a question about them.
        
        Args:
            question: The question to answer.
            image_paths: The paths to the images to view."""
        run = __agent_run__
        query_msg = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": question,
                },
            ],
        }
        for img_path in image_paths:
            ipath = self.path / img_path
            query_msg["content"].append({
                "type": "image_url",
                "image_url": {"url": path_to_image_url(ipath)},
            })
        resp = await run([query_msg])
        return resp.content

    @tool
    async def read_pdf(self, pdf_path: str) -> str:
        """Read a PDF file and return the text inside it."""
        ipath = self.path / pdf_path
        texts = []
        doc = pymupdf.open(str(ipath))
        for page in doc:
            texts.append(page.get_text())
        return "\n".join(texts)
