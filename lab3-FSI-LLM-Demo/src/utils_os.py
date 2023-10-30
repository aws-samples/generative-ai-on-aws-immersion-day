import os
import boto3
import json
import glob
import shutil
from typing import List


def read_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def write_jsonl(path, jl: List[dict]):
    os.makedirs(os.path.dirname(os.path.realpath(path)), exist_ok=True)
    with open(path, "w") as f:
        for j in jl:
            json.dump(j, f, ensure_ascii=False)
            f.write("\n")


def write_json(path, j):
    os.makedirs(os.path.dirname(os.path.realpath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(j, f, ensure_ascii=False)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.realpath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def copy_glob(prefix, dest_dir):
    for file in glob.iglob(prefix):
        shutil.copy2(file, dest_dir)


def dir_size(directory, ext):
    return sum(1 for x in os.listdir(directory) if x.endswith(ext))


def iterate_bucket(s3_path, extension=None):
    assert s3_path.startswith("s3")

    bucket_name = s3_path.split("/")[2]
    directory = "/".join(s3_path.split("/")[3:])

    s3_bucket = boto3.resource("s3").Bucket(bucket_name)

    for file in s3_bucket.objects.filter(Prefix=directory):
        if extension is not None and not file.key.endswith(extension):
            continue
        yield file.key
        
