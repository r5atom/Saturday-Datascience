from datetime import datetime

# helper function
def log_message(fn, msg, verbose):
    with open(fn, 'a+') as fid:
        ts = str(datetime.now())
        fid.write(f'{ts}: {msg}\n')
    if verbose:
        print(msg)
    return

def dump_cfg(fn, cfg):
    msg = f'{fn} has '
    for s in cfg.sections():
        for k in cfg[s].keys():
            msg += f'{s}:{k}:"{cfg[s][k]}", '
    return msg[:-2] # trim last sep