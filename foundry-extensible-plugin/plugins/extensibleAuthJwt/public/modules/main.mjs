
export class ExtensibleAuthJwt {

    static async init() {
        this.configureSettings();

        console.log(`ExtensibleAuthJwt | Initialized`);
    }

    static configureSettings() {
        game.settings.register("extensibleAuth", "method.jwt.enabled", {
            name: "ExtensibleAuth.JWT.Enabled.Name",
            scope: "world",
            default: false,
            type: Boolean,
            config: true
        });

        game.settings.register("extensibleAuth", "method.jwt.shared_key", {
            name: "ExtensibleAuth.JWT.SharedKey.Name",
            scope: "world",
            default: '',
            type: String,
            config: true
        });

        game.settings.register("extensibleAuth", "method.jwt.api_endpoint", {
            name: "ExtensibleAuth.JWT.APIEndpoint.Name",
            scope: "world",
            default: 'http://api:3000',
            type: String,
            config: true
        });

        game.settings.register("extensibleAuth", "method.jwt.api_key", {
            name: "ExtensibleAuth.JWT.APIKey.Name",
            scope: "world",
            default: '',
            type: String,
            config: true
        });
    }

    static setupHook(Hooks) {
        if(typeof Hooks !== 'undefined') {
            Hooks.on('auth-jwt', async (popup_window) => {
                console.log(`ExtensibleAuthJWT Auth callback, redirecting to /game`);

                popup_window.close();
                window.location.href = getRoute('game');
            });
            console.log(`ExtensibleAuthJWT | Hook configured`);
        } else {
            console.warn('ExtensibleAuthJWT | No Hooks object found');
        }
    }


}

if(typeof Hooks !== 'undefined') {
    Hooks.once('init', async function() {
        await ExtensibleAuthJwt.init();
    });
} else {
    console.warn('ExtensibleAuthJwt | No Hooks object found');
}
