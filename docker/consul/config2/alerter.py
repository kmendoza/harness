import datetime as dt
import json
import logging
import os
import pickle
from pathlib import Path
from pprint import pprint
from typing import Any

from data_api.core.types.coercions import PathUtils
from data_api.utils.slack import SlackReportMaker, SlackWebHookNotifier

CONSUL_DATA_ENV = "CONSUL_DATA"
SLACK_HOOK_ENV = "SLACK_WEBHOOK_URL"


logger = logging.getLogger(__name__)


class ConsulNotifierError(Exception):
    pass


class ConsulNotifier:
    def __init__(self, status_pkl_file: str | Path = "/tmp/svc_monitor_status.pkl"):
        self._pkl_path = PathUtils.to_path(status_pkl_file)
        self._previous_state = dict()
        if SLACK_HOOK_ENV in os.environ:
            self._slack_hook = os.environ[SLACK_HOOK_ENV]
            logger.warning(f"using slack hook: {self._slack_hook}")
        else:
            raise ConsulNotifierError(f"No slack hook configured in env variable name {SLACK_HOOK_ENV}")

    def __read_status_pkl(self) -> dict[str, str]:
        if self._pkl_path.exists():
            with open(self._pkl_path, "rb") as f:
                logger.warning(f"Using saved status: {self._pkl_path}")
                return pickle.load(f)
        else:
            logger.warning(f"No saved PKL file: {self._pkl_path}")
            return dict()

    def __save_status_pkl(self, status: dict[str, str]):
        with open(self._pkl_path, "wb") as f:
            pickle.dump(status, f)

    def update_service_status(self, service_status: dict[str, str]) -> dict[str, Any]:
        critical = []
        for svc in service_status:
            id = svc["ServiceID"]
            status = svc["Status"]

            if status == "critical":
                critical.append(id)
            else:
                raise ConsulNotifierError(f"Unknown servicd statsy {status} for service {id}/{svc["ServiceName"]}")
        return {"critical": set(critical)}

    def create_report(self, new_status: dict[str, Any]):
        def compare(level: str):
            if level in self._previous_state:
                prev_bad = self._previous_state[level]
            else:
                prev_bad = set()

            return new_status[level] - prev_bad, prev_bad - new_status[level], prev_bad & new_status[level]

        regressed_critical, progressed_critical, unchanged_critical = compare("critical")

        print(f"{regressed_critical}")
        print(f"{progressed_critical}")
        print(f"{unchanged_critical}")

        report = SlackReportMaker(title="Consul service state monitoring")
        report.add_div()
        report.add_text(
            f":gear: *CONSUL* service monitoring report {':x:' if regressed_critical else ''} "
            f"{':heavy_check_mark:' if progressed_critical else ''}"
        )
        if regressed_critical:
            report.add_div()
            report.add_div()
            report.add_text(":boom: newly *FAILED* services")
            report.add_div()
            for rc in regressed_critical:
                report.add_text(f".....:ladybug:  *{rc}* ")
        if progressed_critical:
            report.add_div()
            report.add_div()
            report.add_text(":green_heart: newly *RECOVERED* services")
            report.add_div()
            for rc in progressed_critical:
                report.add_text(f"    :beetle:  *{rc}* ")
        if unchanged_critical:
            report.add_div()
            report.add_div()
            report.add_text(":broken_heart: still *FAILING* services")
            report.add_div()
            for rc in unchanged_critical:
                report.add_text(f"    :ladybug:  *{rc}* ")

        sn = SlackWebHookNotifier(webhook_uri=self._slack_hook)
        sn.send_report(report)

    def update_from(self):
        self._previous_state = self.__read_status_pkl()
        if CONSUL_DATA_ENV in os.environ:
            json_str = os.environ[CONSUL_DATA_ENV]
            new_status = self.update_service_status(json.loads(json_str))
            self.__save_status_pkl(new_status)
            self.create_report(new_status)


def update():
    print(f"{dt.datetime.now()}: updating")
    cn = ConsulNotifier()
    cn.update_from()


if __name__ == "__main__":
    update()
