import logging


def test_setup_logs_registered_routes(app, caplog):
    with caplog.at_level(logging.INFO):
        app.setup_routes()

    messages = [record.getMessage() for record in caplog.records]
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        assert f'Registered route: {methods} {rule.rule} -> {rule.endpoint}' in messages
    assert any('POST /s3/credentials' in message for message in messages)
