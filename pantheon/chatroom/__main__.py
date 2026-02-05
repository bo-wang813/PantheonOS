import fire
from dotenv import load_dotenv

# Load .env file (user-level .env has highest priority)
load_dotenv(override=True)

# Now safe to import other modules
from .start import start_services


if __name__ == "__main__":
    fire.Fire(start_services)
