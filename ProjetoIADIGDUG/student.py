import asyncio
import getpass
import json
import os
import websockets
from consts import Direction
import math
import heapq
import random

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Loop do cliente exemplo."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receber informações sobre propriedades estáticas do jogo
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        digdug_dir = Direction.EAST
        
        while True:
            try:
                state = json.loads(await websocket.recv())
                key = " "
                if "digdug" in state and "enemies" in state and len(state["enemies"]) > 0 and "rocks" in state: #se o digdug, os inimigos e as rochas estiverem no estado
                    digdug_pos = state["digdug"]                                         #posição do digdug
                    for enemy in state["enemies"]:                                       #para cada inimigo
                            distance = heuristic(digdug_pos,state["digdug"],state["enemies"])   #calcula a distancia entre o digdug e o inimigo
                            path = search_tree(digdug_pos, state)                            #calcula o caminho entre o digdug e o inimigo
                            closest_enemy_dist=distance                                      #distancia do inimigo mais proximo
                            
                            if path is not None and tuple(path[0]) == tuple(enemy["pos"]):  #se o caminho não for nulo e a posição do inimigo for igual ao primeiro elemento do caminho
                                closest_enemy = enemy                                       #o inimigo mais proximo é o inimigo
                                break   
                                       
                    key, digdug_dir = agent_move(state, digdug_pos, digdug_dir, closest_enemy, closest_enemy_dist)  #chama a função agent_move
                    key, digdug_dir = against_rock(digdug_pos, key, digdug_dir,state["rocks"],closest_enemy)    #chama a função against_rock
                    
                await websocket.send(json.dumps({"cmd": "key", "key": key}))

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return
def agent_move(state, digdug_pos, digdug_dir, closest, closest_enemy_dist):
    key = " "
    if pooka_traversing(closest):                                                      #se o pooka estiver em "traverse"
        if closest_enemy_dist<4:                                                       #se o pooka estiver perto
            key, digdug_dir = run_away_from_pooka(digdug_pos, closest) #corre
            return key, digdug_dir                                                     #retorna a key e a direção
    if (state["level"] <= 6) or (state["level"] >= 7 and len(state["enemies"]) >= 3):  #se o nivel for menor que 6 ou maior que 7 e o numero de inimigos for maior ou igual a 3
        if two_enemies_on_same_position(state,closest):                                #se tiverem dois inimigos na mesma posição
            if closest_enemy_dist > 7:                                                 #se a distancia do inimigo mais proximo for maior que 7
                return " ", digdug_dir                                                 #fica parado
            else:
                key, digdug_dir = run_away_from_pooka(digdug_pos, closest)             #se não, corre
                return key, digdug_dir
    if is_fygar(closest):
            if (state["level"] <= 6) or (state["level"] >= 7 and len(state["enemies"]) >= 3): #se o nivel for menor que 6 ou maior que 7 e o numero de inimigos for maior ou igual a 3
                if two_enemies_on_same_position(state,closest):                              #se tiverem dois inimigos na mesma posição
                    if closest_enemy_dist > 7:                                              #se a distancia do inimigo mais proximo for maior que 7
                        return " ", digdug_dir                                             #fica parado
                    else:
                        key, digdug_dir = run_away_from_pooka(digdug_pos, closest)        #se não, corre
                        return key, digdug_dir
            if digdug_pos[1] == closest["pos"][1]:                                         #se o digdug estiver na mesma linha que o inimigo
                if closest_enemy_dist <= 3:                                                #se a distancia do inimigo mais proximo for menor ou igual a 3
                    key, digdug_dir = run_away_from_pooka(digdug_pos, closest)             #corre
                    return key, digdug_dir
                else:
                    if digdug_pos[0] < closest["pos"][0]:                                  # se o digdug estiver à esquerda do inimigo
                        return "s", Direction.SOUTH                                        # Move para baixo
                    else:
                        return "w", Direction.NORTH                                        # Move para cima
            elif digdug_pos[0] == closest["pos"][0]:                                       #se o digdug estiver na mesma coluna que o inimigo
                if closest_enemy_dist > 2 :                                                #se a distancia do inimigo mais proximo for maior que 2
                    if digdug_pos[1] > closest["pos"][1]:                                  #se o digdug estiver abaixo do inimigo
                        return "w", Direction.NORTH                                        #Move para cima
                    else:
                        return "s", Direction.SOUTH                                        #Move para baixo
                else:    
                    key,digdug_dir = agent_shoot(state, digdug_pos, digdug_dir, closest, closest_enemy_dist) #se não, atira
                    return key, digdug_dir
            else:                                                                          #se o digdug não estiver na mesma linha ou coluna que o inimigo
                if state["level"] >= 7:                                                    #se o nivel for maior ou igual a 7
                    if closest_enemy_dist > 2:                                             #se a distancia do inimigo mais proximo for maior que 2
                        if is_moving_vertically(state):                                    #se o inimigo estiver se movendo verticalmente
                            return " ", digdug_dir
                        if digdug_pos[1] != closest["pos"][1]:                             #se o digdug estiver acima ou abaixo do inimigo
                            if digdug_pos[0] < closest["pos"][0]: 
                                return "d", Direction.EAST                                 # Move para a direita
                            else:
                                return "a", Direction.WEST                                 # Move para a esquerda
                else:
                    if closest_enemy_dist > 3:                                             #se a distancia do inimigo mais proximo for maior que 3
                        if is_moving_vertically(state):
                            return " ", digdug_dir                                         #fica parado
                        if digdug_pos[1] != closest["pos"][1]:                             #se o digdug estiver acima ou abaixo do inimigo
                            if digdug_pos[0] < closest["pos"][0]:                          #se o digdug estiver à esquerda do inimigo
                                return "d", Direction.EAST                                 # Move para a direita
                            else:   
                                return "a", Direction.WEST                                 # Move para a esquerda
    else:
        if state["level"] >= 7 and len(state["enemies"]) <= 3:                              #se o nivel for maior ou igual a 7 e o numero de inimigos for menor ou igual a 3
            if closest_enemy_dist <= 3 :                                                    #se a distancia do inimigo mais proximo for menor ou igual a 3
                key, digdug_dir = agent_shoot(state, digdug_pos, digdug_dir, closest, closest_enemy_dist)   #atira
                return key, digdug_dir       
            elif digdug_pos[0] < closest["pos"][0]:                                     #se o digdug estiver à esquerda do inimigo
                    key = "d"                                                           #Move para a direita
                    digdug_dir = Direction.EAST 
            elif digdug_pos[1] < closest["pos"][1]:                                     #se o digdug estiver acima do inimigo
                    key = "s"                                                           #Move para baixo
                    digdug_dir = Direction.SOUTH
            elif digdug_pos[0] > closest["pos"][0]:                                     #se o digdug estiver à direita do inimigo
                    key = "a"                                                           #Move para a esquerda
                    digdug_dir = Direction.WEST
            elif digdug_pos[1] > closest["pos"][1]:                                     #se o digdug estiver abaixo do inimigo
                    key = "w"                                                           #Move para cima
                    digdug_dir = Direction.NORTH
            else:
                key, digdug_dir = run_away_from_pooka(digdug_pos, closest)              #se não, corre
        else:
            if closest_enemy_dist <= 3 and closest_enemy_dist > 1:                      #se a distancia do inimigo mais proximo for menor ou igual a 3 e maior que 1
                key, digdug_dir = agent_shoot(state, digdug_pos, digdug_dir, closest, closest_enemy_dist)   #atira
                return key, digdug_dir       
            elif digdug_pos[0] < closest["pos"][0] and closest_enemy_dist > 1:          #se o digdug estiver à esquerda do inimigo e a distancia do inimigo mais proximo for maior que 1
                    key = "d"
                    digdug_dir = Direction.EAST
            elif digdug_pos[1] < closest["pos"][1] and closest_enemy_dist > 1:          #se o digdug estiver acima do inimigo e a distancia do inimigo mais proximo for maior que 1
                    key = "s"
                    digdug_dir = Direction.SOUTH
            elif digdug_pos[0] > closest["pos"][0] and closest_enemy_dist > 1:          #se o digdug estiver à direita do inimigo e a distancia do inimigo mais proximo for maior que 1
                    key = "a"
                    digdug_dir = Direction.WEST
            elif digdug_pos[1] > closest["pos"][1] and closest_enemy_dist > 1:          #se o digdug estiver abaixo do inimigo e a distancia do inimigo mais proximo for maior que 1
                    key = "w"
                    digdug_dir = Direction.NORTH
            else:
                key, digdug_dir = run_away_from_pooka(digdug_pos, closest)              #se não, corre
                
    return key, digdug_dir
