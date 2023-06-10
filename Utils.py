from ttkbootstrap.constants import *
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import ttkbootstrap as ttk

import time
import json

characterMap = {
    'a': 1,
    'b': 2,
    'c': 3,
    'd': 4,
    'e': 5,
    'f': 6,
    'g': 7,
    'h': 8
}

reverseCharacterMap = characterMap.copy()
reverseCharacterMap = {v: k for k, v in reverseCharacterMap.items()}


class DriverFunctions():
    def __init__(self, driver):
        self.Driver = driver

    def getElement(self, by, value, parent=None) -> WebElement:
        try:
            if parent == None:
                parent = self.Driver
                
            return parent.find_element(by, value)
        except NoSuchElementException:
            return None

    def waitForElement(self, by, value) -> WebElement:
        element = None
        while element == None:
            element = self.getElement(by, value)
        return element
    
class ChessUtils:
    def __init__(self, driver: WebDriver, driverFunctions):
        self.driver = driver
        self.driverFuncs = driverFunctions

        self.PlayerColor = ''
        self.Board = None

        self.NumMoves = 0

        self.Pieces = None
        self.Coordinates = None

        # self.CanCastle = True

        self.Actions = ActionChains(driver, duration=0)

    def isInt(self, var):
        try:
            int(var)
            return True
        except:
            return False
    
    def inGame(self):
        try:    
            self.driver.execute_script("return game")
            return True
        except JavascriptException:
            return False
    
    def getColor(self):
        element = self.driverFuncs.getElement(By.CLASS_NAME, 'flipped')
        if element != None:
            return 'black', 'b'
        else:
            return 'white', 'w'
    
    def getMilisecondsFromTime(self, text):
        if "." in text:
            seconds, miliseconds = text.split('.')
            seconds = seconds.replace(':', '')

            milliseconds = (int(seconds) * 1000) + int(miliseconds)

            return int(milliseconds)
        else:
            minutes, seconds = text.split(':')
            milliseconds = (int(minutes) * 60000) + (int(seconds) * 1000)

            return int(milliseconds)

    def getClocks(self):
        clock1 = self.driver.find_element(By.CLASS_NAME, 'clock-white')
        clock2 = self.driver.find_element(By.CLASS_NAME, 'clock-black')

        return clock1, clock2
    
    def getTimeRemaining(self):
        clock1, clock2 = self.getClocks()

        whiteTime = clock1.find_element(By.CLASS_NAME, 'clock-time-monospace').text
        blackTime = clock2.find_element(By.CLASS_NAME, 'clock-time-monospace').text

        return self.getMilisecondsFromTime(whiteTime), self.getMilisecondsFromTime(blackTime)

    def isGameOver(self):
        gameOverElement = self.driverFuncs.getElement(By.CLASS_NAME, 'game-over-header-component')
        evalBar = self.driverFuncs.getElement(By.CLASS_NAME, "evaluation-bar-fill")

        if evalBar != None and evalBar.is_displayed():
            return True

        if gameOverElement != None and gameOverElement.is_displayed():
            return True
        return False

    def isPlayerTurn(self):
        # if both clocks are greyed out, wierd bug with chess.com
        clock1 = self.driver.find_element(By.CLASS_NAME, 'clock-white')
        clock2 = self.driver.find_element(By.CLASS_NAME, 'clock-black')

        if (clock1.value_of_css_property('opacity') == clock2.value_of_css_property('opacity')) and self.PlayerColor == 'white':
            return True

        # actual check
        playerClock = self.driver.find_element(By.CLASS_NAME, 'clock-' + self.PlayerColor)

        if playerClock.value_of_css_property('opacity') == "1":
            return True
        else:
            return False
    
    def getWhosMoving(self):
        playerColor, _ = self.getColor()

        if playerColor == 'black' and self.isPlayerTurn(playerColor):
            return 'black', 'b'
        else:
            return 'white', 'w'
    
    def getNumMoves(self):
        # moves = self.driver.find_elements(By.CLASS_NAME, 'move')
        # highestMove = 1
        # for move in moves:
        #     blackMove = self.driverFuncs.getElement(By.CLASS_NAME, 'black', parent=move)
        #     if blackMove: # check if black has made their move            
        #         moveNumber = int(move.get_attribute('data-whole-move-number'))

        #         if moveNumber > highestMove:
        #             highestMove = moveNumber
        moveList = self.driver.find_element(By.CLASS_NAME, 'move-list-move-list')

        return len(moveList.find_elements(By.XPATH, ".//*"))

        return highestMove
    
    def cacheCoordinates(self):
        self.Coordinates = {}
        coordinateContainer = self.driverFuncs.getElement(By.CLASS_NAME, 'coordinates')
        coordinates = coordinateContainer.find_elements(By.XPATH, './/*')

        for coord in coordinates:
            self.Coordinates[coord.text] = coord


    def getCoordinate(self, text) -> WebElement:
        if self.Coordinates == None:
            self.cacheCoordinates()

        return self.Coordinates[text]
       
    def getPieces(self, color=None):
        self.Pieces = {}

        if color == None:
            color = self.PlayerColor

        elements = self.Board.find_elements(By.CLASS_NAME, 'piece')

        for piece in elements:
            tileNumber = piece.get_attribute('class')

            if tileNumber == 'element-pool': # something weird
                continue

            pieceCharacters = None

            for name in tileNumber.split():
                if 'square' in name:
                    tileNumber = name[-2:]
                if len(name) == 2:
                    pieceCharacters = name

            tileX = int(tileNumber[0])
            tileY = 9 - int(tileNumber[1])

            if pieceCharacters == None or len(pieceCharacters) <= 0:
                continue

            pieceCharacter = pieceCharacters[-1]
            pieceColor = pieceCharacters[-2]

            self.Pieces[(tileX, tileY)] = pieceCharacter.upper() if pieceColor == 'w' else pieceCharacter.lower() # upper the character if its white else lower it

        return self.Pieces


    def getFen(self, color=None):

        if color == None:
            color = self.PlayerColor

        self.Pieces = self.getPieces(color)

        """
        pieces = {}

        for piece in elements:
            tileNumber = piece.get_attribute('class')

            if tileNumber == 'element-pool': # something weird
                continue

            pieceCharacters = None

            for name in tileNumber.split():
                if 'square' in name:
                    tileNumber = name[-2:]
                if len(name) == 2:
                    pieceCharacters = name

            tileX = int(tileNumber[0])
            tileY = 9 - int(tileNumber[1])

            if pieceCharacters == None or len(pieceCharacters) <= 0:
                continue

            pieceCharacter = pieceCharacters[-1]
            pieceColor = pieceCharacters[-2]

            pieces[(tileX, tileY)] = pieceCharacter.upper() if pieceColor == 'w' else pieceCharacter.lower() # upper the character if its white else lower it 
        """

        # assemble the fen
        fen = ""

        # assemble the board
        for y in range(1, 9):
            for x in range(1, 9):

                if (x, y) in self.Pieces: # if the piece is there, append it to the string
                    fen = fen + self.Pieces[(x, y)]
                    continue

                if len(fen) <= 0: # if string is empty
                    fen = fen + "1" # add 1
                    continue

                lastCharacter = fen[-1]

                if self.isInt(lastCharacter): # if the last character is a number, increase it
                    newNumber = str(1 + int(lastCharacter))
                    fen = fen[:-1] + newNumber
                    continue

                fen = fen + "1"
            fen = fen + "/"

        # remove the extra / at the end
        fen = fen[:-1]


        # add the active player (w or b)
        fen = fen + " " + self.PlayerColor[0] 

        # add castling avaliblity (none for now)
        fen = fen + " -"

        # add en passanting avalibility (none for now)
        fen = fen + " -"

        # adding the halfmove clock (since last capture or pawn advance)
        fen = fen + " 0"

        # add the fulmove clock (incremented after black's move)
        fen = fen + " " + str(self.NumMoves)

        return fen

    def getTilePosition(self, position, switchColor=False):
        board = self.Board
        size = board.size['width']

        tileSize = int(size / 8)
        topLeft = (board.location['x'] - (tileSize / 2), board.location['y'] - (tileSize / 2))

        playerColor = self.PlayerColor
        if switchColor:
            playerColor = 'black' if self.PlayerColor == 'white' else 'white'


        xMult = characterMap[position[0]] if playerColor == "white" else 9 - characterMap[position[0]]
        yMult = 9 - int(position[1]) if playerColor == "white" else int(position[1]) 

        xLocation = topLeft[0] + (tileSize * xMult)
        yLocation = topLeft[1] + (tileSize * yMult)

        return xLocation, yLocation, (size / 8.7)

    def clickAtPosition(self, position):
        xLocation = self.getCoordinate(position[0])
        yLocation = self.getCoordinate(position[1])

        self.Actions.move_to_element_with_offset(yLocation, xLocation.location['x'] - yLocation.location['x'], 0).click().perform()

class TTkConfigManager():
    def __init__(self):
        pass
    
    def getClass(self, var: ttk.Variable):
        className = str(var.__class__)
        nameExtra = className.split("tkinter.")[1]
        return nameExtra[:-2]

    def getStoredVariables(self):
        newValues = None
        try:
            with open('config.json') as file:
                newValues = json.loads(file.read())
        except:
            return {}

        return newValues


    def updateStoredVariables(self, globalVars):
        variables = {}

        for name, value in globalVars.items():
            if isinstance(value, ttk.Variable):
                variables[name] = {
                    'type': self.getClass(value),
                    'value': value.get()
                }

        with open('config.json', 'w') as file:
            file.write(json.dumps(variables))

    def updateCurrentVariables(self, globalVars):
        storedVars = self.getStoredVariables()
        newVars = {}

        for name, values in storedVars.items():
            newValue = values['value']
            varType = values['type']

            variableClass = getattr(ttk, varType)

            newVar = variableClass(value=newValue)
            newVars[name] = newVar

        for name, value in newVars.items():
            globalVars[name] = value
