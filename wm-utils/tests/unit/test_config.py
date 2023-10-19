import os.path

from westmarches_utils.config import Config


def test_config_set():
    conf = Config.load(os.path.join(os.path.dirname(__file__), "config.json"))
    assert conf.opt1 == "value"
    assert conf.get("opt2.sub1") == "value"
    assert conf.get("opt2.sub2", "default") == 'default'

    conf.set("opt3.sub", "value")
    assert conf.opt3.sub == "value"

