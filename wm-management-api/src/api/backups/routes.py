import datetime
import logging
import uuid
from typing import Optional

from quart import request

from api import WestMarchesApi
from services.database import BackupState
from services.docker import NoSuchService

app = WestMarchesApi.instance
logger = logging.getLogger('backup')


@app.route('/backup/list')
@app.auth.required
async def backup_list(user):
    return {
        'backups': [backup.asdict(serializable=True) for backup in app.backup.list(sort=[('date', 1)])]
    }

@app.route('/backup', methods=['SEARCH'])
@app.auth.required
async def backup_search(user):
    query_filter = (await request.json) or {}
    query_sort = [(k.split('_')[1], int(v)) for k, v in request.args.items() if k.startswith('sort_')]
    query_limit = int(request.args.get('limit', 0))

    if 'latest' in request.args.keys():
        query_filter = {'state': 'BackupState.SUCCESS'}
        query_sort = [('date', -1)]
        query_limit = 1

    return {
        'backups': [backup.asdict(serializable=True) for backup in app.backup.find(
            filter=query_filter,
            sort=query_sort,
            limit=query_limit
        )]
    }

@app.route('/backup/perform', methods=['POST'])
@app.auth.required
async def backup_perform(user):
    service_name = 'foundry'
    error: Optional[Exception] = None
    allowed_schemas = ['worlds', 'systems', 'modules']

    schemas_in = request.args.get('schema', '').split(',')
    schemas = []

    for schema in schemas_in:
        if schema == 'all':
            schemas = allowed_schemas
            break
        if schema in allowed_schemas:
            schemas.append(schema)
        else:
            logger.warning(f'schema must be on of {allowed_schemas}')

    try:
        app.compose.stop(service_name)

        try:
            for schema in schemas:
                app.backup.perform(schema)
        except Exception as nse:
            error = nse

        app.compose.restart(service_name)

        if error:
            raise error
        return 'Done', 204
    except NoSuchService as nse:
        logger.exception(nse)
        return nse.msg, 404
    except Exception as e:
        logger.exception(e)
        return str(e), 500


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
        logger.exception(nse)
        return nse.msg, 404
    except Exception as e:
        logger.exception(e)
        return str(e), 500

