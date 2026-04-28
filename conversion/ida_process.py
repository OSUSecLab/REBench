from idautils import *
from idaapi import *
from idc import *
from idc_bc695 import *
import sys
import idaapi
import idautils
import json

filename = GetInputFile()
decom_buf = list()

idaapi.auto_wait()

#idaapi.load_plugin('hexrays')
#idaapi.load_plugin('hexx64')
idaapi.load_plugin('hexarm')
if not idaapi.init_hexrays_plugin():
    print('Unable to load Hex-rays')

callees = dict()
for function_ea in idautils.Functions():
    f_name = idc.get_func_name(function_ea)
    for ref_ea in idautils.CodeRefsTo(function_ea, 0):
        caller_name = idc.get_func_name(ref_ea)
        callees[str(caller_name)] = callees.get(str(caller_name), set())
        callees[str(caller_name)].add(function_ea)
        #callees[str(caller_name)].add(str(f_name))

output = {}
for function_ea in idautils.Functions():
    var_cnt = 1
    type_cnt = 1
    func_cnt = 1

    orig_var = []
    orig_type = []
    orig_func = []
    temp = {}
    answer = {}
    orig_f_name = idc.get_func_name(function_ea)

    idaapi.set_name(function_ea, 'FUNC' + str(func_cnt), idaapi.SN_FORCE)
    answer['FUNC' + str(func_cnt)] = orig_f_name
    #print ('answer', type(orig_f_name))
    func_cnt += 1

    if orig_f_name in callees:
        for callee in callees[orig_f_name]:
            name = idc.get_func_name(callee)
            idaapi.set_name(callee, 'FUNC' + str(func_cnt), idaapi.SN_FORCE)
            func_cnt += 1
            answer['FUNC' + str(func_cnt)] = name
            orig_func.append(name)

    f = get_func(function_ea)
    try:
        cfunc = decompile(f)
        vuu = open_pseudocode(function_ea, 0)
        if cfunc is None:
            continue

        for v in cfunc.lvars:
            orig_var.append(v.name)
            orig_type.append(v.type())
            #vuu.rename_lvar(v, 'temp_var', True)
            answer['VAR' + str(var_cnt)] = v.name
            answer['TYPE' + str(type_cnt)] = str(v.type())
            v.name = 'VAR' + str(var_cnt)
            tinfo = create_typedef('TYPE' + str(type_cnt))
            var_cnt += 1
            type_cnt += 1
            tt = make_pointer(tinfo)
            v.set_lvar_type(tt)
            v.set_user_name()
            v.set_user_type()

    except Exception as e:
        idaapi.set_name(function_ea, orig_f_name, idaapi.SN_FORCE)
        if orig_f_name in callees:
            idx=0
            for callee in callees[orig_f_name]:
                name = idc.get_func_name(callee)
                idaapi.set_name(callee, orig_func[idx], idaapi.SN_FORCE)
                idx += 1

        for v in cfunc.lvars:
            v.clr_user_name()
            v.clr_user_type()
        print ('error')
        continue

    lines = []
    sv = cfunc.get_pseudocode()

    for sline in sv:
        line = tag_remove(sline.line)
        lines.append(line)

    decomp = '\n'.join(lines)

    idaapi.set_name(function_ea, orig_f_name, idaapi.SN_FORCE)

    if orig_f_name in callees:
        idx=0
        for callee in callees[orig_f_name]:
            name = idc.get_func_name(callee)
            idaapi.set_name(callee, orig_func[idx], idaapi.SN_FORCE)
            idx += 1

    for v in cfunc.lvars:
        v.clr_user_name()
        v.clr_user_type()

    cfunc.reset()

    temp['funcbody'] = decomp
    temp['answer'] = answer

    output[orig_f_name] = temp

#json_object = json.dumps(output, indent=2)
print (filename)
with open(filename + '.json', 'w') as outfile:
    json.dump(output, outfile, indent=2)

print ('Done')
ida_pro.qexit(0)
