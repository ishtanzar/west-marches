import json
import logging
from secrets import token_hex

import boto3
import requests
from botocore.exceptions import ClientError
from redbot.core import commands, checks
from westmarches_utils.api import HTTPException

from westmarches.commands import AbstractCommand

log = logging.getLogger("red.westmarches.bot.inkarnate")


class InkarnateApiClient:

    def __init__(self, endpoint='https://api2.inkarnate.com/api'):
        self._token = None
        self._endpoint = endpoint

    def _request(self, method, url, **kwargs):
        resp = requests.request(method, self._endpoint + url, **kwargs)

        log.info('%s %s - %i', method.upper(), url, resp.status_code)

        if resp.ok:
            return resp
        else:
            raise HTTPException(resp)

    def login(self, email: str, password: str):
        resp = self._request('post', '/tokens', json={
            'email': email,
            'password': password
        })

        json_resp = resp.json()
        self._token = json_resp['authToken']
        return json_resp

    def change_password(self, current: str, update: str):
        self._request('post', '/user/changePassword', json={
            'oldPassword': current,
            'newPassword': update
        }, headers={
            'Authorization': 'Token ' + self._token
        })

    def logout(self, token: str = None):
        self._request('delete', '/tokens/' + (token if token else self._token))


class InkarnateCommands(AbstractCommand):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._inkarnate = InkarnateApiClient()

    @checks.has_permissions(administrator=True)
    @commands.group(name="inkarnate")
    async def command_inkarnate(self, ctx: commands.Context):
        """Inkarnate admin commands"""

    @command_inkarnate.command()
    async def update_password(self, ctx: commands.Context):
        """Update inkarnate account with a new random password"""
        inkarnate_logged = False
        try:
            sm_client = boto3.client('secretsmanager')
            secret = sm_client.get_secret_value(SecretId='account/inkarnate')
            secret_value = json.loads(secret['SecretString'])
            new_password = token_hex(16)

            self._inkarnate.login(secret_value['email'], secret_value['password'])
            inkarnate_logged = True

            async with self.config.messages() as messages:
                password_msg = await ctx.message.author.send(messages['inkarnate.password'] % new_password)
            self._inkarnate.change_password(secret_value['password'], new_password)
            secret_value['password'] = new_password
            sm_client.update_secret(SecretId='account/inkarnate', SecretString=json.dumps(secret_value))
            await ctx.message.add_reaction('\U00002705')  # :white_check_mark:
            await password_msg.delete(delay=30)

        except ClientError as e:
            await ctx.send(e.response['Error']['Message'])
        except HTTPException as e:
            log.warning(e.response.text, extra=e.asdict())
            await ctx.send(e.response.text)

        if inkarnate_logged:
            try:
                self._inkarnate.logout()
            except HTTPException as e:
                log.warning(e.response.text, extra=e.asdict())
                await ctx.send(e.response.text)

    @command_inkarnate.command()
    async def password(self, ctx: commands.Context):
        """Get inkarnate account password"""
        try:
            sm_client = boto3.client('secretsmanager')
            secret = sm_client.get_secret_value(SecretId='account/inkarnate')
            secret_value = json.loads(secret['SecretString'])
            async with self.config.messages() as messages:
                password_msg = await ctx.message.author.send(messages['inkarnate.password'] % secret_value['password'])
            await ctx.message.add_reaction('\U00002705')  # :white_check_mark:
            await password_msg.delete(delay=30)
        except ClientError as e:
            await ctx.send(e.response['Error']['Message'])
