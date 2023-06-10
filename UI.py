import ttkbootstrap as ttk
from ttkbootstrap.constants import *


root = ttk.Window(themename="darkly", size=(500, 500))

autoAlign = False

defaultContainer = root
defaultTab = None

currentRow = 0
currentColumn = 0

def setOptions(alignToCenter):
    global autoAlign
    autoAlign = alignToCenter

def setDefaultContainer(container):
    global defaultContainer
    defaultContainer = container

def setDefaultTab(tab):
    global defaultTab
    defaultTab = tab

class Element():
    def __init__(self, container=None, tab=None):
        if container == None:
            self.Container = defaultContainer
        
            if hasattr(self, 'arguments') and 'master' in self.arguments:
                self.arguments['master'] = defaultContainer



    def getGridArguments(self, sameRow=False, padx=10, pady=5,):
        global currentColumn, currentRow

        if sameRow:
            currentColumn += 1
        else:
            currentRow += 1
            
        if currentColumn == 0 and autoAlign:
            padx = (padx * 2, padx)
        if currentRow == 1:
            pady = (pady * 2, pady)

        if currentColumn > 0 and sameRow == False:
            currentColumn = 0

        if autoAlign:
            position = "E" if currentColumn == 0 else "W"
        else:
            position = 'W'



        self.gridArguments = {
            'row': currentRow, 
            'column': currentColumn, 
            'padx': padx, 
            'pady': pady,
            'sticky': position
        }



class Tab():
    def __init__(self, text, tabSystem=None):
        self.Text = text
        self.TabSystem = tabSystem

        self.Frame = DefaultFrame().Create()
        self.TabSystem.Element.add(child=self.Frame, text=self.Text)


class TabSystem(Element):
    def __init__(self, container=None, sameRow=False):

        self.Container = container

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow)

    def Create(self):
        self.Element = ttk.Notebook(self.Container)
        self.Element.grid(**self.gridArguments)

        return self.Element
    
    def NewTab(self, text):
        frame = DefaultFrame().Create()
        self.Element.add(child=frame, text=text)

        return frame
    

class DefaultFrame(Element):
    def __init__(self, container=None, tab=None, sameRow=False):

        self.Container = container
        

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow)

    def Create(self):
        self.Element = ttk.Frame(self.Container)
        self.Element.grid(**self.gridArguments)

        

        return self.Element

class Frame(Element):
    def __init__(self, text, container=None, tab=None, sameRow=False):

        self.Container = container
        self.Text = text
        

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow)

    def Create(self):
        # if self.Text == "":
        #     self.Element = ttk.Frame(self.Container)
        # else:

        self.Element = ttk.LabelFrame(self.Container, text=self.Text)
        self.Element.grid(**self.gridArguments)

        

        return self.Element

class Label(Element):
    def __init__(self, text, container=None, tab=None, sameRow=False, padx=10, pady=5):
        
        
        self.arguments = {
            'master': container,
            'text': text
        }

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def Set(self, text):
        self.Element.configure(text=text)

    def configure(self, text):
        self.Element.configure(text=text)

    def Create(self):
        self.Element = ttk.Label(**self.arguments)
        self.Element.grid(**self.gridArguments)
        
        return self

class Button(Element):
    def __init__(self, text, function=None, container=None, tab=None, sameRow=False, padx=10, pady=5):

        
        self.arguments = {
            'master': container,
            'text': text,
            'width': 35,
            'command': function,
            'bootstyle': 'outline'
        }

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def Create(self):
        self.Element = ttk.Button( **self.arguments)
        self.Element.grid(**self.gridArguments)

    
        return self.Element

class TextInput(Element):
    def __init__(self, variable=None, callback=None, container=None, tab=None, sameRow=False, padx=10, pady=5, width=36):

        self.Callback = callback        
        self.Variable = variable
        

        self.arguments = {
            'master': container,
            'width': width,
            'textvariable': variable
        }

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def updateVariable(self, event):
        updatedText = event.widget.get()
        self.Variable.set(updatedText)

        if self.Callback:
            self.Callback(updatedText)

    def Create(self):
        self.Element = ttk.Entry(**self.arguments)
        self.Element.grid(**self.gridArguments)

        self.Element.bind('<KeyRelease>', self.updateVariable)

        return self.Element

class Slider(Element):
    def __init__(self, variable=None, min=0, max=100, roundDigits=1, callback=None,  container=None, tab=None, sameRow=False, padx=10, pady=5, length=234):
        
        self.startingValue = variable.get()
        self.roundDigits = roundDigits
        self.callback = callback
        

        self.arguments = {
            'master': container,
            'length': length,
            'from_': min,
            'to': max,
            'variable': variable
        }

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def onChanged(self, value):
        number = round(float(value), self.roundDigits)
        self.Label.Element.configure(text=number)

        if self.callback:
            self.callback(number)

    def Create(self):
        self.Element = ttk.Scale(**self.arguments, command=self.onChanged)
        self.Element.grid(**self.gridArguments)

        
            
        self.Label = Label(self.startingValue, sameRow=True, container=self.arguments['master'])
        self.Label.Create()

        return self.Element

class LeftToggle(Element):
    def __init__(self, text, variable=None, callback=None, container=None, tab=None, sameRow=False, padx=10, pady=5):
 
        self.Container = container
        
        self.arguments = {
            'master': container,
            'text': text,
            'variable': variable,
            'command': callback,
            'bootstyle': 'round-toggle'
        }

        super().__init__(container=container)
        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def Create(self):
        self.Element = ttk.Checkbutton(**self.arguments)
        self.Element.grid(**self.gridArguments)

        

        return self.Element

class Toggle(Element):
    def __init__(self, text, variable=None, callback=None, container=None, tab=None, sameRow=False, padx=10, pady=5):

        self.Text = text
        self.SameRow = sameRow

        self.Container = container

        self.arguments = {
            'text': "",
            'variable': variable,
            'callback': callback,
            'sameRow': True,
        }

        super().__init__(container=container)

    def Create(self):
        Label(text=self.Text, sameRow=self.SameRow, container=self.Container).Create()

        self.Element = LeftToggle(**self.arguments)
        self.Element.Create()

        return self.Element
        
class Dropdown(Element):
    def __init__(self, variable=None, options=[], callback=None, container=None, tab=None, sameRow=False, padx=10, pady=5):

        if container == None:
            container = defaultContainer 

        self.Container = container
        self.Variable = variable
        self.Options = options
        self.Callback = callback   
             

        self.Options.append(self.Options[0])

        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def Create(self):
        self.Element = ttk.OptionMenu(self.Container, self.Variable, *self.Options, command=self.Callback)
        self.Element.grid(**self.gridArguments)

        

        return self.Element
    
class Progressbar(Element):
    def __init__(self, variable=None, bootstyle='success-striped', container=None, tab=None, length=234, sameRow=False, padx=10, pady=5):
 
        if container == None:
            container = defaultContainer 

        self.Container = container
        self.Variable = variable
        

        self.arguments = {
            'master': container,
            'length': length,
            'bootstyle': bootstyle,
            'variable': variable
        }

        super().getGridArguments(sameRow=sameRow, padx=padx, pady=pady)

    def Create(self):
        self.Element = ttk.Progressbar(**self.arguments)
        self.Element.grid(**self.gridArguments)

        

        return self.Element
