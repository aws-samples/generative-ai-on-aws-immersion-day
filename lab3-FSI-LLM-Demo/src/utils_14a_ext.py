from typing import List
import re
import glob
import utils_os


def to_san(filename):
    return filename.split("/")[-1].split(".")[0]


def common_token(xs: List[str]) -> str:
    """
    A list of name variations is given.
    Extract a common token (surname).
    Example:
        "Michael A. Bond Jr.",
        "Michael A. Bond, Jr.",
        "Mr. Bond",
        "Michael A. Bond"
    """

    tokens = [[t for t in re.split(r"\,|\s", x) if len(t) > 2] for x in xs]
    sets = [set(xs) for xs in tokens]
    common = list(set.intersection(*sets))
    return common[0] if common else None


def lookup_member_names(san, folder):

    metafiles2022 = f"{folder}/{san}.*.json"
    print("Reading 2022", metafiles2022)

    members = []
    for fname in glob.iglob(metafiles2022):
        if "label" in fname:
            continue

        print("file", fname)
        j = utils_os.read_json(fname)
        members += (
            {"fullname": j["MEMBER_NAME"], "surname": common_token(j["SURNAMES"])},
        )

    assert members, f"No annotations found for {san}"
    print("Member names:", [x["fullname"] for x in members])
    return members
