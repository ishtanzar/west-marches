module.exports = {
  apps : [{
    name: "worker",
    interpreter: "python",
    script: "/opt/project/wm-worker/src/__main__.py",
    // interpreter_args : "-m debugpy --listen 0.0.0.0:5678", // VScode
    // interpreter_args : "/usr/local/lib/python3.10/site-packages/pydevd.py --port 5680 --client 172.17.0.1 --file", // PyCharm
    watch: "/opt/project/wm-worker/src",
    ignore_watch: [
      "__pycache__"
    ]
  }]
}