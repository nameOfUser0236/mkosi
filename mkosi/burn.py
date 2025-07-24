# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import sys

from mkosi.config import Args, Config, OutputFormat
from mkosi.log import complete_step, die
from mkosi.run import run
from mkosi.user import become_root_cmd


def run_burn(args: Args, config: Config) -> None:
    if config.output_format not in (OutputFormat.disk, OutputFormat.esp):
        die(f"{config.output_format} images cannot be burned to disk")

    if not args.cmdline:
        die("Please specify a device to burn the image to", hint="For example /dev/disk/by-id/usb-foobar")

    fname = config.output_dir_or_cwd() / config.output

    if len(args.cmdline) != 1:
        die("Expected device argument.")


    print("Getting info on device")
    lsblk_cmd = [
        "lsblk",
        "-o",
        "PATH,LABEL,PARTLABEL,FSTYPE,SIZE,HOTPLUG,MOUNTPOINTS",
        *args.cmdline,
    ]

    run(
        lsblk_cmd,
        stdin=sys.stdin,
        stdout=sys.stdout,
        env=os.environ | config.finalize_environment(),
        log=False,
        sandbox=config.sandbox(
            devices=True,
            relaxed=True,
        ),
    )

    # Confirm prompt
    if args.force == 0:
        yes = ["y", "yes"]
        sys.stdout.write(f"Confirm burn to, {args.cmdline}: [y/N] ")
        confirm = input().lower()
        if confirm not in yes:
            die("Operation canceled, aborting")

    repart_cmd = [
        "systemd-repart",
        "--no-pager",
        "--pretty=no",
        "--offline=yes",
        "--empty=force",
        "--dry-run=no",
        "--definitions=/",
        f"--copy-from={fname}",
        *args.cmdline,
    ]

    with complete_step("Burning 🔥🔥🔥 to medium…", "Burnt. 🔥🔥🔥"):
        run(
            repart_cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            env=os.environ | config.finalize_environment(),
            log=False,
            sandbox=config.sandbox(
                devices=True,
                network=True,
                relaxed=True,
                options=["--same-dir"],
                setup=become_root_cmd(),
            ),
        )
