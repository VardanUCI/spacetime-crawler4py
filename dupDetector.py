import hashlib

K = 500

def finger(txt: str) -> str:
    w = txt.split()
    if len(w) < K:
        return ""
    sh = [" ".join(w[i:i+K]) for i in range(len(w) - K + 1)]
    return min(hashlib.sha1(chunk.encode()).hexdigest() for chunk in sh)

cache = set()

def dupDetector(txt: str) -> bool:
    f = finger(txt)
    if not f:
        return False
    if f in cache:
        with open("Logs/Worker.log", "a") as f:
            f.write(f"Detecte These Duplicate: {txt[:50]}\n")
        return True
    cache.add(f)
    return False