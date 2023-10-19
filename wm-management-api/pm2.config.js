module.exports = {
  apps : [{
    name: "manager-api",
    interpreter: "python",
    script: "/opt/project/wm-management-api/src/__main__.py",
    // interpreter_args : "-m debugpy --listen 0.0.0.0:5678", // VScode
    interpreter_args : "/usr/local/lib/python3.11/site-packages/pydevd.py --port 5678 --client 172.17.0.1 --file", // PyCharm
    watch: ["/opt/project/wm-management-api/src", "/opt/project/wm-utils/src"],
    ignore_watch: [
        "__pycache__"
    ]
  }]
}