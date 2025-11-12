"""
Generic.py

This is a template for creating modules that integrate with the DynamicUtilityApp GUI.
The GUI will scan the "Functions" folder, read the comments at the top of this file,
and dynamically create buttons and dropdowns based on them.
"""
''' The main module button in the sidebar'''
#title: 'Generic Module'
'''Single-word button'''       
#btn: 'SingleWord'     
'''Multi-word button, spaces will become underscores in function name'''        
#btn: 'Multi Word Button'      

import random  # for generating example data

# ---------------- Module Class ----------------
class GenericUtility:
    """
    This class will be instantiated by the DynamicUtilityApp.

    - The GUI loader scans the module for the first class defined.
    - It then reads the comments at the top (#title: and #btn:) to build the sidebar.
    """

    def __init__(self):
        """
        Initialize the module.
        Use this method to set up database connections, APIs, or any data loading.
        """
        pass

    # ---------------- Button Getter Functions ----------------
    def get_singleword(self):#must be lowercase
        """
        Getter for the 'SingleWord' button.
        Must return (columns, rows)
        """
        columns = ("ID", "Name", "Value")  # Column headers for the table
        rows = [(i, f"Item {i}", random.randint(1, 100)) for i in range(1, 6)]  # Example rows
        return columns, rows

    def get_multi_word_button(self):#must be lowercase
        """
        Getter for the 'Multi Word Button'
        Spaces in the button name become underscores in the function name.
        Example: 'Tables with Info' -> get_tables_with_info(self)
        """
        columns = ("Category", "Count")
        rows = [("Alpha", 5), ("Beta", 3), ("Gamma", 8)]
        return columns, rows

# ---------------- Optional Standalone Test ----------------
if __name__ == "__main__":
    module = GenericUtility()
    '''for func_name in ["get_singleword", "get_multi_word_button"]:
        cols, rows = getattr(module, func_name)()
        print(f"\n{func_name.upper()}:")
        print(cols)
        for row in rows:
            print(row)'''

# ---------------- Description / Instructions ----------------
"""
HOW TO USE THIS TEMPLATE:

1. File placement:
   - Place this file in the "Functions" folder so DynamicUtilityApp can find it.
   - The GUI automatically scans all .py files in this folder.

2. Metadata comments:
   - #title: 'Module Title'       --> Defines the parent button in the sidebar.
   - #btn: 'Button Name'          --> Each button under the parent dropdown.
   - Must use # (hash) comments, not multi-line strings (''' or "").
   - Each button line must be one line per button.
   - Multi-word buttons: spaces will be converted to underscores for function names.

3. Getter function naming:
   - Single-word button: 'Active'  -> get_active(self)
   - Multi-word button: 'Tables with Info' -> get_tables_with_info(self)
   - Must return (columns, rows) for the GUI to populate the table.
   - Must be lowercase

4. Return format:
   - columns: tuple or list of column headers
   - rows: list of tuples/lists with the data for each row
   - Example: 
        columns = ("ID", "Name", "Value")
        rows = [(1, "Item 1", 42), (2, "Item 2", 15)]

5. Functionality:
   - The DynamicUtilityApp automatically reads each .py file, creates the sidebar buttons,
     and calls the corresponding getter when clicked.
   - This allows anyone to create a new module without touching the main GUI code.

6. Additional tips:
   - Keep #title: and #btn: at the very top of the file.
   - Comments anywhere else are ignored for button generation.
   - Include an optional standalone test block to verify the getter functions.
   - This template is fully expandable: add more #btn: lines and corresponding get_<name>() methods.
"""