def agent_shoot(state, digdug_pos, digdug_dir, closest, closest_enemy_dist):            
    if (state["level"] <= 6) or (state["level"] >= 7 and len(state["enemies"]) >= 3):   #se o nivel for menor que 6 ou maior que 7 e o numero de inimigos for maior ou igual a 3
                if two_enemies_on_same_position(state,closest):                         #se tiverem dois inimigos na mesma posição
                    if closest_enemy_dist > 7:                                          #se a distancia do inimigo mais proximo for maior que 7
                        return " ", digdug_dir
                    else:
                        key, digdug_dir = run_away_from_pooka(digdug_pos, closest)      #se não, corre
                        return key, digdug_dir
    if digdug_pos[1] == closest["pos"][1]:                                              #se o digdug estiver na mesma linha que o inimigo
        if digdug_pos[0] < closest["pos"][0]:                                           #se o digdug estiver à esquerda do inimigo
            if digdug_dir != Direction.EAST:                                            #se o digdug não estiver virado para a direita
                if is_fygar(closest):                                                   #se o inimigo for um fygar
                    if closest_enemy_dist > 3:                                          #se a distancia do inimigo mais proximo for maior que 3
                        return "d", Direction.EAST                                      #Move para a direita
                    else:
                        return "w", Direction.NORTH                                     #Move para cima
                else:
                    if state["level"] >= 7 and len(state["enemies"]) <= 3:              #se o nivel for maior ou igual a 7 e o numero de inimigos for menor ou igual a 3
                        if state["step"] > 2000:                                        #se o step for maior que 2000
                            if closest_enemy_dist >= 1:                                 #se a distancia do inimigo mais proximo for maior ou igual a 1
                                return "d", Direction.EAST                              #Move para a direita
                            else:
                                return "w", Direction.NORTH                             #Move para cima
                        else:   
                            if closest_enemy_dist > 1:                                  #se a distancia do inimigo mais proximo for maior que 1
                                return "d", Direction.EAST                              #Move para a direita
                            else:
                                return "w", Direction.NORTH                             #Move para cima
                    else:
                        if closest_enemy_dist > 2:                                      #se a distancia do inimigo mais proximo for maior que 2
                            return "d", Direction.EAST                                  #Move para a direita
                        else:
                            return "w", Direction.NORTH                                 #Move para cima
            else:
                return "A", digdug_dir                                                  #se não, atira
        elif digdug_pos[0] > closest["pos"][0]:                                         #se o digdug estiver à direita do inimigo
            if digdug_dir != Direction.WEST:                                            #se o digdug não estiver virado para a esquerda
                if is_fygar(closest):                                                   #se o inimigo for um fygar
                    if closest_enemy_dist > 3:                                          #se a distancia do inimigo mais proximo for maior que 3
                        return "a", Direction.WEST                                      #Move para a esquerda 
                    else:
                        return "s", Direction.SOUTH                                     #Move para baixo
                else:
                    if state["level"] >= 7 and len(state["enemies"]) <= 3:              #se o nivel for maior ou igual a 7 e o numero de inimigos for menor ou igual a 3
                        if state["step"] > 2000:                                        #se o step for maior que 2000
                            if closest_enemy_dist >= 1:                                 #se a distancia do inimigo mais proximo for maior ou igual a 1   
                                return "a", Direction.WEST                              #Move para a esquerda
                            else:
                                return "d", Direction.EAST                              #Move para a direita
                        else:
                            if closest_enemy_dist > 1:                                  #se a distancia do inimigo mais proximo for maior que 1
                                return "a", Direction.WEST                              #Move para a esquerda
                            else:
                                return "d", Direction.EAST                              #Move para a direita
                    else:
                        if closest_enemy_dist > 2:                                      #se a distancia do inimigo mais proximo for maior que 2
                            return "a", Direction.WEST                                  #Move para a esquerda
                        else:
                            return "d", Direction.EAST                                  #Move para a direita
            else:
                return "A", digdug_dir                                                  #se não, atira
    if digdug_pos[0] == closest["pos"][0]:                                              #se o digdug estiver na mesma coluna que o inimigo
        if digdug_pos[1] < closest["pos"][1]:                                           #se o digdug estiver acima do inimigo
            if digdug_dir != Direction.SOUTH:                                           #se o digdug não estiver virado para baixo
                if is_fygar(closest):                                                   #se o inimigo for um fygar
                    if closest_enemy_dist > 1:                                          #se a distancia do inimigo mais proximo for maior que 1
                        return "s", Direction.SOUTH                                     #Move para baixo
                    else:
                        return "w", Direction.NORTH                                     #Move para cima
                else:
                    if state["level"] >= 7 and len(state["enemies"]) <= 3:              #se o nivel for maior ou igual a 7 e o numero de inimigos for menor ou igual a 3
                        if state["step"] > 2000:                                        #se o step for maior que 2000
                            if closest_enemy_dist >= 1:                                 #se a distancia do inimigo mais proximo for maior ou igual a 1
                                return "s", Direction.SOUTH                             #Move para baixo
                            else: 
                                return "w", Direction.NORTH                             #Move para cima
                        else:
                            if closest_enemy_dist > 1:                                  #se a distancia do inimigo mais proximo for maior que 1
                                return "s", Direction.SOUTH                             #Move para baixo
                            else: 
                                return "w", Direction.NORTH                             #Move para cima
                    else:
                        if closest_enemy_dist > 2:                                      #se a distancia do inimigo mais proximo for maior que 2
                            return "s", Direction.SOUTH                                 #Move para baixo
                        else: 
                            return "w", Direction.NORTH                                 #Move para cima
            else:
                return "A", digdug_dir                                                  #se não, atira
        elif digdug_pos[1] > closest["pos"][1]:                                         #se o digdug estiver abaixo do inimigo
            if digdug_dir != Direction.NORTH:                                           #se o digdug não estiver virado para cima
                if is_fygar(closest):                                                   #se o inimigo for um fygar
                    if closest_enemy_dist > 1:                                          #se a distancia do inimigo mais proximo for maior que 1
                        return "w", Direction.NORTH                                     #Move para cima
                    else:
                        return "s", Direction.SOUTH                                     #Move para baixo
                else:
                    if state["level"] >= 7 and len(state["enemies"]) <= 3:              #se o nivel for maior ou igual a 7 e o numero de inimigos for menor ou igual a 3
                        if state["step"] > 2000:                                        #se o step for maior que 2000
                            if closest_enemy_dist >= 1:                                 #se a distancia do inimigo mais proximo for maior ou igual a 1
                                return "w", Direction.NORTH                             #Move para cima
                            else: 
                                return "s", Direction.SOUTH                             #Move para baixo
                        else:
                            if closest_enemy_dist > 1:                                  #se a distancia do inimigo mais proximo for maior que 1
                                return "w", Direction.NORTH                             #Move para cima
                            else: 
                                return "s", Direction.SOUTH                             #Move para baixo
                    else:
                        if closest_enemy_dist > 2:                                      #se a distancia do inimigo mais proximo for maior que 2
                            return "w", Direction.NORTH                                 #Move para cima
                        else: 
                            return "s", Direction.SOUTH                                 #Move para baixo
            else:
                return "A", digdug_dir                                                  #se não, atira
    else:
        if is_diagonally_adjacent(digdug_pos,state):                                    #se o digdug estiver diagonalmente adjacente ao inimigo
            if digdug_pos[1] > closest["pos"][1]:                                       #se o digdug estiver abaixo do inimigo
                if digdug_pos[0]> closest["pos"][0]:                                    #se o digdug estiver à direita do inimigo
                    if closest["dir"]== Direction.WEST:                                 #se o inimigo estiver virado para a esquerda
                        key = "w"                                                       #Move para cima
                        digdug_dir = Direction.NORTH                                    #Move para cima
                    elif closest["dir"]==Direction.NORTH:                               #se o inimigo estiver virado para cima
                        key = "a"                                                       #Move para a esquerda
                        digdug_dir=Direction.WEST                                       #Move para a esquerda
                    else:
                        key = "A"                                                       #se não, atira
                elif digdug_pos[0]<closest["pos"][0]:                                   #se o digdug estiver à esquerda do inimigo
                    if closest["dir"]==Direction.EAST:                                  #se o inimigo estiver virado para a direita
                        key = "w"                                                       #Move para cima
                        digdug_dir = Direction.NORTH                                    #Move para cima
                    elif closest["dir"]==Direction.NORTH:                               #se o inimigo estiver virado para cima
                        key = "d"                                                       #Move para a direita
                        digdug_dir=Direction.EAST                                       #Move para a direita
                    else:
                        key = "A"                                                       #se não, atira
            elif digdug_pos[1] < closest["pos"][1]:                                     #se o digdug estiver acima do inimigo
                if digdug_pos[0]> closest["pos"][0]:                                    #se o digdug estiver à direita do inimigo
                    if closest["dir"]== Direction.WEST:                                 #se o inimigo estiver virado para a esquerda
                        key = "s"                                                       #Move para baixo
                        digdug_dir = Direction.SOUTH                                    #Move para baixo
                    elif closest["dir"]== Direction.SOUTH:                              #se o inimigo estiver virado para baixo
                        key = "a"                                                       #Move para a esquerda
                        digdug_dir = Direction.WEST                                     #Move para a esquerda
                    else: 
                        key = "A"                                                       #se não, atira
                elif digdug_pos[0]<closest["pos"][0]:                                   #se o digdug estiver à esquerda do inimigo
                    if closest["dir"]==Direction.EAST:                                  #se o inimigo estiver virado para a direita
                        key = "s"                                                       #Move para baixo
                        digdug_dir = Direction.SOUTH                                    #Move para baixo
                    elif closest["dir"]==Direction.SOUTH:                               #se o inimigo estiver virado para baixo
                        key = "d"                                                       #Move para a direita
                        digdug_dir=Direction.EAST                                       #Move para a direita
                    else:
                        key = "A"                                                       #se não, atira
            else: 
                key= " "                                                                #se não, fica parado
                digdug_dir = digdug_dir 
            return key,digdug_dir
        else:
            return " ",digdug_dir                                                       #se não, fica parado
        
