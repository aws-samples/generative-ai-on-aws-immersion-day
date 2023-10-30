import re
from itertools import product
from operator import itemgetter


def dedup(xs):
    seen = set()
    seen_add = seen.add
    return [x for x in xs if not (x in seen or seen_add(x))]


def text_get_number(text, default):
    res = re.findall(r"\d+", text)
    return res[0] if res else default


def tokenize(text):
    tokens = re.split(r" and | at | the | of |[\,\;\(\)]", text)
    tokens = [re.sub(r"\bthe", "", x) for x in tokens]
    tokens = [x.strip() for x in tokens]
    tokens = [x for x in tokens if x]
    return dedup(tokens)


def spans_of_tokens_ordered(text, tokens):
    """
    Get most compact span of text 
    containing tokens preserving the order of tokens
    Returns a list of offsets [i,j]
    """

    # Backtracking
    def bfs(text, tokens, path, solutions):

        if not tokens:
            solutions += (path,)
        elif not text:
            pass
        else:
            t = tokens[0]

            after = path[-1][0] if path else 0
            indices = [
                (m.start(), m.end()) for m in re.finditer(t, text, flags=re.IGNORECASE)
            ]
            indices = [(i, j) for i, j in indices if i >= after]

            for i, j in indices:
                bfs(text, tokens[1:], path + [(i, j)], solutions)

    # Collect all solutions
    solutions = []
    bfs(text, tokens, [], solutions)

    # Most compact solution
    solution = min(solutions, key=lambda xs: xs[-1][1] - xs[0][0], default=[])
    return solution


def spans_of_tokens_compact(text, tokens):
    """
    Find most compact span containing all the tokens.
    Returns a list of offsets [i,j]
    """

    occurrences = [
        [(m.start(), m.end()) for m in re.finditer(t, text, flags=re.IGNORECASE)]
        for t in tokens
    ]

    solutions = product(*occurrences)
    solutions = [s for s in solutions if len(s) == len(tokens)]
    if not solutions:
        return []

    ranges = [
        (min(s, key=itemgetter(0)), max(s, key=itemgetter(0)), i)
        for i, s in enumerate(solutions)
    ]

    # Most compact range
    compact = min(ranges, key=lambda xs: xs[1][1] - xs[0][0])
    i = compact[2]
    return sorted(solutions[i], key=itemgetter(0))
