from compose.project import NoSuchService

from api import WestMarchesApi

flask = WestMarchesApi.instance


@flask.route('/')
@flask.auth.required
def index(user):
    return "Hello, {}!".format(user)


@flask.route('/container/restart/<service_name>', methods=['POST'])
@flask.auth.required
def restart_container(service_name, user):
    try:
        flask.compose.restart(service_name)
    except NoSuchService as nse:
        return nse.msg, 404

    return 'Done', 204


@flask.route('/backup/list')
@flask.auth.required
def backup_list(user):
    return {
        'backups': [backup.asdict(serializable=True) for backup in flask.backup.list(sort=[('date', 1)])]
    }


@flask.route('/backup/perform', methods=['POST'])
@flask.auth.required
def backup_perform(user):
    service_name = 'foundry'
    error = None

    try:
        flask.compose.stop(service_name)

        try:
            for schema in ['worlds', 'systems', 'modules']:
                flask.backup.perform(schema)
        except Exception as nse:
            error = nse

        flask.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as nse:
        return str(nse), 500


@flask.route('/backup/restore/<backup_id>', methods=['POST'])
@flask.auth.required
def backup_restore(user, backup_id):
    service_name = 'foundry'
    error = None

    try:
        flask.compose.stop(service_name)

        try:
            flask.backup.restore(backup_id)
            return 'Done', 204
        except Exception as ex:
            error = ex

        flask.compose.restart(service_name)

        if error:
            raise error
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as ex:
        return str(ex), 500

    return 'Done', 204
