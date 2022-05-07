"""
Inside conditions.json, you will see a subset of UNSW courses mapped to their 
corresponding text conditions. We have slightly modified the text conditions
to make them simpler compared to their original versions.

Your task is to complete the is_unlocked function which helps students
determine
if their course can be taken or not. 

We will run our hidden tests on your submission and look at your success rate.
We will only test for courses inside conditions.json. We will also look over
the
code by eye.

NOTE: We do not expect you to come up with a perfect solution. We are more
interested
in how you would approach a problem like this.
"""
import json
from abc import abstractmethod

from typing import List, Set
import string

COURSE_UOC = 6

# NOTE: DO NOT EDIT conditions.json
with open("./conditions.json") as f:
    CONDITIONS = json.load(f)
    f.close()


def is_unlocked(courses_list: List, target_course: str) -> bool:
    """Given a list of course codes a student has taken, return true if the
    target_course
    can be unlocked by them.
    
    You do not have to do any error checking on the inputs and can assume that
    the target_course always exists inside conditions.json

    You can assume all courses are worth 6 units of credit
    """
    completed = set(courses_list)  # type: Set[str]
    requirements = CONDITIONS[target_course]
    transforms = [normalisedStringSpacing, toUpper, stripUnnecessaryWords,
                  normalisedStringSpacing]

    for f in transforms:
        requirements = f(requirements)

    if len(completed) == 0:
        return requirements == ""

    root = parse(requirements)
    return root.eval(completed)


class Node:
    def __init__(self, val: str):
        self.val = val
        self.children = []

    @abstractmethod
    def eval(self, completed: set[str]) -> bool:
        return False


class ValNode(Node):
    def __init__(self, val: str):
        super(ValNode, self).__init__(val)
        self.val = val

    def eval(self, completed: set[str]) -> bool:
        return self.val in completed


class AndNode(Node):
    def __init__(self):
        super(AndNode, self).__init__("AND")
        self.children = []

    def eval(self, completed: set[str]) -> bool:
        return all([child.eval(completed) for child in self.children])


class OrNode(Node):
    def __init__(self):
        super(OrNode, self).__init__("OR")
        self.children = []

    def eval(self, completed: set[str]) -> bool:
        return any([child.eval(completed) for child in self.children])


# Should technically be broken up further
class InNode(Node):
    def __init__(self, val: str):
        super(InNode, self).__init__(val)
        self.matches = None
        self.children = []

    def eval(self, completed: set[str]) -> bool:
        val = int(self.val)
        if not self.children and not self.matches:
            return len(completed) * COURSE_UOC >= val

        result = set()

        for child in self.children:
            if child.val in completed:
                result.add(child.val)

        if self.matches:
            for course in completed:
                if course.startswith(self.matches):
                    result.add(course)

        if len(result) * COURSE_UOC >= val:
            return True

        return False


def parsedInStatements(s: str) -> Node:
    if " IN " not in s:
        if not s.isdigit():
            return ValNode(s)

        node = InNode(s)
        node.matches = ""
        return node

    count, courses = s.split(" IN ")
    courses = courses.strip("()")
    node = InNode(count)

    courseFilter = s.split("LEVEL")
    if len(courseFilter) == 2:
        codeFilter = courseFilter[1].strip()
        node.matches = codeFilter[2:] + codeFilter[0]
    else:
        node.children.extend(
            [ValNode(course) for course in courses.split(", ")]
        )
    return node


def parsedAndOrStatements(s: str) -> Node:
    node = None
    stack = 0
    prevEnd = 0
    i = 0
    s += " "

    while i < len(s):
        if s[i] == "(":
            stack += 1
        elif s[i] == ")":
            stack -= 1

        hitCriticalCheck = s[i:].startswith("AND") \
                           or s[i:].startswith("OR") \
                           or i == (len(s) - 1)

        if stack == 0 and hitCriticalCheck:
            if not node:
                if s[i:].startswith("AND"):
                    node = AndNode()
                elif s[i:].startswith("OR"):
                    node = OrNode()

            substring = s[prevEnd:i].strip()
            if substring.endswith(")") and substring.startswith("("):
                substring = substring[1: -1]

            node.children.append(parse(substring))

            i += len(node.val) - 1
            prevEnd = i + 1

        i += 1
    return node


def parse(s: str) -> Node:
    if "AND" in s or "OR" in s:
        return parsedAndOrStatements(s)
    return parsedInStatements(s)


def tryParseInt(s: str) -> (int, bool):
    if s.isdigit():
        return int(s), True
    return None, False


"""
String Filtering Functions
"""

def normalisedStringSpacing(s: str) -> str:
    return ' '.join(s.split())


def toUpper(s: str) -> str:
    return s.upper()


def stripUnnecessaryWords(s: str) -> str:
    toRemove = ["PRE-REQUISITE", "PREREQUISITE", "PREQUISITE", "PRE-REQS",
                "COMPLETION OF", "UNITS OF CREDIT", "UNITS OC CREDIT",
                ":", "COURSES"]
    for word in toRemove:
        s = s.replace(word, "")

    return s