def against_rock(digdug_pos, key, digdug_dir,rocks,enemy):
    for rock in rocks:                                                                              #vamos percorrer cada uma das rochas
        distancia = math.dist(digdug_pos,rock["pos"])
        if (distancia<2):
            if digdug_pos[1]==rock["pos"][1] and (abs(rock["pos"][1]-digdug_pos[1])<1):             #se o digdug esta na mesma linha que a rocha e perto da rocha
                if digdug_dir == Direction.WEST or digdug_dir == Direction.EAST:                    #se o digdug se esta a mexer horizontalmente
                    escolha = (("w",Direction.NORTH),("s",Direction.SOUTH))                         #escolhe uma direção a tomar "w" ou "s"
                    key,digdug_dir = random.choice(escolha)
            elif digdug_pos[0]==rock["pos"][0]:                                                     #se o digdug esta na mesma coluna que a rocha e perto da rocha
                if digdug_dir == Direction.SOUTH and (abs(rock["pos"][0]-digdug_pos[0])<1):         #se o digdug se esta a mexer verticalmente
                    escolha = (("a",Direction.WEST),("d",Direction.EAST))                           #escolhe uma direção a tomar "a" ou "d"
                    key,digdug_dir = random.choice(escolha)             
            elif digdug_pos[1] > rock["pos"][1]:                                                    #se o digdug esta em embaixo da rocha
                if digdug_pos[0]> rock["pos"][0]:                                                   #se o digdug a direita da rocha
                    if digdug_dir == Direction.WEST:                                                #se a proxima posição for debaixo da rocha
                        escolha = (("w",Direction.NORTH),("s",Direction.SOUTH))                     #escolhe uma direção a tomar "w" ou "s"
                        key,digdug_dir = random.choice(escolha)
                elif digdug_pos[0]<rock["pos"][0]:                                                  #se o digdug a esquerda da rcoha
                    if digdug_dir==Direction.EAST:                                                  #se a proxima posição for debaixo da rocha
                        escolha = (("w",Direction.NORTH),("s",Direction.SOUTH))                     #escolhe uma direção a tomar "w" ou "s"
                        key,digdug_dir = random.choice(escolha)
            elif digdug_pos[1] < rock["pos"][1]:                                                    #se o digdug esta em cima da rocha
                if digdug_pos[0]< rock["pos"][0]:                                                   #se o digdug esta a esquerda
                    if enemy["pos"][0]==digdug_pos[0]+1:                                            #se o inimigo esta na coluna a direita do digdug
                        if digdug_dir == Direction.WEST:
                            escolha = (("w",Direction.NORTH),("s",Direction.SOUTH))                 #escolhe uma direção a tomar "w" ou "s"
                            key,digdug_dir = random.choice(escolha)
    return key, digdug_dir    
    
