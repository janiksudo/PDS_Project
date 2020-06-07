import click
from . import model


@click.command()
@click.option('--train/--no-train', default=False, help="Train the model.")
def main(train):
    if train:
        model.train()
    else:
        print("You don't do anything.")


if __name__ == '__main__':
    main()
