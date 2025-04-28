# LumToGDS
Lumerical GUI Wizard and Python Library for exporting geometries into GDS format.
Wrapper built around functions released by Lumerical: [Link](https://optics.ansys.com/hc/en-us/articles/1500006203341-GDSII-Export-Automation)
Users can choose to use the Lumerical GUI, or import the library into a Python workflow.

Using the Lumerical GUI (MainLSF.lsf), users can follow the popup wizard's prompt to quickly export:
![GUI](/images/GUI.png)

# Installation
## Python Prerequistes
- [ ] Python 3
- [ ] Klayout Python API 
- [ ] LumAPI
- [ ] numpy

# Installation - Lumerical GUI
1. Open a command prompt and navigate to to the Lumerical Python installation, typically located at `C:\Program Files\Lumerical\vXXX\python`. Replace XXX with version number as necessary.
2. Enter the following command to install the Klayout module: `.\python.exe -m pip install klayout`

# Installation - Python
1. Clone or download this repository and save it to an accessible location.
    - The wrapper refers to the provided files locally, changing any of the files locations relative to each other will require updating the script.
2.  In a command prompt, run the command: `pip install -r requirements.txt` to automatically install the required libraries.

# How to use
- All files must be in the same folder. The relative file hierarchy of `.py`, `.lsf`, and `.lsfx` files MUST remain as is.
- Do not delete the output folder
- File names beginnning with `TEMP_output` and ending with `.gds` in the output folder will be merged into `lumexport.gds` and deleted automatically. To avoid any chance of accidental deletion, please do not save important files in this folder.

## Via LSF
1. Launch Lumerical FDTD and load your .fsp file you wish to extract.
2. In the script editor, load "mainLSF.lsf" and click "Run".
    - A wizard should pop up and provide you with the detected objects for confirmation
    - Follow the wizard instructions and provide the layout layer number that will be assigned to each detected object/material
    - Objects with same material will automatically use the same entry, simplifying the entry process.
    - Objects with the same material and different height will each require an entry.
3. A command-line window should pop up. If the readout confirms successs GDS extraction, you can close the CMD window.
4. Navigate to where you have saved the folder containing the LumToGDS library. Under the "output" folder, you should find your exported file "lumexport.gds"

## Via Python
Example available in `Main.py`.
1. `Import lumtogds`.
2. Create a settings object with the parameters you wish to run the export with.
3. call `main()`
    - If the layer assignment is not loaded from a file, the command-line will provide a UI to create layer assignments.

# Example File
A makefile is provided that generates geoemtries in different situations to demonstrate LumToGDS' functionality.
1. Launch FDTD and load/run the script `example/example_makefile.lsf`
2. Run via the LSF Wizard Method or Python Method.

# FAQ

## Limitations - Geometry Objects
- Geometry objects in the Lumerical object tree MUST have unique names. Same names will be overwritten by newer entries, no error will be prompted.
- Geoemtry objects cannot be nested (e.g. Groups, such as containers, structure groups, analysis groups, etc.). 
Please flatten the whole hierachy for extraction. You may consider copy and pasting the tree into a new FDTD instance by selecting the tree and ctrl+c/ctrl+v into a new FDTD file.

## Same layer objects
To reduce user input, the script will automatically flag an object as same-layer if its properties match another already-defined object. 
All of the below must be satisfied for an object to be detected as same-layer:
- Material data (user defined index or selected material)
- Z position (zmin+zmax/2) are the same.

In all other cases, a layer value will need to be set invidually for objects.
