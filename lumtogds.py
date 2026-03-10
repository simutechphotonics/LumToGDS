import PY_klayout
import ansys.lumerical.core as lumapi
import numpy as np
import os #for clearing terminal if ran from python terminal
from numpy import savetxt #for saving layer info for reuse
from numpy import loadtxt #for loading layer info settings
import re #regex library
from pathlib import Path #for check file exists

class LumToGDS:
    def __init__(self):
        self.INPUT_FILENAME = "example/test.fsp"           #STRING: path to file, the root folder is the library directory.
        self.EXPORT_FILENAME = "lumexport.gds"             #STRING: Final file name, saves in the "output" folder
        self.LAYER_UNASSIGNED = 99                         #INT: value to give a layer if it wasn't assigned by the user
        self.DEFAULT_GDS_NAME_TEMP = "output"              #STRING: intermediate file name
        self.HIDE_LUMERICAL = True                         #BOOLEAN: show or hide lumerical interface
        self.LOAD_LAYER_FILE = False                       #BOOLEAN: True to load layer information, false to use python CMD to set layers
        self.LOAD_LAYER_FILENAME = "example/mylayercsv"    #STRING: output file will have .csv extension
        self.SAVE_LAYER_FILE = True                        #BOOLEAN: True to save the generated layer file from the python CMD as .csv
        self.SAVE_LAYER_FILENAME = "example/mylayercsv"    #STRING: Filename to save .csv

    def main(self):
        metadata, dupe, ori, fdtd, original_file, copy_file = self.get_object_metadata()
        layerinfo = self.assign_layerinfo(metadata,dupe,ori)
        self.export2gds(
            fdtd,
            layerinfo,
            metadata,
            dupe,
            ori,
            original_file,
            copy_file
            )
        if PY_klayout.klayout_mergefiles():
            print("Success: Export Complete.")
        else:
            print("Error: Final merge step did not complete.")

    def get_object_metadata(self):
        fdtd = lumapi.FDTD(hide=self.HIDE_LUMERICAL, filename=self.INPUT_FILENAME)
        code = open('LUM_auto_detect.lsf', 'r').read()
        fdtd.eval(code) #loads the function into Lumerical

        #Copy file to prevent messing up original file while traversing the object tree
        original_file = fdtd.get_currentfilename()
        copy_file = fdtd.create_copy_file()

        #get the meta layer data user will assign
        metadata = fdtd.get_objects_info() #calls the function from LSF
        dupedata = fdtd.get_duplicate_layers(metadata) #gets the duplicate layers that will share a meta data entry

        dupe = dupedata[:,1]-1 #lumerical uses index starting at 1, so -1 is necessary
        ori = dupedata[:,0]-1
        dupe = np.delete(dupe,0) #strip of the -1 index that Lumerical cannot remove (index lines up with names of the dictionaries)
        ori = np.delete(ori,0)
        dupe = [int(item) for item in dupe]
        ori = [int(item) for item in ori]

        return metadata,dupe,ori,fdtd,original_file,copy_file

    def assign_layerinfo(self,metadata,dupe,ori):
        #automatically assign the layers based on material, then heights
        #can have a full list of Lumerical's material names, ahve it written that way
        if not self.LOAD_LAYER_FILE:
            layerinfo = self.layerinfo_creator_ui(metadata,dupe,ori)
            #replace any unassigned layers with the default layer number
            for i in range(0,len(layerinfo)):
                if layerinfo[i][0] == None:
                    layerinfo[i][0] = self.LAYER_UNASSIGNED

        #Load an existing layer file
        else:
            if Path(self.LOAD_LAYER_FILENAME+".csv").is_file():
                layerinfo = loadtxt('{}.csv'.format(self.LOAD_LAYER_FILENAME), delimiter=',') #maybe needs fmt="%d" ?
                print("Loading layer from: {}.csv".format(self.LOAD_LAYER_FILENAME))
            else:
                input("Layer Assignemnt File not found. Defaulting to Python UI. Press enter to continue.")
                layerinfo = self.layerinfo_creator_ui(metadata,dupe,ori)
                #replace any unassigned layers with the default layer number
                for i in range(0,len(layerinfo)):
                    if layerinfo[i][0] == None:
                        layerinfo[i][0] = self.LAYER_UNASSIGNED

        if self.SAVE_LAYER_FILE:
            savetxt('{}.csv'.format(self.SAVE_LAYER_FILENAME), layerinfo, delimiter=',',fmt="%d")
            print("Layer Assignment saved to file: {}.csv".format(self.SAVE_LAYER_FILENAME))

        return layerinfo

    def layerinfo_creator_ui(self,metadata,dupe,ori):
        #similar as the GUI wizard, CMD UI asking for layer assignments
        layerinfo = [[0 for i in range(2)] for j in range(len(metadata['material']))]

        for layer in layerinfo:
            layer[0] = None

        #calculate regex range
        rangesupported = True
        table_length = len(metadata['material'])
        regex_obj = ""
        if table_length < 10:
            regex_obj = "([0-{}])".format(int(table_length))
        elif 10 <= table_length < 100:
            tens = str(table_length)[0]
            ones = str(table_length)[1]
            regex_obj = "([0-9]|[1-{}][0-{}])".format(tens,ones)
        elif table_length == 100:
            regex_obj = "([0-9]|[1-9][0-9]|100)"
        else:
            rangesupported = False

        output = 'Command List===\n'+\
            '"X Y"    | Assign layer Y to object X. Datatype remainds untouched. Value up to 100.\n'+\
            '"X Y Z"  | Assign a layer Y and datatype Z to object X. Value up to 100.\n'+\
            '"X none" | Unassign the layer for Object X.\n'+\
            '"done"   | Continue to the next step of exporting with the above layer information.\n'+\
            '==============='

        if rangesupported:
            ui = True
            print("No layerinfo file provided, proceeding with UI to generate.")
            commandoutput=''
        else:
            ui = False
            print("Error: Metadata list to large (100+)")
            input("Enter to quit.")
            exit()

        while ui:
            os.system('cls' if os.name == 'nt' else 'clear') #multi-platform clear terminal

            print(self.layer_table(metadata,dupe,ori,layerinfo))
            print(output+commandoutput)
            commandoutput=''
            command = input("Command: ")
            if command == 'done':
                print("Generating LayerInfo.")
                ui = False

            #assign layer
            elif re.match('^{} ([0-9]|[1-9][0-9]|100)$'.format(regex_obj),command): #regex, match 3 digits for 3 numbers, separated by a space
                command = command.split(' ')
                objectindex = command[0]
                if int(objectindex) == any(dupe):
                    commandoutput = '\nWarning: Layer not applied, Object shares a layer with another object.\n'
                else:
                    layervalue = command[1]
                    commandoutput=''
                    commandoutput = '\nOutput: Object {} assigned with: Layer {}\n'
                    commandoutput = commandoutput.format(objectindex,layervalue)
                    layerinfo[int(objectindex)][0] = int(layervalue)

            #assign layer and datatype
            elif re.match('^{} ([0-9]|[1-9][0-9]|100) ([0-9]|[1-9][0-9]|100)$'.format(regex_obj),command):
                command = command.split(' ')
                objectindex = command[0]
                if int(objectindex) == any(dupe):
                    commandoutput = '\nWarning: Layer not applied, Object shares a layer with another object.\n'
                else:
                    layervalue = command[1]
                    datavalue = command[2]
                    commandoutput=''
                    commandoutput = '\nOutput: Object {} assigned with: Layer {} Datatype {}\n'
                    commandoutput = commandoutput.format(objectindex,layervalue,datavalue)
                    layerinfo[int(objectindex)][0] = int(layervalue)
                    layerinfo[int(objectindex)][1] = int(datavalue)

            else:
                commandoutput = "\nOutput: Command Error.\n"

        return layerinfo

    def layer_table(self,metadata,dupe,ori,layertable):
        #Prints out the layer table information
        header1= "Obj#"
        header1= '{:<7}'.format(header1[:7])
        header2= "Layer"
        header2= '{:<7}'.format(header2) #do not truncate layer:data value
        header3= "Material"
        header3= '{:<30}'.format(header3[:30])
        header4 = "zmin"
        header4= '{:<10}'.format(header4) #zmin and zmax dont truncate
        header5 = "zmax"
        header5= '{:<10}'.format(header5)
        #print(header1+" | "+header2+" | "+header3+" | "+header4+" | "+header5+" | ")
        output = header1+" | "+header2+" | "+header3+" | "+header4+" | "+header5+" | \n"

        for data_index, data in enumerate(metadata['material']):
            for dup_index, dup_data in enumerate(dupe):
                if data_index == dup_data:
                    entry1 = str(data_index)
                    entry1 = '{:<7}'.format(entry1[:7])
                    entry2 = "Obj{}".format(int(ori[dup_index]))
                    entry2 = '{:<7}'.format(entry2[:7])
                    if metadata['material'][data_index] == "<Object defined dielectric>":
                        entry3 = str(metadata['index'][data_index])
                    else:
                        entry3 = str(metadata['material'][data_index])
                    entry3 = '{:<30}'.format(entry3[:30])
                    entry4 = str(metadata['zmin'][data_index])
                    entry4 = '{:<10}'.format(entry4)
                    entry5 = str(metadata['zmax'][data_index])
                    entry5 = '{:<10}'.format(entry5)
                    #print(entry1+" | "+entry2+" | "+entry3+" | "+entry4+" | "+entry5+" | ")
                    output = output +(entry1+" | "+entry2+" | "+entry3+" | "+entry4+" | "+entry5+" | \n")
                else:
                    entry1 = str(data_index)
                    entry1 = '{:<7}'.format(entry1[:7])
                    if str(layertable[data_index][0]) == "None":
                        entry2 = str(layertable[data_index][0])
                    else:
                        entry2 = str(layertable[data_index][0])+":"+str(layertable[data_index][1])
                    entry2 = '{:<7}'.format(entry2)
                    #entry3 = str(metadata['material'][data_index])
                    if metadata['material'][data_index] == "<Object defined dielectric>":
                        entry3 = str(metadata['index'][data_index])
                    else:
                        entry3 = str(metadata['material'][data_index])
                    entry3 = '{:<30}'.format(entry3[:30])
                    entry4 = str(metadata['zmin'][data_index])
                    entry4 = '{:<10}'.format(entry4)
                    entry5 = str(metadata['zmax'][data_index])
                    entry5 = '{:<10}'.format(entry5)
                    #print(entry1+" | "+entry2+" | "+entry3+" | "+entry4+" | "+entry5+" | ")
                    output = output+ (entry1+" | "+entry2+" | "+entry3+" | "+entry4+" | "+entry5+" | \n")

        return output

    def export2gds(self,fdtd,layerinfo,metadata,dupe,ori,original_file,copy_file):
        #A copy of the latter half of the LSF GUI wizard
        #checks if the layer entry is a duplicate, if it is, copy the duplicate's original values
        #if not, write to the format used by Lumerical's export functions
        layer_def = [dict['z':None,'material':None,'layer':None] for _ in range(len(metadata['material']))]
        for i in range(len(metadata['material'])):
            if i==any(dupe):
                 for j in range(len(dupe)):
                     if i==dupe[j]:
                        #update
                        layer_def[i] = {
                            'z':    layer_def[ori[j]]['z'],
                            'material':layer_def[ori[j]]['material'],
                            'layer':layer_def[ori[j]]['layer']
                        }

            else:
                # update
                if metadata['material'][i] == "<Object defined dielectric>": #TEMP SOLUTION, DIELECTRIC
                    layer_def[i] = {
                    'z': (metadata['zmin'][i]+metadata['zmax'][i])/2,
                    'material': metadata['index'][i],
                    'layer': str(layerinfo[i][0])+":"+str(layerinfo[i][1])
                    }
                else:
                    layer_def[i] = {
                    'z': (metadata['zmin'][i]+metadata['zmax'][i])/2,
                    'material': metadata['material'][i],
                    'layer': str(layerinfo[i][0])+":"+str(layerinfo[i][1])
                    }

        #Directory needs to be changed to the libraries one to properly import lumerical's encrypted functions
        thispath = os.path.dirname(os.path.abspath(__file__))
        thispath = thispath.replace(os.sep, '/')
        fdtd.eval("cd('"+thispath+"');")

        #putv can be used to pass variables, this is used here because sometimes LSF method of importing scripts doesn't work in nested functions
        code = open('PY_exportmacro.lsf', 'r').read()
        fdtd.putv('metadata',metadata)
        fdtd.putv('layer_def',layer_def)
        fdtd.putv('gds_filename_temp',self.DEFAULT_GDS_NAME_TEMP)
        fdtd.eval(code) #loads the function into Lumerical

        #remove temporary copy of the fsp file
        code = open('LUM_auto_detect.lsf', 'r').read()
        fdtd.eval(code) #loads the function into Lumerical
        fdtd.remove_copy_file(original_file,copy_file)

if __name__ == "__main__":
    myexport = LumToGDS()
    myexport.main()
