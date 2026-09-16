import sys
from game.game import Game


if __name__ == "__main__":
    level = sys.argv[1] if len(sys.argv) > 1 else "level_01"
    Game(level_name=level).run()
