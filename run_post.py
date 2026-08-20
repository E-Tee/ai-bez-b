from dotenv import load_dotenv
load_dotenv()
from agent.pipeline import run
run(do_publish=True)