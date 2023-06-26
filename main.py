from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager

from Utils import DriverFunctions, ChessUtils, TTkConfigManager
from UI import Label, Slider, Toggle, Button, TabSystem, setDefaultContainer, root, ttk

import time
import os
import math

import urllib.request
import zipfile
import shutil
import threading
import random
import string

from stockfish import Stockfish, StockfishException

ConfigManager = TTkConfigManager()

# config

skillLevelMin = ttk.IntVar(value=16)
skillLevelMax = ttk.IntVar(value=20)

constraintEnabled = ttk.BooleanVar(value=False)
constraintRandomMin = ttk.IntVar(value=500)
constraintRandomMax = ttk.IntVar(value=800)

drawOpponentMoves = ttk.BooleanVar(value=False)
delayBeforeDrawing = ttk.DoubleVar(value=0.5)

autoJoinGame = ttk.BooleanVar(value=True)

depth = ttk.IntVar(value=16)
threads = ttk.IntVar(value=4)
contempt = ttk.IntVar(value=40)
ponder = ttk.BooleanVar(value=True)

ConfigManager.updateCurrentVariables(globals())

engineArguments = {
    'Depth': 16
}

engineOptimization = {
    "Hash": 2 * 1024,
    "Threads": 4,
    "Ponder": True,
    "Contempt": 40,
    "Skill Level": 20
}


stockfishUrl = 'https://files.stockfishchess.org/files/stockfish_15.1_win_x64_avx2.zip'

def downloadStockfish():
    if os.path.exists("stockfish.exe"):
        return
    
    print("No stockfish found, downloading")
    
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'MyApp/1.0')]
    urllib.request.install_opener(opener)

    print("Extracting...")

    urllib.request.urlretrieve(stockfishUrl, "stockfish.zip")
    with zipfile.ZipFile("stockfish.zip", 'r') as file:
        file.extractall("")

    # shutil.unpack_archive("stockfish.zip", "/")

    shutil.move("stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe", "stockfish.exe")

    print("Sucessfully downloaded stockfish")

    shutil.rmtree('stockfish_15.1_win_x64_avx2')
    os.remove("stockfish.zip")

def updateStockfishParams(*args):
    engineOptimization['Threads'] = threads.get()
    engineOptimization['Ponder'] = ponder.get()
    engineOptimization['Contempt'] = contempt.get()

    stockfish.set_depth(depth.get())
    stockfish.update_engine_parameters(engineOptimization)

downloadStockfish()


stockfish = Stockfish(path='stockfish.exe', depth=engineArguments['Depth'])
stockfish.update_engine_parameters(engineOptimization)


chromeDriver = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(chromeDriver))

driverFuncs = DriverFunctions(driver)
driver.get("https://www.chess.com/play/online")

chessUtils = ChessUtils(driver, driverFuncs)

tabSys = TabSystem()
tabSys.Create()

mainTab = tabSys.NewTab("Main")
engineTab = tabSys.NewTab("Engine")
infoTab = tabSys.NewTab("Info")

setDefaultContainer(mainTab)

Toggle('Auto Join Game', variable=autoJoinGame).Create()

# toggle for drawOpponentMoves
Toggle('Draw Opponent Moves', variable=drawOpponentMoves).Create()

Label("Delay Before Drawing: ").Create()
Slider(variable=delayBeforeDrawing, min=0, max=5, sameRow=True).Create()

setDefaultContainer(engineTab)

Toggle('Constraint Enabled', variable=constraintEnabled).Create()

Label("Constraint Random Min: ").Create()
Slider(variable=constraintRandomMin, min=0, max=5000, sameRow=True).Create()

Label("Constraint Random Max: ").Create()
Slider(variable=constraintRandomMax, min=0, max=5000, sameRow=True).Create()

Label("Skill Level Min: ").Create()
Slider(variable=skillLevelMin, min=0, max=20, sameRow=True).Create()

