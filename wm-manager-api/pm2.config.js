module.exports = {
  apps : [{
    name: "manager-api",
    interpreter: "python",
    script: "/opt/project/wm-manager-api/src/__main__.py",
    interpreter_args : "-m debugpy --listen 0.0.0.0:5678",
    watch: "/opt/project/wm-manager-api/src"
  }]
}