"""Update the manifest file."""
import sys
import json
import os


def update_manifest():
    """Update the manifest file."""
    version = "0.0.0"
    for index, value in enumerate(sys.argv):
        if value in ["--version", "-V"]:
            version = sys.argv[index + 1]

    with open(f"{os.getcwd()}/custom_components/flichub/manifest.json") as manifestfile:
        manifest = json.load(manifestfile)

    manifest["version"] = version

    with open(
        f"{os.getcwd()}/custom_components/flichub/manifest.json", "w"
    ) as manifestfile:
        manifestfile.write(json.dumps(manifest, indent=4, sort_keys=False))

    # print output
    print("# generated manifest.json")
    for key, value in manifest.items():
        print(f"{key}: {value}")

update_manifest()