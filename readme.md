# Offline Minecraft Save Editor

This project is a powerful tool for managing minecraft save files offline. Specifically for automatically downloading server player data modifying it locally and reuploading back to the server.

## Features

- **FTP Access**: Offline Minecraft Server Editor utilizes FTP (File Transfer Protocol) to establish a connection with your server. This allows you to seamlessly transfer files between your local machine and the server.

- Player Data Management: Easily manage player data, including player inventories, location, gamemode, and etc. You can backup, restore, and edit player data files directly from the application.

## Getting Started

To get started with Offline Minecraft Server Editor, follow these steps:

1. Clone or download the repository / application to your local machine.
2. Launch the application, it will provide an error stating there is no data folder however once you see that error the folder has been made.
3. Go into the folder and modify settings.json to fit your needs.
4. Launch the applcation again, you should be good to go.

If you need to modify local files launch the application with the -o argument.

## "Compiling"

To compile the project, you must have pyinstaller installed, be in the base directory, then use the following pyinstaller command: `pyinstaller --add-data "./src/default_settings.json;." --add-data "LICENSE;." -c -F -n OMSE ./src/main.py`

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue on the repo.
