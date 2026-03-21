# OSCR Databases

This repository holds the databases (and default `config.txt`) for the Open Source Cartridge Reader.

The `data` directory contains files with cartridge information stored as JSON. These files are not used by the OSCR, JSON is merely easier to edit. These files do not need to be placed on the SD card.

The `filesystem` directory contains the data that the OSCR firmware uses. The contents of this folder are what you should place in the root directory of your SD card.

The JSON files need "compiled" to a binary format called CRDB (Cartridge Reader Database) before the firmware can use them. The main firmware project builds these files during the build process.
