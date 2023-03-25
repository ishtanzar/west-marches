
import {jwtVerify} from 'https://cdn.jsdelivr.net/npm/jose@4.10.4/dist/browser/jwt/verify.js';
import {importSPKI} from 'https://cdn.jsdelivr.net/npm/jose@4.10.4/dist/browser/key/import.js';
import {JOSEError} from 'https://cdn.jsdelivr.net/npm/jose@4.10.4/dist/browser/util/errors.js';

const JWT_KANKA_TOKEN = 'kankaAccessToken'
const key = '-----BEGIN PUBLIC KEY-----\n' +
    'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvHB5TCg/Ix0y7dgNZ7P2\n' +
    'cESBLyVL1qzmVDD05J/HeX6emCdD/3Jsvsf1FLMhff6DOWlVFBrDpJYK0lmDn+mO\n' +
    '6DPRxT9fMlypdZ1Iycog9E9PRHcDf5uK7mPrRqU7ccxsWm4PgaUzEvYpp2BuGdYn\n' +
    'bzTs4GI2K88Oj1PtpCTSF2rwctnNX82q4a2n+1jauDn6F7w8yfbuV3RU8koZuNJl\n' +
    'Mz+0hdNdzk2yo8qrwkscswjjlMJoLlQmOsRA+TghCY6G/MpL17QGdgBMljmUhC1A\n' +
    '5lh3EIE+Zd5n1cmlsUSglg+Fx9n1WKQiHaBajINGu1H9n2ESVFRDijQwfOMcnRtB\n' +
    'OwIDAQAB\n' +
    '-----END PUBLIC KEY-----\n';

let _kankaToken;

export class WestMarches {

    async initialize() {
        const jwt = Cookies.get('jwt');

        try {
            const spki = await importSPKI(key, 'RS256');
            const {payload, protectedHeader} = await jwtVerify(jwt, spki);

            if(JWT_KANKA_TOKEN in payload) _kankaToken = payload[JWT_KANKA_TOKEN];
        } catch (e) {
            if(e instanceof JOSEError) {
                console.log(`${e.code}: ${e.message}`);
            } else {
                console.log(`${e.message}`);
            }
        }

        return this;
    }

    get kankaToken() {
        return _kankaToken;
    }

    static async build() {
        return await (new this()).initialize();
    }

}
