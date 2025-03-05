## Fetching Updated Capacity Data

The `rooms.py` script can be used to parse the centrally scheduled classroom capacity document published annually by Georgia Tech. This pdf can be found [here](https://registrar.gatech.edu/registration/buildings-and-class-locations). If this link is no longer functional, it may have been relocated and is now hosted at a different endpoint. For reference, a frozen snapshot of this page is provided [here](https://github.com/adibiasio/gatech-enrollment-data/tree/main/data/room_pdf_webpage_frozen.html). You can parse the pdf by downloading it and providing a local path to it as shown below, along with a path to save the outputted csv file.

```
$ python rooms.py [-p <pdf_path>] [-o <save_path>]
```