Label("Skill Level Max: ").Create()
Slider(variable=skillLevelMax, min=0, max=20, sameRow=True).Create()

Label("Depth: ").Create()
Slider(variable=depth, min=1, max=20, sameRow=True).Create()

Label("Threads: ").Create()
Slider(variable=threads, min=1, max=8, sameRow=True).Create()

Toggle('Ponder', variable=ponder).Create()

Label("Contempt: ").Create()
Slider(variable=contempt, min=-100, max=100, sameRow=True).Create()

Label("Update Engine Params: ").Create()
Button("Update", function=updateStockfishParams, sameRow=True).Create()

setDefaultContainer(infoTab)

Label("In Game: ").Create()
inGameLabel = Label("", sameRow=True).Create()

Label("Current Task: ").Create()
currentTaskLabel = Label("", sameRow=True).Create()

Label("Player Color: ").Create()
playerColorLabel = Label("", sameRow=True).Create()

Label("Is Player Turn: ").Create()
isTurnLabel = Label("", sameRow=True).Create()

Label("FEN: ").Create()
fenLabel = Label("", sameRow=True).Create()

Label("Get Move Time: ").Create()
getBestMoveLabel = Label("", sameRow=True).Create()

Label("Game Over: ").Create()
gameOverLabel = Label("", sameRow=True).Create()


def nextGameAvailable():
    newGame = driverFuncs.getElement(By.XPATH, "//button[@data-cy='sidebar-game-over-new-game-button']")
    return newGame is not None and newGame.is_displayed(), newGame 

def joinNextGame():
    avalible, button = nextGameAvailable()
    if avalible:
        currentTaskLabel.configure(text="Starting new game")
        button.click()
    else:
        playButton = driverFuncs.getElement(By.XPATH, "//button[@data-cy='new-game-index-play']")
        if playButton is not None and playButton.is_displayed():
            playButton.click()

class Box:
    def __init__(self, position, size, thickness=3, color=(0, 255, 0), opacity=1):
        self.Id = ''.join(random.choices(string.ascii_letters, k=30))
        imageScript = f"""
            const div = Object.assign(document.createElement('div'), {{
                style: `
                    position: absolute;
                    pointer-events: none;

                    left: {position[0] - (size[0] / 2)}px;
                    top: {position[1] - (size[1] / 2)}px;
                    
                    width: {size[0]}px;
                    height: {size[1]}px;

                    border: {thickness}px solid rgba({color[0]}, {color[1]}, {color[2]}, {opacity});
                    background-color: transparent;

                    transform: translate({size[0] / 2}, {size[1] / 2});
                `
                }});

                div.id = '{self.Id}';
                document.body.appendChild(div);
        """
        driver.execute_script(imageScript)

    def Destroy(self):
        script = f"""
            var elem = document.getElementById('{self.Id}');
            if (elem) {{
                elem.remove();
            }}
        """
        driver.execute_script(script)
        pass

class Line:
    def __init__(self, start, end, thickness=3, color=(0, 255, 0), opacity=1):
        self.Id = ''.join(random.choices(string.ascii_letters, k=30))
        imageScript = f"""
            const div = Object.assign(document.createElement('div'), {{
                style: `
                    position: absolute;
                    pointer-events: none;
                    
                    left: {start[0]}px;
                    top: {start[1]}px;
                    
                    width: {math.dist(start, end)}px;
                    height: {thickness}px;

                    transform-origin: 0% 0%;
                    transform: rotate({math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))}deg);

                    border-bottom: {thickness}px solid rgba({color[0]}, {color[1]}, {color[2]}, {opacity});
                `
            }});
            div.id = '{self.Id}';
            document.body.appendChild(div);
        """
        driver.execute_script(imageScript)

    def Destroy(self):
        script = f"""
            var elem = document.getElementById('{self.Id}');
            if (elem) {{
                elem.remove();
            }}
        """
        driver.execute_script(script)

startBox = None
toBox = None