previous_enemy_pos = None            
def is_moving_vertically(state):
    global previous_enemy_pos

    if previous_enemy_pos is None:                                                  # Verifica se é a primeira vez que a função é chamada
        previous_enemy_pos = state['enemies'][0]['pos']                             # Atualiza a posição anterior do inimigo
        return False                                                                # Retorna falso para não atrapalhar o algoritmo

    moving_vertically = previous_enemy_pos[1] != state['enemies'][0]['pos'][1]      # Verifica se o inimigo está se movendo verticalmente

    previous_enemy_pos = state['enemies'][0]['pos']                                 # Atualiza a posição anterior do inimigo

    return moving_vertically                                                        # Retorna se o inimigo está se movendo verticalmente


def is_diagonally_adjacent(digdug_pos, state):
    for enemy in state["enemies"]:                                                  # Verifica se o digdug está diagonalmente adjacente a algum inimigo
        if abs(digdug_pos[0] - enemy["pos"][0]) <= 1 and abs(digdug_pos[1] - enemy["pos"][1]) <= 1: 
            return True                                                             # Retorna verdadeiro se o digdug estiver diagonalmente adjacente a algum inimigo
    return False

def is_fygar(closest):                                                              # Verifica se o inimigo mais próximo é um Fygar
    if closest["name"]=="Fygar":
            return True
    else:
        return False
    
