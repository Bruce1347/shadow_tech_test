from src.api.main import engine
from src.database.common import BaseModel

import argparse


def init_cmd_line() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Database initializer",
        description="Initialises an empty database for a books library management",
    )

    parser.add_argument("-d", "--drop", action="store_true")

    return parser


if __name__ == "__main__":
    args = init_cmd_line().parse_args()

    if args.drop:
        BaseModel.metadata.drop_all(bind=engine)

    # Create only missing tables
    BaseModel.metadata.create_all(bind=engine, checkfirst=True)
