## The Harness

A container for runnnig python code. Launches a python task in an isolated process and provices a HTTP interfact for interacting with that process. The harness provides an interface for:
- *Heartbeat* - ping the harness to return the status of the process and some sumammary statistics
- Commands: *START*, *STOP*, *PAUSE*, *RESUME*, *CONFIG*. Each of these can carry some data
- Status feedback. Returns status explictily sent by the job.
- Killing the job in short order and exiting in an orderly manner.

### Interface
---
The intreface requires a job to extend a class (_Cradle_) and implement a _run_ method as the entrypoint. The service (_Harness_) can communicated with observers via the HTTP and with the job via the Cradle.

#### Impact
In the simplest implementation the job does not need to interact with the Cradle at all. Even a Cradel agnostic implementaion will still provide the heartbeat and kill functionality.

#### Isolation
The Harness runs in complete separatation from the actual job which has its own process. The interface cannot use the job's CPU cycles and thus interfere with it. No limiations are imposed on what a job can do. Interfaces like argument parsing are unchanged. 

#### Parameter passing
Parameters `--harness-config` / `-x `should be reserved for use by the harness and jobs should ignore it. Otherwise parameter parsing is unaffected


### Example
---

The job must implement Cradle

``` python
from bqm.harness import Cradle

class TestJob(Cradle):
    def run(self, *args):
        ... # job code
```

To lauch the harness with our job. Configuration is optional:
``` python
if __name__ == "__main__":
    job = TestJob()
    exit_code = asyncio.run(
        ProcessHarness(
            config={
                "http": {
                    "host": "0.0.0.0",
                    "port": 3000,
                }
            }
        ).main(job)
    )
    sys.exit(exit_code)
```
(This needs to be wrapped up in a function for simplicity)


The interface between the job and the harness:
``` python
from bqm.harness import Command

    msg = self.get_msg()
    if msg["cmd"] == Command.START:
        ...
```

The interface to feed back the status
``` python
    if 1 > 2:
        self.set_status(status={"key": value})
```

### Client interface
From a http client...
``` bash
# Kill:
curl -X GET http://127.0.0.1:2222/kill

# Heartbeat:
curl -X GET http://127.0.0.1:2222/hb

# Start:
curl -X GET http://127.0.0.1:2222/start

# Stop:
curl -X GET http://127.0.0.1:2222/stop

# Pause:
curl -X GET http://127.0.0.1:2222/pause

# Resume:
curl -X GET http://127.0.0.1:2222/resume

# Config:
curl -X POST http://127.0.0.1:2222/config -d "{'target_vol':4.2}"

# get Status:
curl -X GET http://127.0.0.1:2222/status
```

Kill and heartbeat are immedaite methods and do not interact with the job to proceed.