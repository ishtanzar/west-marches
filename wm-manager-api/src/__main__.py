import bjoern

from api import app


def main():
    bjoern.run(app, '0.0.0.0', 5000)


if __name__ == "__main__":
    main()
