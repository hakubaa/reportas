import subprocess
import imp
import importlib
import sys
import inspect
import ctypes


def pdftotext(path, layout=True, first_page=None, last_page=None):
    '''Runs pdftotext command and intercepts output & errors.''' 
    args = ["pdftotext", path, "-"]
    if layout: args.append("-layout")
    if first_page: args.extend(("-f", str(first_page)))
    if last_page: args.extend(("-l", str(last_page)))

    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def load_module(name, attach = False, force_reload = True):
    '''Load dynamically module.'''
    if name in sys.modules and force_reload:
        module = imp.reload(sys.modules[name])
    else:
        module = importlib.import_module(name)
    if attach:
        calling_frame = inspect.stack()[1][0]
        calling_frame.f_locals.update(
            { attr: getattr(module, attr) for attr in dir(module) 
                                          if not attr.startswith("_") }
        )
        ctypes.pythonapi.PyFrame_LocalsToFast(
                ctypes.py_object(calling_frame), ctypes.c_int(0))
    return module