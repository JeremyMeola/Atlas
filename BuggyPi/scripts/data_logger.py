import sys
import time
import traceback

sys.path.insert(0, "../")

from robots.loggerbot import LoggerBot


def main():
    robot = LoggerBot(enable_camera=False, log_data=False)
    for _ in range(10):
        robot.leds["green"].set("toggle")
        time.sleep(0.05)

    try:
        while True:
            status = robot.update()
            print(robot.state["x"], robot.state["y"])
            if not status:
                break
    except:
        traceback.print_exc()
    finally:
        robot.close()


if __name__ == '__main__':
    main()
