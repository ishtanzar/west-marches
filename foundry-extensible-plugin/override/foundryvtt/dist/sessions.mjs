import sessions from "foundry:dist/sessions.mjs";

//authenticateUser

sessions._orig_authenticateUser = sessions.authenticateUser;

sessions.authenticateUser = function(req, res) {
    extensibleFoundry.hooks.call('pre.sessions.authenticateUser', req, res);
    const result = this.authenticateUser(req, res);
    extensibleFoundry.hooks.call('post.sessions.authenticateUser', req, res, result);

    return result;
}

export default sessions;