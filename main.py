import pyautogui
import cv2
import numpy as np
import time
import sys
import os
from datetime import datetime
from abc import ABC, abstractmethod

class ImageLocator:
    @staticmethod
    def locate_on_screen(image_path, confidence):
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(image_path, 0)
        result = cv2.matchTemplate(cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY), template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        return max_loc if max_val > confidence else None

    @staticmethod
    def locate_all_icons(image_path, confidence, color_filter=None):
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(image_path, 0)
        result = cv2.matchTemplate(cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY), template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)
        icons = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + template.shape[1] // 2
            center_y = pt[1] + template.shape[0] // 2
            if color_filter is None or color_filter(screenshot[center_y, center_x]):
                icons.append((center_x, center_y))
        return icons

class ClickerStrategy(ABC):
    @abstractmethod
    def execute(self):
        pass

class IconClickerStrategy(ClickerStrategy):
    def __init__(self, image_path, confidence, color_filter=None):
        self.image_path = image_path
        self.confidence = confidence
        self.color_filter = color_filter

    def execute(self):
        icons = ImageLocator.locate_all_icons(self.image_path, self.confidence, self.color_filter)
        clicked_count = 0
        for icon in icons:
            pyautogui.click(icon)
            print(f"Clicked icon at {icon}")
            clicked_count += 1
            pyautogui.moveRel(-30, 0)
            time.sleep(1.5)
        return clicked_count

class RefreshClickerStrategy(ClickerStrategy):
    def __init__(self, image_path, confidence, mouse_move_distance):
        self.image_path = image_path
        self.confidence = confidence
        self.mouse_move_distance = mouse_move_distance

    def execute(self):
        refresh_pos = ImageLocator.locate_on_screen(self.image_path, self.confidence)
        if refresh_pos:
            pyautogui.click(refresh_pos)
            print(f"Clicked refresh icon at {refresh_pos}")
            current_pos = pyautogui.position()
            pyautogui.moveTo(current_pos[0], current_pos[1] + self.mouse_move_distance)
            return True
        else:
            print("Refresh icon not found")
            return False

class ScrollStrategy:
    def __init__(self, scroll_amount):
        self.scroll_amount = scroll_amount

    def execute(self):
        pyautogui.scroll(-self.scroll_amount)
        print(f"Scrolled {self.scroll_amount} pixels")

class StateDetector:
    def __init__(self, config):
        self.config = config

    def detect_state(self):
        if self.is_at_homing_point():
            return "homing"
        else:
            return "unknown"

    def is_at_homing_point(self):
        return ImageLocator.locate_on_screen(self.config.HOMING_ICON, self.config.STATE_CONFIDENCE) is not None

