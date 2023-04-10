import argparse

from rogue.migrations import makemigrations, migrate


actions = {
    "makemigrations": makemigrations,
    "migrate": migrate,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actions for the Rogue ORM.")
    parser.add_argument(
        "action",
        type=str,
        choices=actions.keys(),
        help="The action expected from Rogue.",
    )
    parser.add_argument(
        "--db_name",
        type=str,
        help="The name of the database to use. Will default to the settings database if not specified.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        help="The name of the file to use to migrate. Eventually, this will be deprecated in favor of a better migration tracking solution.",
    )

    args = parser.parse_args()

    print(args)

    kwargs = {"db_name": args.db_name}

    if args.action == "migrate":
        kwargs["filename"] = args.filename

    actions[args.action](**kwargs)
