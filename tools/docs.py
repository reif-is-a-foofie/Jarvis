def run(args):
    with open(args["path"], "w") as f:
        f.write(args["content"])
    return {"written": args["path"]}