class AutoClicker:
    def __init__(self, config):
        self.config = config
        self.heart_clicker = self.select_heart_strategy()
        self.refresh_clicker = RefreshClickerStrategy('refresh.png', config.REFRESH_CONFIDENCE, config.MOUSE_MOVE_DISTANCE)
        self.scroller = ScrollStrategy(config.SCROLL_AMOUNT)
        self.state_detector = StateDetector(config)
        self.clicks_since_refresh = 0
        self.scrolls_without_hearts = 0

    def select_heart_strategy(self):
        heart_image = f"{self.config.HEART_COLOR}_heart.png"
        return IconClickerStrategy(heart_image, self.config.get_heart_confidence(), self.config.color_filter)

    def run(self):
        print(f"Starting auto-clicker. Clicking {self.config.HEART_COLOR} hearts only.")
        self.initialize_program()
        print("Program initialized. Starting main loop. Press Ctrl+C to stop.")
        try:
            while True:
                self.execute_cycle()
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            sys.exit(0)

    def initialize_program(self):
        self.go_to_homing_point()
        self.open_browser()
        self.navigate_to_target_page()
        print("Successfully navigated to target page.")

    def go_to_homing_point(self):
        print("Going to homing point...")
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            homing_icon_pos = ImageLocator.locate_on_screen(self.config.HOMING_ICON, self.config.STATE_CONFIDENCE)
            if homing_icon_pos:
                pyautogui.click(homing_icon_pos)
                print("Clicked homing icon.")
                time.sleep(self.config.HOMING_DELAY)
                return
            attempts += 1
            print(f"Homing icon not found. Attempt {attempts}/{max_attempts}")
            time.sleep(1)

        print("Unable to find homing icon. Please navigate to the correct starting point manually.")
        input("Press Enter when ready...")

    def open_browser(self):
        print("Opening browser...")
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            browser_icon_pos = ImageLocator.locate_on_screen(self.config.BROWSER_ICON, self.config.STATE_CONFIDENCE)
            if browser_icon_pos:
                pyautogui.click(browser_icon_pos)
                print("Clicked browser icon. Waiting for browser to open...")

                for _ in range(10):
                    time.sleep(1)
                    address_bar_pos = ImageLocator.locate_on_screen(self.config.ADDRESS_BAR_ICON, self.config.STATE_CONFIDENCE)
                    if address_bar_pos:
                        print("Browser opened successfully.")
                        return

            attempts += 1
            print(f"Browser not detected. Attempt {attempts}/{max_attempts}")

        print("Unable to open browser. Please open the browser manually.")
        input("Press Enter when ready...")

    def navigate_to_target_page(self):
        print("Navigating to target page...")
        address_bar_pos = ImageLocator.locate_on_screen(self.config.ADDRESS_BAR_ICON, self.config.STATE_CONFIDENCE)
        if address_bar_pos:
            pyautogui.click(address_bar_pos)
            pyautogui.write(self.config.TARGET_URL)
            pyautogui.press('enter')
            print(f"Waiting {self.config.PAGE_LOAD_TIME} seconds for the page to load...")
            time.sleep(self.config.PAGE_LOAD_TIME)
            pyautogui.move(0, 75)  # Move the mouse down 10 pixels after sleep
            print("Mouse moved down 10 pixels.")
        else:
            print("Address bar not found. Please navigate to the target page manually.")
            input("Press Enter when ready...")

    def execute_cycle(self):
        hearts_clicked = self.check_and_click_hearts(attempts=2)
        self.clicks_since_refresh += hearts_clicked

        if hearts_clicked == 0:
            self.scroller.execute()
            time.sleep(self.config.SCROLL_PAUSE)
            self.scrolls_without_hearts += 1
        else:
            self.scrolls_without_hearts = 0
        
        print(f"Cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
              f"Total clicks since last refresh: {self.clicks_since_refresh}, "
              f"Scrolls without hearts: {self.scrolls_without_hearts}")

        if (self.clicks_since_refresh >= self.config.MAX_CLICKS_BEFORE_REFRESH or 
            self.scrolls_without_hearts >= self.config.MAX_SCROLLS_WITHOUT_HEARTS):
            print(f"Reached refresh condition. Clicks: {self.clicks_since_refresh}, "
                  f"Scrolls without hearts: {self.scrolls_without_hearts}")
            self.perform_refresh()

    def check_and_click_hearts(self, attempts=1):
        total_hearts_clicked = 0
        for _ in range(attempts):
            hearts_clicked = self.heart_clicker.execute()
            total_hearts_clicked += hearts_clicked
            if hearts_clicked == 0:
                break
            time.sleep(0.5)
        return total_hearts_clicked

    def perform_refresh(self):
        print("Performing refresh...")
        if self.refresh_clicker.execute():
            print(f"Waiting {self.config.PAGE_LOAD_TIME} seconds for the page to load...")
            time.sleep(self.config.PAGE_LOAD_TIME)
            print("Refresh completed.")
        else:
            print("Refresh failed. Continuing with current page.")
        self.clicks_since_refresh = 0
        self.scrolls_without_hearts = 0

class Config:
    def __init__(self):
        self.REFRESH_CONFIDENCE = 0.7
        self.GREY_HEART_CONFIDENCE = 0.80
        self.PINK_HEART_CONFIDENCE = 0.95
        self.STATE_CONFIDENCE = 0.9
        self.SCROLL_AMOUNT = 4
        self.SCROLL_PAUSE = 1.5
        self.MOUSE_MOVE_DISTANCE = 100
        self.HOMING_ICON = 'homing_icon.png'
        self.BROWSER_ICON = 'browser_icon.png'
        self.ADDRESS_BAR_ICON = 'address_bar.png'
        self.PAGE_LOAD_TIME = 6.1
        self.INITIAL_SCROLLS = 5
        self.HOMING_DELAY = 2
        self.TARGET_URL = ''
        self.HEART_COLOR = ''
        self.color_filter = None
        self.MAX_CLICKS_BEFORE_REFRESH = 100
        self.MAX_SCROLLS_WITHOUT_HEARTS = 5

    def get_user_input(self):
        self.TARGET_URL = input("Enter the target URL: ")
        while self.HEART_COLOR not in ['grey', 'pink']:
            self.HEART_COLOR = input("Choose heart color to click (grey/pink): ").lower()

        print(f"Auto-clicker will click on {self.HEART_COLOR} hearts with " 
              f"{self.GREY_HEART_CONFIDENCE if self.HEART_COLOR == 'grey' else self.PINK_HEART_CONFIDENCE} confidence.")

        while True:
            try:
                self.MAX_CLICKS_BEFORE_REFRESH = int(input("Enter the maximum number of clicks before refreshing: "))
                if self.MAX_CLICKS_BEFORE_REFRESH > 0:
                    break
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

        while True:
            try:
                self.MAX_SCROLLS_WITHOUT_HEARTS = int(input("Enter the maximum number of scrolls without hearts before refreshing: "))
                if self.MAX_SCROLLS_WITHOUT_HEARTS > 0:
                    break
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    def get_heart_confidence(self):
        return self.GREY_HEART_CONFIDENCE if self.HEART_COLOR == 'grey' else self.PINK_HEART_CONFIDENCE

def check_files():
    required_files = ['refresh.png', 'grey_heart.png', 'pink_heart.png', 'homing_icon.png', 'browser_icon.png', 'address_bar.png']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: Make sure '{file}' is in the same directory as this script.")
            sys.exit(1)

def main():
    check_files()
    config = Config()
    config.get_user_input()
    auto_clicker = AutoClicker(config)
    auto_clicker.run()

if __name__ == "__main__":
    main()