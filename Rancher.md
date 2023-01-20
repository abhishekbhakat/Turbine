# Issue
There are issues related to mount on vm.max_map_count for Mac

Change the file `~/Library/Application\ Support/rancher-desktop/lima/_config/override.yaml` to add the following:

```
mountType: 9p
mounts:
  - location: "~"
    9p:
      securityModel: mapped-xattr
      cache: "mmap"
provision:
  - mode: system
    script: |
      #!/bin/sh
      set -o xtrace
      sysctl -w vm.max_map_count=262144
```

Related issues:
- https://github.com/rancher-sandbox/rancher-desktop/issues/1209
- https://github.com/runfinch/finch/issues/131