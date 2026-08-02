"""
memory.py

Simple user profile memory.
"""

profile = {}


def remember_name(name: str):

    profile["name"] = name


def get_name():

    return profile.get("name")


def remember(key: str, value: str):

    profile[key] = value


def recall(key: str):

    return profile.get(key)


def all_memory():

    return profile