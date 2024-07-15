import os
import io
import sys
import json
import ftplib
import shutil
import requests
import argparse
import mcstatus
from nbt import nbt
import PySimpleGUI as sg


def get_player_info(player_file: nbt.NBTFile) -> dict:
    """
    Get the health, hunger, and dimension of a player.
    
    :param player_file: The player file
    :return dict: The player information
    """

    player_info: dict = {}

    player_info['health'] = player_file['Health'].value
    player_info['hunger'] = player_file['foodLevel'].value
    player_info['dimension'] = player_file['Dimension'].value
    player_info['gamemode'] = player_file['playerGameType'].value

    return player_info


def set_player_info(player_file: nbt.NBTFile, player_info: dict) -> nbt.NBTFile:
    """
    Set the health, hunger, and dimension of a player.
    
    :param player_file: The player file
    :param player_info: The player information
    :return nbt.NBTFile: The player file with the updated information
    """

    player_file['Health'].value = float(player_info['health'])
    player_file['foodLevel'].value = int(player_info['hunger'])
    player_file['Dimension'].value = str(player_info['dimension'])
    player_file['playerGameType'].value = int(player_info['gamemode'])

    return player_file


def get_position(player_file: nbt.NBTFile) -> dict:
    """
    Get the position of a player.
    
    :param player_file: The player file
    :return dict: The position of the player
    """

    coord_directions: tuple = ('x', 'y', 'z')
    position: dict = {}

    for i in range(0, 3):
        position[coord_directions[i]] = player_file['Pos'][i].value
    
    return position


def set_position(player_file: nbt.NBTFile, position: dict) -> nbt.NBTFile:
    """
    Set the position of a player.
    
    :param player_file: The player file
    :param position: The position of the player
    :return nbt.NBTFile: The player file with the updated position
    """

    coord_directions: tuple = ('x', 'y', 'z')

    for i in range(0, 3):
        player_file['Pos'][i].value = float(position[coord_directions[i]])

    return player_file


def get_inventory(player_file: nbt.NBTFile) -> list:
    """
    Get the inventory of a player.

    :param player_file: The player file
    :return list: The inventory of the player
    """

    inventory: list = []
    
    for slot in range(len(player_file['Inventory'].tags)):
        item_slot: int = 0
        item_id: str = ''
        item_count: int = 0

        for tag in player_file['Inventory'][slot].tags:
            if "TAG_Byte('Slot')" in tag.tag_info():
                item_slot = int(tag.tag_info().replace("TAG_Byte('Slot'): ", ''))

            if "TAG_String('id')" in tag.tag_info():
                item_id = str(tag.tag_info().replace("TAG_String('id'): ", ''))

            if "TAG_Byte('Count')" in tag.tag_info():
                item_count = int(tag.tag_info().replace("TAG_Byte('Count'): ", ''))

        inventory.append({"item" : item_id, "slot" : item_slot, "count" : item_count})

    return inventory


def set_inventory(player_file: nbt.NBTFile, inventory: list) -> nbt.NBTFile:
    """
    Set the inventory of a player.

    :param player_file: The player file
    :param inventory: The inventory of the player
    :return nbt.NBTFile: The player file with the updated inventory
    """


    player_file['Inventory'].clear()

    for item in inventory:
        if item['count'] == '':
            continue

        if not (int(item['count']) >= 0 and int(item['count']) <= 64):
            print(f"Invalid item count: {item['count']}. Must be between 0 and 64.")
            return

        item_tag = nbt.TAG_Compound()

        item_tag.tags.append(nbt.TAG_String(name="id", value=item['item']))

        item_tag.tags.append(nbt.TAG_Byte(name="Slot", value=int(item['slot'])))
        item_tag.tags.append(nbt.TAG_Byte(name="Count", value=int(item['count'])))  

        player_file['Inventory'].tags.append(item_tag)

    return player_file


