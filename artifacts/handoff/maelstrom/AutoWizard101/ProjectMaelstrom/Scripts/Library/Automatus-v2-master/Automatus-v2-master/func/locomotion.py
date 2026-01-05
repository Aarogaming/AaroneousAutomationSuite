# Local imports
from func.util import log

# Third-party imports
import asyncio
from wizwalker import Keycode, WIZARD_SPEED, XYZ

# TODO REFACTOR THIS FUNCTION - Lots of duplicated code!
# Follow a specified list of coordinates (using rudimentary goto() function from wizwalker)
# map --> lib.map.Map object
async def follow_map(bot, map, forward=True):
    log(f"Beginning route to {map.locname}", bot.logging)
    if forward:
        map.goto_start()
        while not map.end:
            await bot.handle_pause()
            point = map.next()

            # Keypress interface - -1 : S , 0 : X , 1 : W
            if point.x == 0 and point.y == 0:
                if point.z == -1:
                    await bot.client.send_key(Keycode.X, 0.2)
                    continue
                elif point.z == 0:
                    await bot.client.send_key(Keycode.S, 0.5)
                    continue
                elif point.z == 1:
                    await bot.client.send_key(Keycode.W, 0.5)
                    continue

            log(f"Moving client to: {point.x}, {point.y}...", bot.logging)
            await bot.client.goto(point.x, point.y)
    else:
        map.goto_end()
        while not map.start:
            await bot.handle_pause()
            point = map.prev()

            # Keypress interface - -1 : X , 0 : S , 1 : W
            if point.x == 0 and point.y == 0:
                if point.z == -1:
                    await bot.client.send_key(Keycode.X, 0.2)
                    continue
                elif point.z == 0:
                    await bot.client.send_key(Keycode.S, 0.5)
                    continue
                elif point.z == 1:
                    await bot.client.send_key(Keycode.W, 0.5)
                    continue

            log(f"Moving client to: {point.x}, {point.y}...", bot.logging)
            await bot.client.goto(point.x, point.y)

# Appends a point to the end of {cwd}/POINTS
async def append_point(bot, point):
    # try:
        path = os.path.abspath("./data/maps/Custom/USER_REC")
        file = None

        # Check if file does not exist or is empty
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            file = open(path, 'w')
            file.write("USER_REC\n")
        else: file = open(path, 'a')

        file.write(f"{round(point.x)},{round(point.y)},{round(point.z)}\n")
        log(f"Appended point {round(point.x)}, {round(point.y)}, {round(point.z)}", bot.logging)

        file.close()

    # except Exception:
    #     log(f"Failed to append to points file!", True)

# Removes the last point in the file at {cwd}/POINTS
async def remove_point(bot):
    # try:
        path = os.path.abspath("./data/maps/Custom/USER_REC")
        file = open(path, 'r')
        points = file.readlines()
        file.close()

        # Remove last point
        if len(points) > 1:
            points = points[:-1]
            log("Removed last point", bot.logging)

        file = open(path, 'w')
        file.writelines(points)

        file.close()

    # except Exception:
        # log(f"Failed to remove point from points file!", True)