selfDrawings = []
otherDrawings = []

def removeDrawings(drawings):
    for drawing in drawings:
        drawing.Destroy()

def takeTurn():
    global selfDrawings, otherDrawings, stockfish
    
    # try:
        # Get FEN
    fen = chessUtils.getFen()
    stockfish.set_fen_position(fen)

    # Get best move
    start = time.time()

    if constraintEnabled.get():
        randomConstraint = random.randint(constraintRandomMin.get(), constraintRandomMax.get())
        bestMove = stockfish.get_best_move_time(randomConstraint)
    else:
        bestMove = stockfish.get_best_move()

    getBestMoveLabel.Set(f"{round(time.time() - start, 3)}s")
    
    # Make move
    makeMove(bestMove)

    # except StockfishException as err:
    #     print(err, 'Reinitializing stockfish')
    #     stockfish = Stockfish(path='stockfish.exe', depth=engineArguments['Depth'])
    #     stockfish.update_engine_parameters(engineOptimization)

def makeMove(bestMove):
    # Update labels
    fen = chessUtils.getFen()
    fenLabel.Set(fen)
    
    start = bestMove[:2]
    to = bestMove[2:]
    startPiece = stockfish.get_what_is_on_square(start).name.lower().replace("_", " ").title()
    currentTaskLabel.Set(f"Making move: {startPiece} to {to}")
    
    # Drawings
    removeDrawings(otherDrawings)
    removeDrawings(selfDrawings)

    xPosStart, yPosStart, tileSize = chessUtils.getTilePosition(start)
    xPosTo, yPosTo, _ = chessUtils.getTilePosition(to)

    startBox = Box(position=(xPosStart, yPosStart), size=(tileSize, tileSize), color=(0, 255, 0))
    toBox = Box(position=(xPosTo, yPosTo), size=(tileSize, tileSize), color=(0, 255, 0))
    line = Line(start=(xPosStart, yPosStart), end=(xPosTo, yPosTo), color=(0, 255, 0))

    selfDrawings.append(startBox)
    selfDrawings.append(toBox)
    selfDrawings.append(line)

    # Move piece
    chessUtils.clickAtPosition(start)
    chessUtils.clickAtPosition(to)

    # Check if move is a promotion move
    pieceToMove = stockfish.get_what_is_on_square(start)
    if (int(to[1]) == 1 or int(to[1]) == 8) and 'pawn' in pieceToMove.name.lower():
        print("promoting")
        promotePiece()
        print("done promoting")

colors = [
    (19, 233, 224),
    (77, 177, 255), 
    (189, 239, 92)
]

bestMoves = None

def getMovesAsync():
    global bestMoves
    oldDepth = int(stockfish.depth)

    stockfish.set_depth(6)
    stockfish.set_skill_level(20)
    bestMoves = stockfish.get_top_moves(3)
    stockfish.set_depth(oldDepth)

def drawOpponentPieces(playerColor):
    global otherDrawings, selfDrawings

    # setStockfishArgs(oponnentStockfishArgs)
    stockfish.set_elo_rating(3500)

    fen = chessUtils.getFen()
    stockfish.set_fen_position(fen)

    threading.Thread(target=getMovesAsync).start()

    chessUtils.PlayerColor = playerColor
    
    while bestMoves is None:
        if chessUtils.isPlayerTurn():
            return
        pass

    # stockfish.set_depth(6)
    # moves = stockfish.get_top_moves(3)
    # stockfish.set_depth(stockfishArgs['depth'])

    # chessUtils.PlayerColor = playerColor
    # if chessUtils.isPlayerTurn():
    #     return

    removeDrawings(otherDrawings)
    removeDrawings(selfDrawings)

    for i, move in enumerate(bestMoves):
        move = move['Move']

        start = move[:2]
        to = move[2:]

        xPosStart, yPosStart, tileSize = chessUtils.getTilePosition(start)
        xPosTo, yPosTo, _ = chessUtils.getTilePosition(to)

        color = colors[i]
        opacity = 1 #opacities[i]

        startBox = Box(position=(xPosStart, yPosStart), size=(tileSize, tileSize), color=color, opacity=opacity)
        toBox = Box(position=(xPosTo, yPosTo), size=(tileSize, tileSize), color=color, opacity=opacity)
        line = Line(start=(xPosStart, yPosStart), end=(xPosTo, yPosTo), color=color, opacity=opacity)

        otherDrawings.append(startBox)
        otherDrawings.append(toBox)
        otherDrawings.append(line)