def gui(users: list, uuids: list, server: ftplib.FTP, properties: list, directory: str, offline: bool) -> None:
    global subdirectory, ip, port

    """
    The GUI for the application.

    :param users: The list of users
    :param uuids: The list of UUIDs
    :param server: The server to connect to
    :return None:
    """

    server_info: dict = {}

    if not offline:
        for line in properties:
            if 'query.port' in line:
                server_info['port'] = int(line.split('=')[1])
            
            if 'level-name' in line:
                server_info['world'] = line.split('=')[1]
    
        minecraft_server = mcstatus.JavaServer.lookup(ip, port)

        online_players: int = 0
        max_players: int = 0

        if minecraft_server is not None:
            online_players: int = minecraft_server.status().players.online
            max_players: int = minecraft_server.status().players.max
    else:
        server_info['port'] = 0
        server_info['world'] = 'NO SERVER WORLD'

        minecraft_server = None

        online_players: int = 0
        max_players: int = 0
    
        
    default_layout = [
        [sg.Text("Server Info:"), sg.Text(f'Players Online: {online_players}/{max_players}', key='_PLAYER_COUNT_'), sg.Text(f"Port: {server_info['port']}"), sg.Text(f"World Name: {server_info['world']}")],
        [sg.Text("User:"), sg.Combo(users, default_value='SELECT USER', key='_USER_INPUT_', enable_events=True), sg.Button("save"), sg.Button("upload")],
        [sg.Text("Health:"), sg.Input(key='_HEALTH_', size=(20, 1)), sg.Text("Hunger:"), sg.Input(key='_HUNGER_', size=(20, 1)), sg.Text("Dimension:"), sg.Input(key='_DIMENSION_', size=(20, 1)), sg.Text("Gamemode:"), sg.Input(key='_GAMEMODE_', size=(2, 1))],
        [sg.Text("X:"), sg.Input(key='_X_', size=(20, 1)), sg.Text("Y:"), sg.Input(key='_Y_', size=(20, 1)), sg.Text("Z:"), sg.Input(key='_Z_', size=(20, 1))],
        [sg.Text("Slot"), sg.Text("Item"), sg.Text("Count")],
        [
            sg.Text("Helmet:", size=(6, 1)), sg.Input(key='_ITEM_103_', size=(27, 1)), sg.Input(key='_COUNT_103_', size=(2, 1)), 
            sg.Text("Chestplate:", size=(8, 1)), sg.Input(key='_ITEM_102_', size=(27, 1)), sg.Input(key='_COUNT_102_', size=(2, 1)), 
            sg.Text("Leggings:", size=(7, 1)), sg.Input(key='_ITEM_101_', size=(27, 1)), sg.Input(key='_COUNT_101_', size=(2, 1)), 
            sg.Text("Boots:", size=(5, 1)), sg.Input(key='_ITEM_100_', size=(25, 1)), sg.Input(key='_COUNT_100_', size=(2, 1)),
        ],
        [sg.Text("Shield:", size=(6, 1)), sg.Input(key='_ITEM_-106_', size=(27, 1)), sg.Input(key='_COUNT_-106_', size=(2, 1))]
    ]

    for a in range(0, 9):
        temp_list = []
        for b in range(0, 4):
            temp_list.append(sg.Text(f'Slot {b + (a * 4)}:', size=(6, 1)))
            temp_list.append(sg.Input(key=f'_ITEM_{b + (a * 4)}_', size=(27, 1)))
            temp_list.append(sg.Input(key=f'_COUNT_{b + (a * 4)}_', size=(2, 1)))

        default_layout.append(temp_list)

    window = sg.Window('Editor', default_layout, resizable=True)

    player_file = None

    while True:
        special_items: tuple = (103, 102, 101, 100, -106)
        event, values = window.read()

        match event:
            case sg.WIN_CLOSED:
                break

            case '_USER_INPUT_':
                current_player = uuids[users.index(values['_USER_INPUT_'])]
            
                print(f"Retrieving player data for {current_player}...")
                if not offline:
                    try:
                        server.retrbinary(f'RETR /world/playerdata/{current_player}.dat', open(f'data{subdirectory}players{subdirectory}{current_player}.dat', 'wb').write)
                        print("Player data retrieved successfully.")
                    except Exception as e:
                        print(f"Failed to retrieve player data: {str(e)}")
                        continue
                else:
                    print("Player data already loaded.")

                player_file = nbt.NBTFile(f'{directory}{subdirectory}data{subdirectory}players{subdirectory}{current_player}.dat', "rb")
                
                position: dict = get_position(player_file)
                inventory: list = get_inventory(player_file)
                player_info: dict = get_player_info(player_file)

                window['_HEALTH_'].update(value=player_info['health'])
                window['_HUNGER_'].update(value=player_info['hunger'])
                window['_DIMENSION_'].update(value=player_info['dimension'])
                window['_GAMEMODE_'].update(value=player_info['gamemode'])

                window['_X_'].update(value=position['x'])
                window['_Y_'].update(value=position['y'])
                window['_Z_'].update(value=position['z'])

                for a in range(0, 9):
                    for b in range(0, 4):
                        window[f'_ITEM_{b + (a * 4)}_'].update(value='')
                        window[f'_COUNT_{b + (a * 4)}_'].update(value='')

                for item in special_items:
                    window[f'_ITEM_{item}_'].update(value='')
                    window[f'_COUNT_{item}_'].update(value='')

                for item in inventory:
                    try:
                        window[f'_ITEM_{item["slot"]}_'].update(value=item['item'])
                        window[f'_COUNT_{item["slot"]}_'].update(value=item['count'])
                    except:
                        print(item, item["slot"])
                
                if not offline:
                    minecraft_server = mcstatus.JavaServer.lookup(ip, port)

                online_players: int = 0
                max_players: int = 0

                if minecraft_server is not None:
                    online_players: int = minecraft_server.status().players.online
                    max_players: int = minecraft_server.status().players.max
                
                window['_PLAYER_COUNT_'].update(value=f'Players Online: {online_players}/{max_players}')

                window.refresh()
            
            case 'save':
                if player_file is None:
                    print("No player data loaded.")
                    continue

                current_player = uuids[users.index(values['_USER_INPUT_'])]

                new_inventory: list = []

                for a in range(0, 9):
                    for b in range(0, 4):
                        item: dict = {}

                        item['count'] = values[f'_COUNT_{b + (a * 4)}_']
                        item['item'] = values[f'_ITEM_{b + (a * 4)}_']
                        item['slot'] = b + (a * 4)

                        new_inventory.append(item)

                for item in special_items:
                    new_inventory.append({'count': values[f'_COUNT_{item}_'], 'item': values[f'_ITEM_{item}_'], 'slot': item})

                player_file = set_player_info(player_file, {'health': values['_HEALTH_'], 'hunger': values['_HUNGER_'], 'dimension': values['_DIMENSION_'], 'gamemode': values['_GAMEMODE_']})
                player_file = set_position(player_file, {'x': values['_X_'], 'y': values['_Y_'], 'z': values['_Z_']})
                player_file = set_inventory(player_file, new_inventory)

                player_file.write_file(f'.{subdirectory}data{subdirectory}players{subdirectory}{current_player}.dat')

                print(f"Player data for {current_player} saved.")
            
            case 'upload':
                current_player = uuids[users.index(values['_USER_INPUT_'])]

                print(f"Uploading player data for {current_player}...")

                if offline:
                    print("Cannot upload player data in offline mode.")
                    continue
                
                try:
                    server.storbinary(f"STOR /world/playerdata/{current_player}.dat", open(f'data{subdirectory}players{subdirectory}{current_player}.dat', 'rb'))
                    print("Player data uploaded successfully.")
                except Exception as e:
                    print(f"Failed to upload player data: {str(e)}")
    window.close()


