'use strict';

const fetch = require('node-fetch');

class KankaOAuth {

  async fetch_setting(key) {
    const {db} = global;
    return JSON.parse((await db['Setting'].findOne({'key': key})).value)
  }

  async client_id() {
    return this.fetch_setting('wm-foundry-module.kankaClientId');
  }

  async client_secret() {
    return this.fetch_setting('wm-foundry-module.kankaClientSecret');
  }

  async redirect_uri() {
    return this.fetch_setting('wm-foundry-module.kankaRedirectUri');
  }

  async doLogin(req, resp) {
    const code = req.query.code;

    // const oauthResult = await fetch('https://kanka.io/oauth/token', {
    //   method: 'POST',
    //   body: new URLSearchParams({
    //     client_id: await this.client_id(),
    //     client_secret: await this.client_secret(),
    //     code,
    //     grant_type: 'authorization_code',
    //     redirect_uri: await this.redirect_uri(),
    //     // scope: 'identify',
    //   }),
    //   headers: {
    //     'Content-Type': 'application/x-www-form-urlencoded',
    //   }
    // });
    //
    // const oauthData = await oauthResult.json();

    resp.render('kanka-oauth', {
      // 'access_token': oauthData.access_token,
      // 'refresh_token': oauthData.refresh_token
      'access_token': "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI1OCIsImp0aSI6IjM1YjNjMTYzYmY1YjNmOWZlNWRmOTZiZTcwM2Y5OTdhMjkzMTYwZTliNDdhY2JhYmViYTcyNjEyYjQ2Y2Q3YzQ0NjFkZjk1ZThkZDg2NWEwIiwiaWF0IjoxNjI3MzcwMDQwLjYyNzA0OCwibmJmIjoxNjI3MzcwMDQwLjYyNzA1NywiZXhwIjoxNjU4OTA2MDQwLjYwODU5LCJzdWIiOiI2OTE5NiIsInNjb3BlcyI6W119.CsEvNL6CmLqvnf0IBBAcnLthIZD1gja25b4BZpXb3ugKgIpqhNkvICQETR4NSbgEG2_IYRJHXNzXbX84szKZn9I2_1O1X-KBHQPUIepDoE23wRUBPkyN0nNd8XQjiN_f77CGJZcHAb_nCqw_9JrrVEdx3nEUe5tCZiGNavSxrGldKgGbhilRtQke224LoNR_X3xXSciB-n_0Aiah1tNnyoAQZPShy-99tCHbE5qu_Gog1aXTmIoqr5OGggAAK1wDOIhnEnDFwCDyfQWmdGHwJPefaWhO41oNNew9IENFS3xiAmioioHhlxPvXI1U9s-RQjGj4AqHz-fEb_nEUWgF8eQDWcp_f_LRqtgEC3yQj_Et0PFcQSh5dqTAOm24bgOruqjzHiLsOTzfRX8UstsCtJrFw_Q_LIBA7j9dlaZWl-PxrSRCNVsFcNSz3fttx_VmDpyKnimVtX8G56daseZjGfkS1OJgtyUDYlM5OEMsQDSVdwMbcUuy4fNcAwpkKRF51n0oZwnQeZtIyZx7VRe7tCyFKZqgzzxqYkMk8OP0m_zVBm3yq36LK4FkG5kU52c9C-FZMYi6WzLefrnFMSgRqRKgC2VTupZC56cCeTqoEdoixooVOK7dyzHvi0M0EgnlcDV7NXxWfENRWe20iB_tpGcxQ1n3mOsPIXMLSpkC4Js",
      'refresh_token': "def50200c33b4d3fd137a740092823460a230c061c46e1125d156a43505e34fc165ad368415703ec1502fed506303b8f9b69e27355f8b3adf13d7ef000a0574de3b0c9318c046009ab68b40448c6a451b354673ed754dfa2be8d3a308234aa9385427789567f07718129d1b2f8487587ad78faa5f2f31709787460f2dd3ee532755fff9a96e7ec3520fb3d531f6c6b5bd817d1ba16118b772ab1f068581f3c764b68bd1ed39c6da9967872f16d65ce4b4360b04eb76d67a73fa23bfe69acf91026f2a2a0ff6166aca9319b10b933d49958b572807cebfa6447a4ae58bf9fd727fde8bddd518c98f5ffe502328cfbc3195900d0e1f23676a007ca60dbf82d3dd1b47f30fad38eafb4aedad9d37aab3e6a140470b9a2152573b46297c6b17fd149a109faf1cb4590b7e127a8f4df6ffb6300f3f338e6f664ef7b572e08b71071081c2bbcc5a98bf911be86f62700c40cdd6eb17f2712da4612f30ddda6db2cc55a61378474c54d"
    });

    /**
     * {
  "token_type": "Bearer",
  "expires_in": 31536000,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI1OCIsImp0aSI6IjM1YjNjMTYzYmY1YjNmOWZlNWRmOTZiZTcwM2Y5OTdhMjkzMTYwZTliNDdhY2JhYmViYTcyNjEyYjQ2Y2Q3YzQ0NjFkZjk1ZThkZDg2NWEwIiwiaWF0IjoxNjI3MzcwMDQwLjYyNzA0OCwibmJmIjoxNjI3MzcwMDQwLjYyNzA1NywiZXhwIjoxNjU4OTA2MDQwLjYwODU5LCJzdWIiOiI2OTE5NiIsInNjb3BlcyI6W119.CsEvNL6CmLqvnf0IBBAcnLthIZD1gja25b4BZpXb3ugKgIpqhNkvICQETR4NSbgEG2_IYRJHXNzXbX84szKZn9I2_1O1X-KBHQPUIepDoE23wRUBPkyN0nNd8XQjiN_f77CGJZcHAb_nCqw_9JrrVEdx3nEUe5tCZiGNavSxrGldKgGbhilRtQke224LoNR_X3xXSciB-n_0Aiah1tNnyoAQZPShy-99tCHbE5qu_Gog1aXTmIoqr5OGggAAK1wDOIhnEnDFwCDyfQWmdGHwJPefaWhO41oNNew9IENFS3xiAmioioHhlxPvXI1U9s-RQjGj4AqHz-fEb_nEUWgF8eQDWcp_f_LRqtgEC3yQj_Et0PFcQSh5dqTAOm24bgOruqjzHiLsOTzfRX8UstsCtJrFw_Q_LIBA7j9dlaZWl-PxrSRCNVsFcNSz3fttx_VmDpyKnimVtX8G56daseZjGfkS1OJgtyUDYlM5OEMsQDSVdwMbcUuy4fNcAwpkKRF51n0oZwnQeZtIyZx7VRe7tCyFKZqgzzxqYkMk8OP0m_zVBm3yq36LK4FkG5kU52c9C-FZMYi6WzLefrnFMSgRqRKgC2VTupZC56cCeTqoEdoixooVOK7dyzHvi0M0EgnlcDV7NXxWfENRWe20iB_tpGcxQ1n3mOsPIXMLSpkC4Js",
  "refresh_token": "def50200c33b4d3fd137a740092823460a230c061c46e1125d156a43505e34fc165ad368415703ec1502fed506303b8f9b69e27355f8b3adf13d7ef000a0574de3b0c9318c046009ab68b40448c6a451b354673ed754dfa2be8d3a308234aa9385427789567f07718129d1b2f8487587ad78faa5f2f31709787460f2dd3ee532755fff9a96e7ec3520fb3d531f6c6b5bd817d1ba16118b772ab1f068581f3c764b68bd1ed39c6da9967872f16d65ce4b4360b04eb76d67a73fa23bfe69acf91026f2a2a0ff6166aca9319b10b933d49958b572807cebfa6447a4ae58bf9fd727fde8bddd518c98f5ffe502328cfbc3195900d0e1f23676a007ca60dbf82d3dd1b47f30fad38eafb4aedad9d37aab3e6a140470b9a2152573b46297c6b17fd149a109faf1cb4590b7e127a8f4df6ffb6300f3f338e6f664ef7b572e08b71071081c2bbcc5a98bf911be86f62700c40cdd6eb17f2712da4612f30ddda6db2cc55a61378474c54d"
}
     */
  }
}

module.exports = {DiscordOAuth, KankaOAuth};
