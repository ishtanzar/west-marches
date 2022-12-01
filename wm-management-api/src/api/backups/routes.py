from typing import Optional

from compose.project import NoSuchService

from api import WestMarchesApi

app = WestMarchesApi.instance


@app.route('/backup/list')
@app.auth.required
async def backup_list(user):
    return {
        'backups': [backup.asdict(serializable=True) for backup in app.backup.list(sort=[('date', 1)])]
    }


@app.route('/backup/perform', methods=['POST'])
@app.auth.required
async def backup_perform(user):
    service_name = 'foundry'
    error: Optional[Exception] = None

    try:
        app.compose.stop(service_name)

        try:
            for schema in ['worlds', 'systems', 'modules']:
                app.backup.perform(schema)
        except Exception as nse:
            error = nse

        app.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as nse:
        return str(nse), 500


@app.route('/backup/restore/<backup_id>', methods=['POST'])
@app.auth.required
async def backup_restore(user, backup_id):
    service_name = 'foundry'
    error: Optional[Exception] = None

    try:
        app.compose.stop(service_name)

        try:
            app.backup.restore(backup_id)
        except Exception as ex:
            error = ex

        app.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        return nse.msg, 404
    except Exception as ex:
        return str(ex), 500

