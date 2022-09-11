def clean_frame(frame: dict):
    res = {}
    for k, v in frame.items():
        if v is not None:
            res[k] = v
    return res
