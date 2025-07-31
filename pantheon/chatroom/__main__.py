import fire
from dotenv import load_dotenv

from .start import start_services


if __name__ == "__main__":
    load_dotenv()
    fire.Fire(start_services)