def get_file(server: ftplib.FTP, filename: str) -> str:
    """
    Get a file from the server.
    
    :param server: The server to retrieve the file from
    :param filename: The name of the file to retrieve
    :return str: The file's data
    """

    file = io.BytesIO()
    server.retrbinary(f'RETR {filename}', file.write)

    return file.getvalue().decode('utf-8')


def build_local_user_cache(player_folder: str, minecraft_api: str) -> dict:
    """
    Build a local user cache from the player folder.
    
    :param player_folder: The folder containing the player data
    :param minecraft_api: The API to retrieve player data
    :return dict: The user cache generated from the player folder
    """

    usercache_data: dict = {}
    network_connection: bool = False

    #Check for internet connection
    try:
        requests.get('https://www.google.com')
        network_connection = True
    except:
        print("No internet connection. Attempting to continue offline")


    for player in os.listdir(player_folder):
        current_player = player.replace('.dat', '')

        if not network_connection:
            usercache_data[current_player] = current_player
            continue

        print(f"Retrieving player name for {current_player}...")
        player_data = requests.get(minecraft_api.format(uuid=current_player.replace('-', ''))).json()

        if player_data['code'] == 'player.found':
            usercache_data[current_player] = player_data['data']['player']['username']
            
        elif player_data['code'] == 'minecraft.api_failure':
            print(f"Failed to retrieve player name for {current_player}.")
            usercache_data[current_player] = current_player
    
    return usercache_data


