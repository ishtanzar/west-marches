import axios from "axios";

export class OAuthInvalidCodeException extends Error {}

export class OAuthInvalidTokenException extends Error {}

export async function oauth_perform(config, code, redirect_uri) {
    let token_resp, identity_resp;

    try {
        token_resp = await axios.post(
            config.token_endpoint,
            new URLSearchParams({
                client_id: config.client_id,
                client_secret: config.client_secret,
                code: code,
                grant_type: 'authorization_code',
                redirect_uri: redirect_uri
            })
        );
    } catch (e) {
        if (axios.isAxiosError(e)) {
            throw new OAuthInvalidCodeException();
        } else {
            throw e;
        }
    }

    try {
        identity_resp = await axios.get(config.resource_owner_details, {
            headers: {
                Authorization: `Bearer ${token_resp.data.access_token}`
            }
        });

        return {
            identity: identity_resp.data,
            credentials: token_resp.data
        };
    } catch (e) {
        if (axios.isAxiosError(e)) {
            throw new OAuthInvalidTokenException();
        } else {
            throw e;
        }
    }
}