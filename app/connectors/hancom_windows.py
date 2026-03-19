from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Union


def fill_hancom_template(
    template_path: Union[str, Path],
    payload_json_path: Union[str, Path],
    output_path: Union[str, Path],
) -> None:
    """Windows + Hancom Office COM connector.

    This connector is intentionally optional and is not exercised in CI.
    It expects placeholder text in the Hancom document and replaces them
    with values from payload_json_path["template_placeholders"].
    """

    if platform.system().lower() != "windows":
        raise RuntimeError("Hancom COM connector requires Windows environment")

    try:
        import win32com.client  # type: ignore
    except ImportError as exc:  # pragma: no cover - windows only dependency
        raise RuntimeError("pywin32 is required for Hancom COM integration") from exc

    template_path = Path(template_path)
    payload_json_path = Path(payload_json_path)
    output_path = Path(output_path)

    with payload_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    placeholders = payload.get("template_placeholders", {})

    hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")  # pragma: no cover
    hwp.XHwpWindows.Item(0).Visible = False  # pragma: no cover
    hwp.Open(str(template_path))  # pragma: no cover

    for placeholder, value in placeholders.items():  # pragma: no cover
        hwp.HAction.GetDefault("RepeatFind", hwp.HParameterSet.HFindReplace.HSet)
        hwp.HParameterSet.HFindReplace.FindString = str(placeholder)
        hwp.HParameterSet.HFindReplace.ReplaceString = str(value) if value is not None else ""
        hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
        hwp.HAction.Execute("AllReplace", hwp.HParameterSet.HFindReplace.HSet)

    hwp.SaveAs(str(output_path))
    hwp.Quit()
