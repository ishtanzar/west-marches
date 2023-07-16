import json
import pytest

from unittest.mock import patch, mock_open

from services.utils import Config


def test_config():

    val1 = 'value'
    val2 = 'other_value'
    default_val = 'something'

    config_in = {
        'key': val1,
        'deeper': {
            'key': val2
        }
    }

    with patch('pathlib.Path.open', mock_open(read_data=json.dumps(config_in))):
        config = Config.load('/dev/null')

        assert config.key == val1
        assert config.deeper.key == val2

        with pytest.raises(AttributeError):
            assert config.deeper.unexpected is None

        assert config.get('deeper.key') == val2
        assert config.get('deeper.unexpected', default_val) == default_val
        assert config.get('do.not.exist', default_val) == default_val

