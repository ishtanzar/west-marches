module.exports = {
  apps : [{
    name: "wm-api-server",
    script: "/opt/project/wm-api/src/main.mjs",
    interpreter_args : "--inspect=0.0.0.0:9228",
    // interpreter_args : "--inspect-brk=0.0.0.0:9228",
    watch: "/opt/project/wm-api/src"
  }]
}