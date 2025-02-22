from baseplate.server import load_app_and_run_server
from sqlalchemy import create_engine

engine = create_engine("sqlite:///:memory:", future=True)

load_app_and_run_server()
