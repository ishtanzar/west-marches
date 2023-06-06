
class JoinView {

    /**
     *
     * @param client_id
     * @param redirect_uri
     * @param scopes
     * @param oauth_endpoint
     */
    constructor(client_id, redirect_uri, scopes, oauth_endpoint) {
        this.client_id = client_id;
        this.redirect_uri = redirect_uri;
        this.scopes = scopes;

        this.oauth_endpoint = oauth_endpoint.replace(
            /{([a-zA-Z_]+)}/g,
            function (match, index) {
                return this.hasOwnProperty(index) ? this[index] : match;
            }.bind(this)
        )
    }

    onClick(event) {
        event.preventDefault();

        const width = 500;
        const height = 750;

        const screenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX;
        const screenTop = window.screenTop !== undefined ? window.screenTop : window.screenY;
        const screenWidth = window.innerWidth ? window.innerWidth : document.documentElement.clientWidth ? document.documentElement.clientWidth : screen.width;
        const screenHeight = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight ? document.documentElement.clientHeight : screen.height;

        const left = (screenWidth - width) / 2 + screenLeft;
        const top = (screenHeight - height) / 2 + screenTop;

        console.log(`ExtensibleAuthDiscord | JoinView | Join button clicked, opening Discord OAuth`);

        window.open(
            this.oauth_endpoint,
            "Authorization",
            `width=${width},height=${height},top=${top},left=${left}`
        );
    }

    setupHook(Hooks) {
        if(typeof Hooks !== 'undefined') {
            Hooks.on('oauth-discord', async (access_token, refresh_token, popup_window) => {
                console.log(`ExtensibleAuthDiscord | JoinView | OAuth callback, redirecting to /game`);

                popup_window.close();
                window.location.href = getRoute('game');
            });
            console.log(`ExtensibleAuthDiscord | JoinView | Hook configured`);
        } else {
            console.warn('ExtensibleAuthDiscord | JoinView | No Hooks object found');
        }
    }

}

export class ExtensibleAuthDiscord {

    static JoinView = JoinView;

    static async init() {
        this.configureSettings();

        console.log(`ExtensibleAuthDiscord | Initialized`);
    }

    static configureSettings() {
        game.settings.register("extensibleAuth", "method.discord.enabled", {
            name: "ExtensibleAuth.Discord.Enabled.Name",
            scope: "world",
            type: Boolean,
            config: true
        });

        game.settings.register("extensibleAuth", "method.discord.clientId", {
            name: "ExtensibleAuth.Discord.ClientId.Name",
            scope: "world",
            default: '',
            type: String,
            config: true
        });

        game.settings.register("extensibleAuth", "method.discord.clientSecret", {
            name: "ExtensibleAuth.Discord.ClientSecret.Name",
            scope: "world",
            default: '',
            type: String,
            config: true
        });

        game.settings.register("extensibleAuth", "method.discord.redirectUri", {
            name: "ExtensibleAuth.Discord.RedirectUri.Name",
            scope: "world",
            default: '',
            type: String,
            config: true
        });

        game.settings.register("extensibleAuth", "method.discord.oauthEndpoint", {
            name: "ExtensibleAuth.Discord.OAuthEndpoint.Name",
            scope: "world",
            default: 'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}',
            type: String,
            config: true
        });
    }
}

if(typeof Hooks !== 'undefined') {
    Hooks.once('init', async function() {
        await ExtensibleAuthDiscord.init();
    });
} else {
    console.warn('ExtensibleAuthDiscord | No Hooks object found');
}