def pooka_traversing(closest):                                                      # Verifica se o Pooka está em "traverse"
    if closest and 'traverse' in closest and closest['traverse'] == True:
        return True
    else:
        return False
    
def run_away_from_pooka(digdug_pos, closest):                                       # Função para fugir do Pooka ou outros inimigos
    if digdug_pos[0] < closest["pos"][0]:                                           #se o digdug estiver à esquerda do inimigo
        if digdug_pos[1] == closest["pos"][1]:                                      #se o digdug estiver na mesma linha que o inimigo
            if closest["dir"] == Direction.WEST:                                    #se o inimigo estiver virado para a esquerda
                if digdug_pos[1] <= 12:                                             #se o digdug estiver acima do meio do mapa
                    return "s", Direction.SOUTH                                     #Move para baixo
                else:
                    return "w", Direction.NORTH                                     #Move para cima
            else:
                return "a", Direction.WEST                                          #Move para a esquerda
        else:
            return "a", Direction.WEST                                              #Move para a esquerda
    elif digdug_pos[1] < closest["pos"][1]:                                         #se o digdug estiver acima do inimigo
        if digdug_pos[0] == closest["pos"][0]:                                      #se o digdug estiver na mesma coluna que o inimigo
            if closest["dir"] == Direction.NORTH:                                   #se o inimigo estiver virado para cima
                if digdug_pos[0] <= 24:                                             #se o digdug estiver à esquerda do meio do mapa
                    return "d", Direction.EAST                                      #Move para a direita
                else:
                    return "a", Direction.WEST                                      #Move para a esquerda
            else:
                return "w", Direction.NORTH                                         #Move para cima
        else:
            return "w", Direction.NORTH                                             #Move para cima
    elif digdug_pos[0] > closest["pos"][0]:                                         #se o digdug estiver à direita do inimigo
        if digdug_pos[1] == closest["pos"][1]:                                      #se o digdug estiver na mesma linha que o inimigo
            if closest["dir"] == Direction.EAST:                                    #se o inimigo estiver virado para a direita
                if digdug_pos[1] <= 12:                                             #se o digdug estiver acima do meio do mapa   
                    return "s", Direction.SOUTH                                     #Move para baixo
                else:
                    return "w", Direction.NORTH                                     #Move para cima
            else:
                return "d", Direction.EAST                                          #Move para a direita
        else:
            return "d", Direction.EAST
    elif digdug_pos[1] > closest["pos"][1]:                                         #se o digdug estiver abaixo do inimigo
        if digdug_pos[0] == closest["pos"][0]:                                      #se o digdug estiver na mesma coluna que o inimigo
            if closest["dir"] == Direction.SOUTH:                                   #se o inimigo estiver virado para baixo
                if digdug_pos[0] <= 24:                                             #se o digdug estiver à esquerda do meio do mapa
                    return "d", Direction.EAST                                      #Move para a direita
                else:
                    return "a", Direction.WEST                                      #Move para a esquerda
            else:
                return "s", Direction.SOUTH                                         #Move para baixo
        else:
            return "s", Direction.SOUTH                                             #Move para baixo
    else:
        return "w", Direction.NORTH                                                 #Move para cima