def main(minecraft_api: str, ip: str, port: int, username: str, password: str, directory: str, offline: bool) -> None:
    """
    The main function of the application.

    :param minecraft_api: The API to retrieve player data
    :param ip: The IP of the server
    :param port: The port of the server
    :param username: The username for server login
    :param password: The password for server login
    :param directory: The directory to save the player data
    :param offline: Run the program in offline mode
    :return None:
    """

    server: ftplib.FTP = ftplib.FTP()

    if offline:
        usercache_data = build_local_user_cache(f'{directory}{subdirectory}data{subdirectory}players', minecraft_api)

        uuids: list = list(usercache_data.keys())
        user_list: list = list(usercache_data.values())

        gui(user_list, uuids, server, [], directory, offline)
        sys.exit()
    
    while True:
        try:
            server.connect(ip, port)
            server.login(username, password)
            print('SUCCESS LOGGING IN!')
            break
        except:
            print('FAILED TO LOGIN!')

    usercache_data = get_file(server, 'usernamecache.json')
    usercache_data = usercache_data.replace('[', '{')
    usercache_data = usercache_data.replace(']', '}')

    usercache_data = json.loads(usercache_data)

    properties_data = get_file(server, 'server.properties')
    properties_data = properties_data.split('\n')

    ops_data = get_file(server, 'ops.json')
    ops_data = ops_data.replace('[', '{')
    ops_data = ops_data.replace(']', '}')

    ops_data = json.loads(ops_data)

    uuids: list = list(usercache_data.keys())
    user_list: list = list(usercache_data.values())

    gui(user_list, uuids, server, properties_data, directory, offline)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Offline Minecraft Save Editor")

    #Local arguments
    parser.add_argument("-o", "--offline", help="Run the program in offline mode", action="store_true", required=False)
    parser.add_argument("-a", "--add", help="Add a player data file to the player folder", type=str, required=False)
    parser.add_argument("-dir", "--directory", help="The directory to save the player data", type=str, required=False)

    #Server arguments
    parser.add_argument("-m", "--minecraft_api", help="The API to retrieve player data", type=str, required=False)
    parser.add_argument("-i", "--ip", help="The IP of the server", type=str, required=False)
    parser.add_argument("-p", "--port", help="The port of the server", type=int, required=False)
    parser.add_argument("-u", "--username", help="The username for server login", type=str, required=False)
    parser.add_argument("-pw", "--password", help="The password for server login", type=str, required=False)
    
    args = parser.parse_args()

    #For PyInstaller
    compiled = False
    if hasattr(sys, '_MEIPASS'):
        compiled = True

    directory: str = '.'
    subdirectory: str = os.sep

    if args.directory:
        directory = args.directory

    data_folder = f'{directory}{subdirectory}data'
    player_folder = f'{data_folder}{subdirectory}players'
    settings_file = f'{data_folder}{subdirectory}settings.json'

    if not os.path.exists(settings_file):
        if not os.path.exists(data_folder):
            os.mkdir(data_folder)

        settings_location = 'default_settings.json'
        if compiled:
            settings_location = os.path.join(sys._MEIPASS, 'default_settings.json')

        shutil.copy(settings_location, settings_file)

        print("Settings file not found. Creating new settings file with default values.")

        if not args.offline:
            input("Please edit the settings file and restart the program. \nPress enter to exit.")
            sys.exit()

    if not os.path.exists(player_folder):
        os.mkdir(player_folder)

    settings: dict = json.load(open(settings_file, 'r'))

    minecraft_api: str =  settings.get('minecraft_api', 'https://playerdb.co/api/player/minecraft/{uuid}')
    offline: bool = settings.get('start_in_offline_mode')
    ip: str = settings.get('ip')
    port: int = settings.get('port')
    username: str = settings.get('username')
    password: str = settings.get('password')

    if args.ip:
        ip = args.ip
    if args.port:
        port = args.port
    if args.username:
        username = args.username
    if args.password:
        password = args.password
    if args.offline:
        offline = args.offline
    
    if args.add:
        print(f"Copying player data from {args.add} to the player folder.")

        try:
            shutil.copyfile(args.add, f'{player_folder}{subdirectory}{args.load.add(os.sep)[-1]}')
        except Exception as error:
            print(f"Failed to copy {args.add} to {player_folder} due to: {error}")

    main(minecraft_api, ip, port, username, password, directory, offline)