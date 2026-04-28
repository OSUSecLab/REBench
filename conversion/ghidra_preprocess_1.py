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
from ghidra.program.model.data import TypedefDataType, Structure, StructureDataType, Array, Union, TypeDef
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import Program
from ghidra.framework.options import Options
import os
import json
import signal

number = os.path.basename(__file__).replace('ghidra_preprocess_', '')
number = number.replace('.py', '')

program = getCurrentProgram()
program.setImageBase(toAddr(0), 0)
function = getFirstFunction()
ifc = DecompInterface()
ifc.openProgram(program)
origtype = None


func_idx = 1

answer = {}
while function is not None:
    funcname = function.name

    startaddr = str(function.getEntryPoint().toString())
    functype = function.getReturnType()
    answer[startaddr] = {}
    answer[startaddr][startaddr] = [str(funcname), str(functype)]

    called_funcs = function.getCalledFunctions(ConsoleTaskMonitor())

    # Function
    for called_func in called_funcs:
        called_funcname = called_func.name
        called_funcaddr = called_func.getEntryPoint().toString()
        answer[startaddr][str(called_funcaddr)] = str(called_funcname)

    results = ifc.decompileFunction(function, 3, ConsoleTaskMonitor())
    if results.decompileCompleted():
        high_func = results.getHighFunction()
        symbol_table = high_func.getGlobalSymbolMap()
        for symbol in symbol_table.getSymbols():
            if symbol.isGlobal():
                answer[startaddr][str(symbol.getSymbol().getAddress().toString())] = str(symbol.getName())

    locals = function.getAllVariables()

    for idx in range(len(locals)):
        if locals[idx].getSymbol() != None:
            answer[startaddr][str(locals[idx].getMinAddress().toString())] = [str(locals[idx].getName()), str(locals[idx].getDataType().getName())]

    def extract_primitives(dt, name, stack, answer):
        size = 0
        if isinstance(dt, Structure):
            while True:
                if size >= dt.getLength():
                    return stack, answer
                comp = dt.getComponentContaining(size)

                if comp == None:
                    size += 1
                    temp = 'Stack[' + str(hex(stack)) + ']'
                    answer[startaddr][temp] = ["undefined", "undefined"]
                    stack -= 1
                    continue

                comp_dt = comp.getDataType()
                if isinstance(comp_dt, Structure):
                    #print ('strcture structure detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += comp_dt.getLength()
                elif isinstance(comp_dt, Union):
                    #print ('strcture union detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += comp_dt.getLength()
                elif isinstance(comp_dt, Array):
                    #print ('strcture array detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += comp_dt.getLength()
                else:
                    if isinstance(comp_dt, TypeDef):
                        #print ('strcture typedef detected')
                        temp = 'Stack[' + str(hex(stack_addr)) + ']'
                        answer[startaddr][temp] = [str(name), str(comp_dt.getBaseDataType().getName())]
                        stack -= 1
                        size += 1
                    else:
                        size += 1
                        temp = 'Stack[' + str(hex(stack)) + ']'
                        answer[startaddr][temp] = [str(comp.getFieldName()), str(comp_dt.getName())]
                        stack -= 1
        elif isinstance(dt, Union):
            union_dt_list= []
            union_name_list= []
            for union_dt in dt.getComponents():
                if isinstance(union_dt.getDataType(), TypeDef):
                    #print ('union typedef')
                    union_dt_list.append(str(union_dt.getDataType().getBaseDataType().getName()))
                else:
                    union_dt_list.append(str(union_dt.getDataType().getName()))
                union_name_list.append(str(union_dt.getFieldName()))

            while True:
                if size >= dt.getLength():
                    return stack, answer

                size += 1
                temp = 'Stack[' + str(hex(stack)) + ']'
                answer[startaddr][temp] = ['union', 'union', union_name_list, union_dt_list]
                stack -= 1

        elif isinstance(dt, Array):
            while True:
                if size >= dt.getLength():
                    return stack, answer
                comp_dt = dt.getDataType()

                if isinstance(comp_dt, Structure):
                    #print ('Array Structure detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += dt.getElementLength()
                elif isinstance(comp_dt, Union):
                    #print ('Array union detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += dt.getElementLength()
                elif isinstance(comp_dt, Array):
                    #print ('Array array detected')
                    stack, answer = extract_primitives(comp_dt, name, stack, answer)
                    size += dt.getElementLength()
                else:
                    if isinstance(comp_dt, TypeDef):
                        #print ('Array typedef detected')
                        temp = 'Stack[' + str(hex(stack_addr)) + ']'
                        answer[startaddr][temp] = [str(name), str(comp_dt.getBaseDataType().getName())]
                        stack -= 1
                        size += 1
                    else:
                        temp = 'Stack[' + str(hex(stack)) + ']'
                        answer[startaddr][temp] = [str(name), str(comp_dt.getName())]
                        stack -= 1
                        size += 1


    stack_addr = 0
    while True:
        var = function.getStackFrame().getVariableContaining(stack_addr)
        if var != None:
            if isinstance(var.getDataType(), Structure):
                #print ('data structure found')
                stack_addr, answer = extract_primitives(var.getDataType(), str(var.getName()), stack_addr, answer)
            elif isinstance(var.getDataType(), Union):
                #print ('union structure found')
                stack_addr, answer = extract_primitives(var.getDataType(), str(var.getName()), stack_addr, answer)
            elif isinstance(var.getDataType(), Array):
                #print ('array structure found')
                stack_addr, answer = extract_primitives(var.getDataType(), str(var.getName()), stack_addr, answer)
            elif isinstance(var.getDataType(), TypeDef):
                #print ('typedef found')
                temp = 'Stack[' + str(hex(stack_addr)) + ']'
                answer[startaddr][temp] = [str(var.getName()), str(var.getDataType().getBaseDataType().getName())]
                stack_addr -= 1
            else:
                temp = 'Stack[' + str(hex(stack_addr)) + ']'
                answer[startaddr][temp] = [str(var.getName()), str(var.getDataType().getName())]
                stack_addr -= 1
        else:
            stack_addr -= 1

        if -stack_addr > function.getStackFrame().getFrameSize():
            break

    function = getFunctionAfter(function)


with open("temp_" + str(number) + ".json", 'w') as fp:
    json.dump(answer, fp, indent=2)
