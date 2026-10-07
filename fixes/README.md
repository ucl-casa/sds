# Common Fixes

## Windows

### ```crun: controller 'pids' is not available```

Powershell Fix - https://gist.github.com/sjg/482ed10a03b86880c36ae4c0ca90c42e

**Error Message**
```
Error:preparing container X for attach: crun: controller
'pids' is not available under /sys/fs/cgroup/non-systemd/user.slice/user-1000.slice/user@1000.service/user.slice/libpod
-X.scope/container/cgroup.controllers: OCI runtime error
```
*First saw Oct 1st 2026 Install Day*
