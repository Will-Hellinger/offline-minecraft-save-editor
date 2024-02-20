import ftplib
import os
import io
import json
from nbt import nbt
import PySimpleGUI as sg


subdirectory: str = os.sep
settings: dict = json.load(open(f'.{subdirectory}data{subdirectory}settings.json', 'r'))

ip: str = settings.get('ip')
port: int = settings.get('port')
username: str = settings.get('username')
password: str = settings.get('password')


def get_player_info(uuid: str) -> dict:
    """
    Get the health, hunger, and dimension of a player.
    
    :param uuid:
    :return: dict
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")
    player_info: dict = {}

    player_info['health'] = player_file['Health'].value
    player_info['hunger'] = player_file['foodLevel'].value
    player_info['dimension'] = player_file['Dimension'].value
    player_info['gamemode'] = player_file['playerGameType'].value

    return player_info


def set_player_info(uuid: str, player_info: dict) -> None:
    """
    Set the health, hunger, and dimension of a player.
    
    :param uuid:
    :param player_info:
    :return: None
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")

    player_file['Health'].value = float(player_info['health'])
    player_file['foodLevel'].value = int(player_info['hunger'])
    player_file['Dimension'].value = str(player_info['dimension'])
    player_file['playerGameType'].value = int(player_info['gamemode'])

    player_file.write_file(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat')


def get_position(uuid: str) -> dict:
    """
    Get the position of a player.
    
    :param uuid:
    :return: dict
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")
    coord_directions: tuple = ('x', 'y', 'z')
    position: dict = {}

    for i in range(0, 3):
        position[coord_directions[i]] = player_file['Pos'][i].value
    
    return position


def set_position(uuid: str, position: dict) -> None:
    """
    Set the position of a player.
    
    :param uuid:
    :param position:
    :return: None
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")
    coord_directions: tuple = ('x', 'y', 'z')

    for i in range(0, 3):
        player_file['Pos'][i].value = float(position[coord_directions[i]])

    player_file.write_file(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat')


def get_inventory(uuid: str) -> list:
    """
    Get the inventory of a player.

    :param uuid:
    :return: list
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")
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


def set_inventory(uuid: str, inventory: list) -> None:
    """
    Set the inventory of a player.

    :param uuid:
    :param inventory:
    :return: None
    """

    player_file = nbt.NBTFile(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat', "rb")


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


    player_file.write_file(f'.{subdirectory}data{subdirectory}players{subdirectory}{uuid}.dat')


def gui(users: list, uuids: list, server: ftplib.FTP) -> None:
    """
    The GUI for the application.

    :param users:
    :param uuids:
    :param server:
    :return: None
    """

    default_layout = [
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

    while True:
        special_items: tuple = (103, 102, 101, 100, -106)
        event, values = window.read()

        match event:
            case sg.WIN_CLOSED:
                break

            case '_USER_INPUT_':
                current_player = uuids[users.index(values['_USER_INPUT_'])]
            
                print(f"Retrieving player data for {current_player}...")
                try:
                    server.retrbinary(f'RETR /world/playerdata/{current_player}.dat', open(f'data/players/{current_player}.dat', 'wb').write)
                    print("Player data retrieved successfully.")
                except Exception as e:
                    print(f"Failed to retrieve player data: {str(e)}")
                    continue
                
                position: dict = get_position(current_player)
                inventory: list = get_inventory(current_player)
                player_info: dict = get_player_info(current_player)

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

                window.refresh()
            
            case 'save':
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

                set_player_info(current_player, {'health': values['_HEALTH_'], 'hunger': values['_HUNGER_'], 'dimension': values['_DIMENSION_'], 'gamemode': values['_GAMEMODE_']})
                set_position(current_player, {'x': values['_X_'], 'y': values['_Y_'], 'z': values['_Z_']})
                set_inventory(current_player, new_inventory)
            
            case 'upload':
                current_player = uuids[users.index(values['_USER_INPUT_'])]

                print(f"Uploading player data for {current_player}...")
                try:
                    server.storbinary(f"STOR /world/playerdata/{current_player}.dat", open(f'data/players/{current_player}.dat', 'rb'))
                    print("Player data uploaded successfully.")
                except Exception as e:
                    print(f"Failed to upload player data: {str(e)}")
                    continue

    window.close()


def main() -> None:
    """
    The main function of the application.
    
    :return: None
    """

    server: ftplib.FTP = ftplib.FTP()
    
    while True:
        try:
            server.connect(ip, port)
            server.login(username, password)
            print('SUCCESS LOGGING IN!')
            break
        except:
            print('FAILED TO LOGIN!')
            break
    
    data = io.BytesIO()
    server.retrbinary('RETR usernamecache.json', data.write)

    usercache_data = data.getvalue().decode('utf-8')
    usercache_data = usercache_data.replace('[', '{')
    usercache_data = usercache_data.replace(']', '}')

    usercache_data = json.loads(usercache_data)

    uuids: list = list(usercache_data.keys())
    user_list: list = list(usercache_data.values())

    gui(user_list, uuids, server)


if __name__ == '__main__':
    main()