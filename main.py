import sys
from dotenv import load_dotenv
load_dotenv()

from agent.pipeline import run

if __name__ == "__main__":
    # python main.py test  -> только показать
    # python main.py       -> опубликовать в паблик
    run(do_publish="test" not in sys.argv)