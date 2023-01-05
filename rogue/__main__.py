import argparse

from rogue.migrations import makemigrations


actions = {
    "makemigrations": makemigrations,
    "migrate": NotImplemented,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actions for the Rogue ORM.")
    parser.add_argument(
        "action",
        type=str,
        choices=actions.keys(),
        help="The action expected from Rogue.",
    )

    args = parser.parse_args()

    actions[args.action]()
