import click

import aw_client


@click.command()
@click.option("--testing", is_flag=True)
def main(testing: bool):
    awc = aw_client.ActivityWatchClient(testing=testing)
    raise NotImplementedError
