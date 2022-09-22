module.exports = {
  apps : [{
    name: "websocket-server",
    script: "/opt/project/wm-websocket-server/src/main.js",
    // interpreter_args : "--inspect=0.0.0.0:9228",
    interpreter_args : "--inspect-brk=0.0.0.0:9228",
    watch: "/opt/project/wm-websocket-server/src"
  }]
}