def promotePiece():
    window = driver.find_element(By.CLASS_NAME, 'promotion-window')
    pieces = window.find_elements(By.CLASS_NAME, 'promotion-piece')

    for piece in pieces:
        if 'q' in piece.get_attribute('class'):
            piece.click()
            break

def main():
    global otherDrawings, selfDrawings, stockfish, chessUtils

    currentGameUrl = ""
    while True:
        try:
            inGameLabel.Set(str(chessUtils.isGameOver() == False))

            removeDrawings(otherDrawings)
            removeDrawings(selfDrawings)

            time.sleep(1)
            
            chessUtils.PlayerColor, _ = chessUtils.getColor()
            chessUtils.Board = driver.find_element(By.CLASS_NAME, 'board')

            chessUtils.Pieces = None
            chessUtils.Coordinates = None
            
            playerColorLabel.configure(text=chessUtils.PlayerColor)

            currentGameUrl = driver.current_url


            if autoJoinGame.get():
                gameAvailable, _ = nextGameAvailable()
                if gameAvailable:
                    driver.refresh()
                    time.sleep(5)
                    joinNextGame()

            gameOverLabel.Set(str(chessUtils.isGameOver()))
            chessUtils.NumMoves += 1

            while chessUtils.isGameOver() == False and driver.current_url != "https://www.chess.com/play/online":
                os.system('cls')
                inGameLabel.Set(str(chessUtils.isGameOver() == False))

                # setStockfishArgs(stockfishArgs)
                
                if chessUtils.isPlayerTurn():

                    randomLevel = random.randint(skillLevelMin.get(), skillLevelMax.get())
                    stockfish.set_skill_level(randomLevel)

                    currentTaskLabel.Set(f"Making move, Depth: {stockfish.depth}, Skill Level: {randomLevel}")
                    chessUtils.NumMoves += 1
                    takeTurn()

                    # print(drawOpponentMoves.get())

                    if drawOpponentMoves.get():
                        print("drawing opponent's moves")

                        start = time.time()

                        while time.time() - start < delayBeforeDrawing.get():
                            if chessUtils.isPlayerTurn() == False:
                                continue
                            else:
                                break
                        
                        currentTaskLabel.Set("drawing opponent's moves")

                        oldColor = chessUtils.PlayerColor
                        otherPlayerColor = "white" if chessUtils.PlayerColor == "black" else "black"

                        chessUtils.PlayerColor = otherPlayerColor

                        drawOpponentPieces(oldColor)

                        chessUtils.PlayerColor = oldColor
                        currentTaskLabel.Set("Waiting for opponent's move") 

                    else:
                        time.sleep(0.1)

                else:

                    currentTaskLabel.Set("Waiting for opponent's move")

                    while chessUtils.isPlayerTurn() == False:
                        if chessUtils.isGameOver():
                            break
                        pass


                if chessUtils.isGameOver():
                    break

        except StockfishException as err:
            print(err, 'Reinitializing stockfish')
            stockfish = Stockfish(path='stockfish.exe', depth=engineArguments['Depth'])
            stockfish.update_engine_parameters(engineOptimization)

        except (NoSuchElementException, StaleElementReferenceException, StockfishException, ElementNotInteractableException, TypeError):
            pass




threading.Thread(target=main).start()
root.mainloop()

driver.quit()
ConfigManager.updateStoredVariables(globals())
