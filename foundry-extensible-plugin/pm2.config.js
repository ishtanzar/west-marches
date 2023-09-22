module.exports = {
  apps : [{
    name: "foundrvtt",
    script: "/home/foundry/resources/app/main.mjs",
    // interpreter_args : "--inspect-brk=0.0.0.0:9229 --experimental-vm-modules --loader=/home/foundry/resources/foundry-extensible-plugin/custom-resolver.mjs",
    // interpreter_args : "--inspect=0.0.0.0:9229 --experimental-vm-modules --loader=/home/foundry/resources/foundry-extensible-plugin/custom-resolver.mjs",
    // interpreter_args : "--inspect-brk=0.0.0.0:9229",
    args : "--port=30000 --headless --noupdate --dataPath=/data --extensibleAuthJwt-api-key=changeme_api_admin",
    ignore_watch: ["\.pm2", "healthcheck-cookiejar.txt", "healthcheck-cookiejar\.txt.*"],
    env: {
      // DEBUG: '*,-axm:services:metrics'
    },
    watch: true
  }]
}