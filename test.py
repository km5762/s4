from pathlib import Path

test = Path("./root/test/")
test1 = Path("./root/")
test2 = Path("./")
test3 = Path("../")
root = Path("/")

print(test <= test)