def two_enemies_on_same_position(state,closest):
    for enemy1 in state["enemies"]:                                                 # Verifica se temos dois inimigos juntos
            if enemy1 != closest and enemy1["name"] == "Fygar" and closest["name"] == "Fygar":    #se forem dois fygar retorna False
                return False
            elif enemy1 != closest and enemy1["pos"] == closest["pos"]:                           #se tiver dois inimigos na mesma posiçao retorna True
                return True
            elif enemy1 != closest and enemy1["pos"][1] == closest["pos"][1] and abs(enemy1["pos"][0] - closest["pos"][0]) <=6: # Verifica se tem dois inimigos na mesma linha e uma distancia inferior ou igual a 6, retorna True
                return True
            elif enemy1 != closest and enemy1["pos"][0] == closest["pos"][0] and abs(enemy1["pos"][1] - closest["pos"][1]) <=6: # Verifica se tem dois inimigos na mesma coluna e uma distancia inferior ou igual a 6, retorna True
                return True
    return False                                                                                            
#------------------------------------------------------------Tree Search------------------------------------------------------------#


def actions(state):                                                                 #retorna as ações possiveis
    actions = []                                                                    #lista de ações
    if state[1] > 0:                                                                #se o digdug não estiver na borda superior
        actions.append(("w", Direction.NORTH))                                      #adiciona a ação de mover para cima
    if state[1] < 25:                                                               #se o digdug não estiver na borda inferior
        actions.append(("s", Direction.SOUTH))                                      #adiciona a ação de mover para baixo
    if state[0] > 0:                                                                #se o digdug não estiver na borda esquerda
        actions.append(("a", Direction.WEST))                                       #adiciona a ação de mover para a esquerda
    if state[0] < 48:                                                               #se o digdug não estiver na borda direita
        actions.append(("d", Direction.EAST))                                       #adiciona a ação de mover para a direita
    
    return actions

