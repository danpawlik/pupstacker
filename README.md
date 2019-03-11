# Pupstacker

Pupstacker is a tool that generates missing parameters in puppet Openstack
module based on official Openstack module, example:
some parameters that can be set in nova.conf are not available in
puppet-nova module. That tool checks which params are missing.

```
python3 pupstacker.py --project glance
```

Output of the tool will look like:
```
Missing parameters for section:
DEFAULT:
  - some_param
  - some_other_param
scheduler:
  - new_param
```

Project is now in WIP state. Please be patient.
