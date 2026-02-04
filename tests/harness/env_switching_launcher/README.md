### Environment switching launcher tests
----

Core behaviour of these tests is to test the features of an environment switching launcher. Basic premise of this launcher is that it can attempt to use, create or update a specified target environment, using Conda or Pip specifications. If the target environnment requirements can be satisfied, the launcher then switches the python process to one that runs with a specified environment and proceeds to run the rest of the launcher.

Configuration allows for Several modes of how the env switching launcer can be run. 

Note that the environment switching launcher is also a 'Repo' launcher.

Note that the word 'environment' in this context refers to a Conda/Mamba Python environment.

----
#### Detail
----
In order to 'switch' environments, the intended target needs to be launched in a new python process but with a reduced launcher (i.e. without the Repo and Env part). So we write a bit of new code on the fly and launch it with the `conda run` command:

```python
from bqm.harness.file_launcher import FileLauncher
FileLauncher(config="{cfg_file}")
```

This is essentially just a launcher switch but after the Repo and Env steps have been performed alreeady.

----
#### Environment section of the config
```json
{
    "env": {
        ...
    }
}
```
----
#### Strict mode
----
- specify target environment name
- if environment exists, swithc the python process to use it and run the rest of the launcher
- otherwise, exit with an error