def result(state, action):                                                          #retorna o estado resultante de uma ação
    if action[1] == Direction.NORTH:                                                #se a ação for mover para cima
        return (state[0], state[1] - 1)                                             #retorna o estado resultante
    elif action[1] == Direction.SOUTH:                                              #se a ação for mover para baixo
        return (state[0], state[1] + 1)                                             #retorna o estado resultante
    elif action[1] == Direction.WEST:                                               #se a ação for mover para a esquerda
        return (state[0] - 1, state[1])                                             #retorna o estado resultante
    elif action[1] == Direction.EAST:                                               #se a ação for mover para a direita
        return (state[0] + 1, state[1])                                             #retorna o estado resultante

def cost(state, action):                                                            #retorna o custo de uma ação
    return 1                                                                        #custo uniforme de 1

def goal_test(state, enemies):                                                      #verifica se o estado é um estado objetivo
    for enemy in enemies:                                                           #para cada inimigo
        if state[0] == enemy["pos"][0] and state[1] == enemy["pos"][1]:             #se o estado for igual a posição do inimigo
            return True                                                             
    return False    

def is_valid_position(state, child_state):                                          #verifica se o estado é valido
    return child_state[0] >= 0 and child_state[0] <= 48 and child_state[1] >= 0 and child_state[1] <= 25    #se o estado estiver dentro do mapa

