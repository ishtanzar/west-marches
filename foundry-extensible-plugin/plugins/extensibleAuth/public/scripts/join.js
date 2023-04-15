window.addEventListener("DOMContentLoaded", async function() {
    if (typeof JoinGameForm !== 'undefined') {
        const _JoinGameForm = JoinGameForm;

        class ExtensibleJoinGameForm extends _JoinGameForm {

            constructor(object, options) {
                super(object, options);
            }

            async getData(options) {
                const data = super.getData(options);
                data.auth = await new Promise(resolve => {
                    game.socket.emit('getLoginData', data => {
                        resolve(data);
                    });
                });
                return data;
            }

            async _renderInner(data) {
                data.rendered_methods = await Promise.all(data.auth.methods.map(method => renderTemplate(`templates/auth/${method}.html`, data)));

                return super._renderInner(data);
            }
        }

        JoinGameForm = ExtensibleJoinGameForm;
        console.log(`ExtensibleAuth | JoinGameForm extended`);
    }

});
