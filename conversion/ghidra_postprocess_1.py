#TODO write a description for this script
#@author
#@category _NEW_
#@keybinding
#@menupath
#@toolbar


#TODO Add User Code Here

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.program.model.symbol import SymbolType
from ghidra.util.exception import DuplicateNameException
from ghidra.program.model.data import DataTypeConflictHandler
from ghidra.program.model.data import TypedefDataType, DataType
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import Program

import os
import json
import signal
import re

number = os.path.basename(__file__).replace('ghidra_postprocess_', '')
number = number.replace('.py', '')

program = getCurrentProgram()
program.setImageBase(toAddr(0), 0)
function = getFirstFunction()
ifc = DecompInterface()
ifc.openProgram(program)
funcmngr = currentProgram.getFunctionManager()
dtmanager = currentProgram.getDataTypeManager()
smgr = program.getSymbolTable()

origtype = None

func_idx = 1

with open('temp_' + str(number) + '.json', 'r') as file:
    gt = json.load(file)

file_dict = {}
while function is not None:
    func_dict = {}
    orig_name = []
    answer = {}
    funcname = function.name
    orig_name.append(funcname)
    startaddr = function.getEntryPoint()
    func_count = 1
    function.setName("FUNC" + str(func_count), SourceType.USER_DEFINED)
    #answer["FUNC" + str(func_count)] = funcname

    if str(startaddr.toString()) in gt and str(startaddr.toString()) in gt[str(startaddr.toString())]:
        answer["FUNC" + str(func_count)] = gt[str(startaddr.toString())][str(startaddr.toString())][0]
    else:
        answer["FUNC" + str(func_count)] = 'undefined'

    functype = function.getReturnType()
    typedef = TypedefDataType("TYPE0", function.getReturnType())
    new_datatype = typedef.copy(dtmanager)
    function.setReturnType(new_datatype, SourceType.USER_DEFINED)
    #answer["TPYE0"] = functype.getName()
    if str(startaddr.toString()) in gt and str(startaddr.toString()) in gt[str(startaddr.toString())]:
        answer["TPYE0"] = gt[str(startaddr.toString())][str(startaddr.toString())][1]
    else:
        answer["TPYE0"] = 'undefined'

    func_count += 1

    called_funcs = function.getCalledFunctions(ConsoleTaskMonitor())

    # Function
    for called_func in called_funcs:
        called_funcname = called_func.name
        orig_name.append(called_funcname)
        called_func.setName("FUNC" + str(func_count), SourceType.USER_DEFINED)
        #answer["FUNC" + str(func_count)] = called_funcname
        if str(startaddr.toString()) in gt and str(called_func.getEntryPoint().toString()) in gt[str(startaddr.toString())]:
            answer["FUNC" + str(func_count)] = gt[str(startaddr.toString())][str(called_func.getEntryPoint().toString())]
        else:
            answer["FUNC" + str(func_count)] = 'undefined'

        func_count += 1


    # Varaible name and type
    locals = function.getAllVariables()
    origtypes = []
    orignames = []
    local_count = 1

    for idx in range(len(locals)):
        if locals[idx].getSymbol() != None:
            origtype = locals[idx].getDataType()
            typedef = TypedefDataType("TYPE" + str(local_count), locals[idx].getDataType())
            new_datatype = typedef.copy(dtmanager)
            locals[idx].setDataType(new_datatype, SourceType.USER_DEFINED)
            #answer["TYPE" + str(local_count)] = origtype.getName()
            if str(startaddr.toString()) in gt and str(locals[idx].getMinAddress().toString()) in gt[str(startaddr.toString())]:
                if gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][1] == 'union' and gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][0] == 'union':
                    if len(gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][3]) != 0:
                        answer["TYPE" + str(local_count)] = gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][3][0]
                    else:
                        answer["TYPE" + str(local_count)] = 'undefined'
                else:
                    answer["TYPE" + str(local_count)] = gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][1]
            else:
                answer["TYPE" + str(local_count)] = 'undefined'
            origtypes.append(origtype)

            origname = locals[idx].getName()
            locals[idx].setName("VAR" + str(local_count), SourceType.USER_DEFINED)
            #answer["VAR" + str(local_count)] = origname
            if str(startaddr.toString()) in gt and str(locals[idx].getMinAddress().toString()) in gt[str(startaddr.toString())]:
                if gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][1] == 'union' and gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][0] == 'union':
                    if len(gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][3]) != 0:
                        answer["VAR" + str(local_count)] = gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][2][0]
                    else:
                        answer["VAR" + str(local_count)] = 'undefined'
                else:
                    answer["VAR" + str(local_count)] = gt[str(startaddr.toString())][str(locals[idx].getMinAddress().toString())][0]
            else:
                answer["VAR" + str(local_count)] = 'undefined'
            orignames.append(origname)

            local_count += 1

    results = ifc.decompileFunction(function, 3, ConsoleTaskMonitor())

    global_var = []
    if results.decompileCompleted():
        high_func = results.getHighFunction()
        symbol_table = high_func.getGlobalSymbolMap()
        for symbol in symbol_table.getSymbols():
            if symbol.isGlobal():
                sym = smgr.getGlobalSymbols(symbol.getName())
                if len(sym) == 0:
                    continue
                global_var.append([sym[0], symbol.getName()])
                sym[0].setName("VAR" + str(local_count), SourceType.USER_DEFINED)
                if str(startaddr.toString()) in gt and str(symbol.getSymbol().getAddress().toString()) in gt[str(startaddr.toString())]:
                    answer["VAR" + str(local_count)] = gt[str(startaddr.toString())][str(symbol.getSymbol().getAddress().toString())]
                else:
                    answer["VAR" + str(local_count)] = 'undefined'
                local_count += 1

    if results.getDecompiledFunction() != None:
        dec_res = results.getDecompiledFunction().getC()
        dec_res = dec_res.encode('ascii', 'ignore')
        func_dict['funcbody'] = dec_res

        conflicts = re.findall(r'_conflict\d+', func_dict['funcbody'])
        for conflict in conflicts:
            func_dict['funcbody'] = func_dict['funcbody'].replace(conflict, '')
        func_dict['funcbody'] = func_dict['funcbody'].replace('_conflict', '')

    assembly = ""
    currentInstr = getInstructionContaining(startaddr)
    while currentInstr != None and getFunctionContaining(currentInstr.getAddress()) == function:
        assembly+= currentInstr.toString() + "\n"
        currentInstr = currentInstr.getNext()

    func_dict['assembly'] = assembly

    function.setName(orig_name[0], SourceType.USER_DEFINED)
    function.setReturnType(functype, SourceType.USER_DEFINED)
    i=1
    for called_func in called_funcs:
        called_func.setName(orig_name[i], SourceType.USER_DEFINED)
        i+=1

    i=0
    for idx in range(len(locals)):
        if locals[idx].getSymbol() != None:
            locals[idx].setDataType(origtypes[i], SourceType.USER_DEFINED)
            locals[idx].setName(orignames[i], SourceType.USER_DEFINED)
            i+=1

    for idx in range(len(global_var)):
        global_var[idx][0].setName(global_var[idx][1], SourceType.USER_DEFINED)

    func_dict['answer'] = answer
    file_dict[func_idx] = func_dict
    func_idx += 1
    function = getFunctionAfter(function)

#with open(program.name + "_input.json", 'w') as fp:
with open(str(number) + ".json", 'w') as fp:
    #for func in file_dict:
    #json.dump(func, fp)
    json.dump(file_dict, fp, indent=2)
