#!/usr/bin/env python3
from github import Github
import re
import subprocess

g = Github()

flake = g.get_repo("ch4og/zen-browser-flake")
zen = g.get_repo("zen-browser/desktop")

zen_ver = zen.get_latest_release().tag_name
flake_ver = str(flake.get_commits()[0].commit.message).split()[-1]

if flake_ver == zen_ver:
    print("Already up to date")
    exit()

print(f"Updating {flake_ver} -> {zen_ver}")

zen_types = {
    "specific": "0",
    "generic": "0",
}

for zen_type in zen_types.keys():
    url = f"https://github.com/zen-browser/desktop/releases/download/{zen_ver}/zen.linux-{zen_type}.tar.bz2"
    output = subprocess.check_output(f"nix-prefetch-url --unpack {url}".split())
    hash = output.decode().split()[-1]
    zen_types[zen_type] = hash

flake_file = open("flake.nix", "r").read()

with open("flake.nix", "w") as f:
    for i in range(len(flake_file.splitlines())):
        line = flake_file.splitlines()[i]
        a = line
        if line.strip().startswith("sha256"):
            rep_type = flake_file.splitlines()[i - 2].replace('"', "").split()[0]
            if rep_type in zen_types.keys():
                new_hash = "sha256:" + zen_types[rep_type]
                a = str(re.sub(r"sha256:\S+", new_hash, line)) + '";'
        elif flake_ver in line:
            a = line.replace(flake_ver, zen_ver)
        _ = f.write(a + "\n")

_ = subprocess.check_output(f"nix flake update".split())
