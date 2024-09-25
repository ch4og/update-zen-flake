from github import Github
from packaging.version import parse
import subprocess
import os
import pygit2
import shutil
from dotenv import load_dotenv

_ = load_dotenv()

g = Github(os.getenv("GITHUB_TOKEN"))

flake = g.get_repo("ch4og/zen-browser-flake")
zen = g.get_repo("zen-browser/desktop")

zen_ver = parse(zen.get_latest_release().tag_name)
msg = str(flake.get_commits()[0].commit.message).split()
try:
    flake_ver = parse(msg[2])
except:
    print(f"Error parsing {msg[2]}")
    exit(1)

if zen_ver == flake_ver:
    print("No updates")
    exit(0)

if zen_ver > flake_ver:
    zen_ver = str(zen_ver).replace("a", "-a.")
    flake_ver = str(flake_ver).replace("a", "-a.")

else:
    print("Error")
    exit(1)

print(f"Updating {flake_ver} -> {zen_ver}")

commit_name = f"Update to {zen_ver}"

zen_types = {
    "specific": "0",
    "generic": "0",
}
for zen_type in zen_types.keys():
    url = "https://github.com/zen-browser/desktop/releases/download/{}/zen.linux-{}.tar.bz2".format(
        zen_ver, zen_type
    )
    output = subprocess.check_output(
        "nix-prefetch fetchTarball --url {} --option extra-experimental-features flakes".format(
            url
        ).split()
    )
    hash = output.decode().split()[-1]
    zen_types[zen_type] = hash

repo_path = "../zen-browser-flake"
try:
    clone = pygit2.clone_repository(flake.clone_url, repo_path)
except ValueError:
    shutil.rmtree(repo_path)
    clone = pygit2.clone_repository(flake.clone_url, repo_path)
print(f"Cloned {flake.clone_url}")
flake_file = open(repo_path + "/flake.nix", "r").read()

with open(repo_path + "/flake.nix", "w") as f:
    for i in range(len(flake_file.splitlines())):
        line = flake_file.splitlines()[i]
        a = line
        if "sha256" in line:
            rep_type = (
                flake_file.splitlines()[i - 2].strip().replace('"', "").split()[0]
            )
            if rep_type in zen_types.keys():
                a = line.replace(line.split(":")[1], f'{zen_types[rep_type]}";')
        elif flake_ver in line:
            a = line.replace(flake_ver, zen_ver)
        _ = f.write(a + "\n")

flake_update = subprocess.check_output(f"nix flake update {repo_path}".split())

repo = pygit2.Repository(repo_path)
repo.index.add_all()
repo.index.write()

author = pygit2.Signature(os.getenv("GIT_USER"), os.getenv("GIT_EMAIL"))
commiter = author

parent = [repo.head.peel(pygit2.Commit).id]

tree = repo.index.write_tree()
commit = repo.create_commit("HEAD", author, commiter, commit_name, tree, parent)
print(f"Commited {commit_name}")
_ = subprocess.run(
    [
        "notify-send",
        "-u",
        "normal",
        "-t",
        "1000000",
        "Zen Update",
        f"Commited {commit_name}",
    ],
    check=True,
)
