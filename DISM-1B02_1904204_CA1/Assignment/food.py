# import kivy widgets from module
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
# import regex module
import re
# import os module
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
# import my module
from misc import convert_cost_to_currency

# init widgets to use in code (content in .kv file)
class FoodScrollBtn(TabbedPanelItem):
    pass

class FoodTabScroll(ScrollView):
    pass

class FoodLabel(ButtonBehavior, BoxLayout):
    pass

class MyLabel(Label):
    pass


# food stall object to hold food items
class FoodStall():
    def __init__(self, stall_name: str, food_list: list):
        self.stall_name: str = stall_name
        self.food_list: list = food_list


# food item object
class Food():
    amount: int = 0

    def __init__(self, food_name: str, food_url: str, 
                 food_price: str):
        self.food_name: str = food_name
        self.food_url: str = "images/" + food_url
        self.food_price: str = "$" + food_price
        self.discounted: bool = False
        self.orig_price = convert_cost_to_currency(food_price)

    # strike through given string
    def strike_through(self, string: str):
        result = ''
        for char in string:
            result = result + char + '\u0336'
        return result

    # apply discount to food item
    def apply_discount(self, disc_percentage: float):
        food_pri = float(self.food_price.replace("$", ""))
        food_pri = food_pri * (1 - float(disc_percentage))
        self.food_price = "$" + str(food_pri)
        self.discounted = True

    # remove discount from food item
    def remove_discount(self):
        self.discounted = False
        self.food_price = self.orig_price

    # check if discount applied and change appearance accordingly
    def check_price_for_discounts(self):
        self.food_price = convert_cost_to_currency(self.food_price)
        food_str = self.food_price
        if self.discounted:
            orig_p = self.strike_through(self.orig_price)
            food_str = f"{orig_p} {self.food_price}"
        return food_str

    # show details of food item
    def display_food_details(self,  sm):
        food_details_screen = sm.get_screen('food-details-screen')
        food_details_screen.ids.food_img.source = self.food_url
        food_details_screen.ids.food_name.text = self.food_name

        food_details_screen.ids.food_price.text = self.check_price_for_discounts()

        food_details_screen.ids.food_amt_label.text = str(self.amount)
        food_details_screen.food_amount = self.amount

        sm.change_screen("food-details-screen")

    # initialise food label to click that brings to details screen
    def init_food_label(self, sm):
        food_label = FoodLabel(width=Window.width, size_hint=(None, None),
                               orientation="horizontal")
        food_label.bind(on_press = lambda x: self.display_food_details(sm))
        food_image = Image(source=self.food_url, height=food_label.height,
                           size_hint=(None, None), allow_stretch=True)
        food_label_name = MyLabel(text=self.food_name, bold=True)
        food_label_price = MyLabel(text=self.check_price_for_discounts(), font_size=15)
        food_label.add_widget(food_image)
        food_label.add_widget(food_label_name)
        food_label.add_widget(food_label_price)

        return food_label


# foodcourt object to hold foodstall objects
class FoodCourt():
    def __init__(self, name: str, stalls: list):
        self.fc_name: str = name
        self.stall_list: list = stalls
    
    # Call this function to display the GUI screen of the foodcourt and its
    # relative stalls
    def display_food_screen(self, root, sm):
        food_screen = sm.get_screen('food-screen')

        if food_screen.ids.foodcourt_name.text == self.fc_name:
            return
        # changes name of food screen
        food_screen.ids.foodcourt_name.text = self.fc_name
        food_tab = food_screen.ids.food_tab

        food_tab.clear_tabs()

        for food_stall in self.stall_list:
            self.create_stall_widget(root, food_screen, food_stall, sm)

        food_tab.switch_to(food_tab.tab_list[0])


    # Creates the relative stall tabs
    def create_stall_widget(self, root, food_screen, stall: FoodStall, sm):
        food_widget = FoodScrollBtn(text=stall.stall_name)

        food_scroll = FoodTabScroll(do_scroll_y=False, do_scroll_x=True)

        food_grid = GridLayout(id='food-grid', cols=1, width=root.width,
                               padding=(10, 0), size_hint_y=None)
        food_grid.height = food_grid.minimum_height

        food_list = stall.food_list
        for food in food_list:
            self.populate_foods(root, food_grid, food, sm)

        food_scroll.add_widget(food_grid)
        food_widget.add_widget(food_scroll)
        food_screen.ids.food_tab.add_widget(food_widget)

    # Function to add food labels into stall tabs
    def populate_foods(self, root, food_grid, food: Food, sm):
        food_grid.add_widget(food.init_food_label(sm))


# food manager to manage all food items in excel/txt file
class FoodManager():
    all_foods: list = []
    all_foodcourts: list = []
    food_categories: dict = {}

    # read the txt file
    def read_food_file(self):
        with open(dir_path + "/data/food.txt") as raw_txt:
            current_food_cat = []
            raw_txt_list = [line.rstrip('\n') for line in raw_txt]
            for row in raw_txt_list:
                row_data = row.split("\t")
                if "_" not in row_data[0]:
                    new_food = Food(row_data[0], f"{row_data[1]}.jpg", row_data[2])
                    current_food_cat.append(new_food)
                    self.all_foods.append(new_food)
                elif "_" in row_data[0]:
                    row_data[0] = row_data[0].replace("_", "")
                    self.food_categories[row_data[0]] = current_food_cat
                    current_food_cat = []
        self.food_categories['All'] = self.all_foods


    # init the foodcourts from the txt file
    def init_foodcourts(self):
        # print(self.food_categories)
        with open(dir_path + "/data/foodcourts.txt") as raw_txt:
            raw_txt_list = [line.rstrip('\n') for line in raw_txt]
            for row in raw_txt_list:
                fc_stall_list = []
                row_data = row.split("\t")
                for stall_name in row_data[1:]:
                    try:
                        food_cat_list = self.food_categories[stall_name]
                        fc_stall = FoodStall(stall_name, food_cat_list)
                        fc_stall_list.append(fc_stall)
                    except KeyError:
                        pass
                new_fc = FoodCourt(row_data[0], fc_stall_list)
                self.all_foodcourts.append(new_fc)

    # call this to init all needed food vars
    def init_all_food_vars(self):
        self.read_food_file()
        self.init_foodcourts()


# Holds all the foodcourts available
myFoodManager = FoodManager()
myFoodManager.init_all_food_vars()
all_foodcourts = myFoodManager.all_foodcourts
all_foods = myFoodManager.all_foods