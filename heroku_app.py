from typing import *
import os
import json
from flask import Flask, stream_with_context
from flask.helpers import make_response
from flask.wrappers import Response
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import facebook
import util


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, world"


@app.route("/event/<int:event_id>", methods=["GET"])
def event(event_id: int):

    d = get_webdriver()

    event_page = util.memoize(
        "fb_page_event",
        util.curry(facebook.fetch_page__event)(d)
    )(str(event_id))

    event_details = facebook.extract_event_details(event_page)
    generic_event = facebook.parse_event_details(event_details)

    response = make_response(generic_event)
    response.headers["Access-Control-Allow-Origin"] = "*"

    return response


@app.route("/profile/<profile_name>/events", methods=["GET"])
def profile_events(profile_name: str):
    try:
        d = get_webdriver()

        _, postrender = util.memoize(
            "fb_page_events_for_profile",
            util.curry(facebook.fetch_page__events_for_profile)(d)
        )(profile_name)

    except facebook.ProfileNotFoundError:
        return make_response("Profile not found", 404)

    ids = facebook.extract_event_ids(postrender)

    response = make_response(
        stream_with_context(
            profile_events_generator(ids)))

    response.headers["Content-Type"] = "text/plain"
    response.headers["Access-Control-Allow-Origin"] = "*"

    return response


def profile_events_generator(ids: List[str]):
    d = get_webdriver()

    yield json.dumps(ids)
    yield "\n"

    for id in ids:
        event_page = util.memoize(
            "fb_page_event",
            util.curry(facebook.fetch_page__event)(d)
        )(id)
        event_details = facebook.extract_event_details(event_page)
        generic_event = facebook.parse_event_details(event_details)

        yield json.dumps(generic_event)
        yield "\n"


def get_webdriver() -> WebDriver:
    if "GOOGLE_CHROME_SHIM" in os.environ:
        cap = DesiredCapabilities.CHROME
        cap = {"binary_location": os.environ.get("GOOGLE_CHROME_SHIM")}
        driver = util.lazy_chrome_web_driver(desired_capabilities=cap)
        return driver

    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    return util.lazy_chrome_web_driver(options=chrome_options)


if __name__ == "__main__":
    app.run(debug=True)