def heuristic(child_state,digdug_pos,enemies):                                      #retorna a heuristica de um estado
        distance = float('inf')                                                     #distancia infinita
        for enemy in enemies:                                                       #para cada inimigo
            enemy_distance = math.sqrt((digdug_pos[0] - enemy["pos"][0])**2 + (digdug_pos[1] - enemy["pos"][1])**2) #calcula a distancia entre o digdug e o inimigo
            if enemy_distance < distance:                                           #se a distancia for menor que a distancia atual
                distance = enemy_distance                                           #atualiza a distancia
        return distance                                                             #retorna a distancia

def search_tree(initial_state,state):                                               #retorna o caminho para o estado objetivo
    open_nodes = []                                                                 #lista de nós abertos
    closed_nodes = set()                                                            #conjunto de nós fechados
    heapq.heappush(open_nodes, (0, tuple(initial_state), None))                     #adiciona o estado inicial na lista de nós abertos

    while open_nodes:                                                               #enquanto a lista de nós abertos não estiver vazia
        cost, node, parent = heapq.heappop(open_nodes)                              #remove o nó com menor custo da lista de nós abertos
        if node in closed_nodes:                                                    #se o nó já estiver na lista de nós fechados
            continue

        closed_nodes.add(node)                                                      #adiciona o nó na lista de nós fechados


        if goal_test(node, state["enemies"]):                                       #se o nó for um estado objetivo
            return get_path(node)                                                   #retorna o caminho para o estado objetivo
        

        for action in actions(node):                                                #para cada ação possivel
            child_state = result(node, action)                                      #calcula o estado resultante da ação
            if child_state not in closed_nodes and is_valid_position(node, child_state):
                g_cost = cost + 1                                                   # Assume um custo uniforme de 1 para cada ação
                h_cost = heuristic(child_state,state["digdug"],state["enemies"])    #calcula a heuristica do estado
                f_cost = g_cost + h_cost                                            #calcula o custo total do estado
                heapq.heappush(open_nodes, (f_cost, child_state, node))             #adiciona o estado na lista de nós abertos

    return None

def get_path(goal_state):                                                           #retorna o caminho para o estado objetivo
    path = []                                                                       #lista de estados
    while goal_state :                                                              #enquanto o estado objetivo não for nulo
        path.insert(0, goal_state)                                                  #adiciona o estado na lista de estados
        if len(goal_state) > 3:                                                     #se o estado for um estado filho
            goal_state = goal_state[2]                                              #atualiza o estado objetivo
        else:   
            break   
    return path                                                                     #retorna o caminho para o estado objetivo

    
 

 
# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

#{'level': 1, 'step': 33, 'timeout': 3000, 'player': 'chapelsdev', 'score': 300, 'lives': 3, 'digdug': [15, 11], 
# 'enemies': [{'name': 'Fygar', 'id': 'd40de2d1-fe8d-483a-a327-b3f7b1a7a915', 'pos': [42, 20], 'dir': 3}, 
# {'name': 'Pooka', 'id': '8342eba9-032f-4133-9087-c79ea2a1c806', 'pos': [25, 18], 'dir': 1}], 
# 'rocks': [{'id': '5944be3b-413d-4b75-801c-809871b5538d', 'pos': [41, 11]}], 'ts': 1701554199.091476}
