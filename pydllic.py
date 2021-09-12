#!/usr/bin/env python
import re
import os


class pydllic():
    # this assumes you write one extern "C" per function
    func_re = re.compile(r'extern\s+"[Cc]"\s+(.*?)\s*\((.*?)\)')
    # type_re assumes there are zero comments in the cpp
    type_re = re.compile(r"struct\s+(.*?)\s*{(.*?)};",
                         re.DOTALL | re.MULTILINE
    )
    # used to remove comments before finding types
    comment_re = re.compile(r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
                            re.DOTALL | re.MULTILINE
    )
    py = """import ctypes


class {name}():

    lib = ctypes.CDLL("{cdll}")
{funcs}

{types}
    """
    func = """
    def {name}(self{in_args}):
        self.lib.{name}.restype = {ret}
        return self.lib.{name}({out_args})"""
    func_addr = """
    def {name}(self{in_args}):
        self.lib.{name}.restype = {ret}
        ret = self.lib.{name}({out_args})
        return {type}.from_address(ret)"""
    struct = """
class {name}(ctypes.Structure):
    _fields_ = {fields}
    {members}

"""

    def get_type(ret):
        if "*" in ret:
            if "char*" in ret.split() or "char" in ret.split():
                return "ctypes.c_char_p"
            else:
                return "ctypes.c_void_p"
        elif "bool" in ret.split():
            return "ctypes.c_bool"
        elif "float" in ret.split():
            return "ctypes.c_float"
        elif "void" in ret.split():
            return "None"
        else:
            return "ctypes.c_int"

    def remove_comments(text):
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return " "
            else:
                return s

        return re.sub(pydllic.comment_re, replacer, text)


def build_file(cdef, out_file):
    py_types = []
    for k, v in cdef["types"].items():
        py_types.append(pydllic.struct.format_map({
            "name": k,
            "fields": "["+",\n                ".join([f"('{m[0]}', {m[1]})" for m in v])+"]",
            "members": "\n    ".join([f"{m[0]} = None" for m in v])
        }
        ))

    py_funcs = []
    for k, v in cdef["functions"].items():
        arg_str = ", ".join(v["args"]) if v["args"] else ""
        fdict = {
            "name": k,
            "ret": v["type"],
            "in_args": ", "+arg_str if arg_str else "",
            "out_args": arg_str
        }
        if v["ret"].replace("*", "") in types:
            fdict["type"] = v["ret"].replace("*", "")
            func_str = pydllic.func_addr.format_map(fdict)
        else:
            func_str = pydllic.func.format_map(fdict)
        py_funcs.append(func_str)

    py_file = pydllic.py.format_map({
        "name": cname,
        "cdll": args.dll,
        "funcs": "\n".join(py_funcs),
        "types": "\n".join(py_types)
    })
    with open(out_file, "w") as out_file:
        out_file.write(py_file)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dll', action='store', type=str, help='dll to link import with ctypes', required=True)
    parser.add_argument('files', action='store', nargs="*", type=str, help='files parsed by pydllic ')
    args = parser.parse_args()
    cdef = {}
    funcs = {}
    types = {}
    cdef["functions"] = funcs
    cdef["types"] = types
    cname = os.path.basename(args.dll).split(".")[0]
    out_file = args.dll.replace(".", "_")+".py"
    for in_file in args.files:
        with open(in_file) as in_file:
            lines = in_file.read()
            lines = pydllic.remove_comments(lines)
            functions = pydllic.func_re.findall(lines)
            for func in functions:
                ret, fname = func[0].rsplit(' ', 1)
                funcs[fname] = {"ret": ret}
                funcs[fname]["args"] = [x.rsplit(" ")[-1] for x in func[1].split(',') if x.rsplit(" ")[-1]]
                funcs[fname]["type"] = pydllic.get_type(ret)

            for match in pydllic.type_re.findall(lines):
                name, members = match
                members = members.split(";")
                members = [m.strip() for m in members]
                members = [m.split("=")[0] for m in members]
                members = [m.rsplit() for m in members]
                members = [(m[-1], pydllic.get_type(m[-2])) for m in members if m]
                types[name] = members

    build_file(cdef, out_file)
