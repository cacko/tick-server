import logging
import typer
from lambo.config import app_config
from lambo.hue.client import Hue
from app.lametric.models import ALERT_COLOR, ALERT_DURATION
from app.botyo.models import ACTION
from time import sleep

app = typer.Typer()


@app.command()
def test_alerts() -> None:
    logging.info(">> GOAL POSITIVE")
    Hue.signaling(duration=ALERT_DURATION.GOAL, colors=ALERT_COLOR.GOAL_POSITIVE.value)
    sleep(5)
    logging.info(">> GOAL NEGATIVE")
    Hue.signaling(duration=ALERT_DURATION.GOAL, colors=ALERT_COLOR.GOAL_NEGATIVE.value)

    sleep(5)
    logging.info(">> GUYELLOW CARD")
    Hue.signaling(duration=ALERT_DURATION.YELLOW_CARD, colors=ALERT_COLOR.YELLOW_CARD.value)
    sleep(5)
    logging.info(">> RED CARD")
    Hue.signaling(duration=ALERT_DURATION.RED_CARD, colors=ALERT_COLOR.RED_CARD.value)
    
    sleep(5)
    logging.info(">> WIN")
    Hue.signaling(duration=ALERT_DURATION.FULL_TIME, colors=ALERT_COLOR.WIN.value)
    sleep(5)
    logging.info(">> WIN")
    Hue.signaling(duration=ALERT_DURATION.FULL_TIME, colors=ALERT_COLOR.LOSS.value)
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        print("test")
    
def start():
    Hue.register(hostname=app_config.hue.hostname, username=app_config.hue.username)
    app() 

if __name__ == "__main__":
    print("kiur")
    start()
