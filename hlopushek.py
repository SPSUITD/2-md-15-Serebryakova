import math
from tkinter import SEL
from token import NUMBER
from typing import List
from turtle import width
import arcade
from arcade.key import Q
import arcade.scene
import arcade.gui

SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
SCREEN_TITLE = "HLOPUSHEK"

CHARACTER_SCALING = 1
TILE_SCALING = 1

PLAYER_X_SPEED = 5
PLAYER_Y_SPEED = 5

JUMP_MAX_HEIGHT = 200
PLAYER_MOVEMENT_SPEED = 5

PLAYER_SPRITE_IMAGE_CHANGE_SPEED = 30

PLAYER_START_X = 90
PLAYER_START_Y = 148

SPRITE_PIXEL_SIZE = 128
NUMBER_OF_LEVELS = 2

RIGHT_FACING = 1
LEFT_FACING = -1



class MainView(arcade.View):
    def __init__(self):
        super().__init__()
        self.player_texture = None
        self.player_sprite = None
        self.player_list = None
        self.wall_list = None
        self.camera = None
        self.camera_max = 0
        self.player_jump  = False
        self.player_start = None

        self.key_right_pressed = False
        self.key_left_pressed = False
        self.collide = False

        self.player_dx = PLAYER_X_SPEED
        self.player_dy = PLAYER_Y_SPEED

        self.gui_camera = None
        self.score_text = None
        self.total_time = 0
      
        self.player_sprite_image_r = []
        self.player_sprite_image_l = []

        self.facing_direction = RIGHT_FACING
        self.jump_direction = None 

        self.tile_map = None
        self.fishes = 0

        self.end_of_map = 0
        self.level = 1
        self.total_fishes = 0

        self.manager = arcade.gui.UIManager()
        switch_menu_button = arcade.gui.UIFlatButton(text="| |", width=50)

        @switch_menu_button.event("on_click")
        def on_click_switch_button(event):
            menu_view = MenuView(self)
            self.window.show_view(menu_view)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
        anchor_x="right",
        anchor_y="top",
        child=switch_menu_button,
       )

    def on_hide_view(self):
        self.manager.disable()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        self.manager.enable()


    def setup(self):
        self.background_color = arcade.csscolor.AQUA
        self.player_texture = arcade.load_texture(
            r"player.png"
         )

        self.player_sprite = arcade.Sprite(self.player_texture)
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player_sprite)


        self.background = arcade.Sprite(r"bg.jpg")

        self.camera = arcade.Camera2D()

        self.gui_camera = arcade.Camera2D()
        self.end_of_map = 5120


        for i in range (1,5):
           self.player_sprite_image_r.append(arcade.load_texture(f"walk {i}.png"))
           
        for i in range (6,10):
           self.player_sprite_image_l.append(arcade.load_texture(f"walk {i}.png"))

        map_name = f"maps\map{self.level}.json"
        layer_options = {
             "platforms": {"use_spatial_hash": True, 
             }
        }
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.end_of_map = self.tile_map.width * SPRITE_PIXEL_SIZE
        print(self.end_of_map)

        self.fishes = 0

    def on_draw(self):
        self.clear()
        self.camera.use()
        for i in range(0, 5120, SCREEN_WIDTH):
            arcade.draw_sprite_rect(self.background, arcade.LBWH(i, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        self.scene.draw()
        self.player_list.draw()
        
        self.manager.draw()

        self.gui_camera.use()
        arcade.Text(f"Level: {self.level}/{NUMBER_OF_LEVELS}", x=0, y=35).draw()
        arcade.Text(f"Time: {self.total_time_print}", x = 0, y = 20).draw()
        arcade.Text(f"Fishes: {self.fishes} / 3", x = 0, y = 5).draw()

    def center_camera_to_player(self):
     
        level_width = 5120
        level_height = 768

        screen_center_x = self.player_sprite.center_x
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 4)
    
        if screen_center_x < self.camera.viewport_width / 2:
            screen_center_x = self.camera.viewport_width / 2
        elif screen_center_x > level_width - self.camera.viewport_width / 2:
            screen_center_x = level_width - self.camera.viewport_width / 2
    
        if screen_center_y < self.camera.viewport_height / 2:
            screen_center_y = self.camera.viewport_height / 2
        elif screen_center_y > level_height - self.camera.viewport_height / 2:
            screen_center_y = level_height - self.camera.viewport_height / 2

        self.camera.position = (screen_center_x, screen_center_y)

    def player_movement(self): 

       if self.collide:
            self.player_dy = 0
       else:
            self.player_dx = PLAYER_X_SPEED
            self.player_dy = PLAYER_Y_SPEED

       if self.key_left_pressed:
            self.player_sprite.center_x -= self.player_dx
            self.player_sprite.texture = self.player_sprite_image_l[int(self.player_sprite.center_x / PLAYER_SPRITE_IMAGE_CHANGE_SPEED) % 4]
            self.facing_direction = LEFT_FACING
       elif self.key_right_pressed:
            self.player_sprite.center_x += self.player_dx
            self.player_sprite.texture = self.player_sprite_image_r[int(self.player_sprite.center_x / PLAYER_SPRITE_IMAGE_CHANGE_SPEED) % 4]
            self.facing_direction = RIGHT_FACING

       if self.player_jump:
            self.player_sprite.center_y += self.player_dy
            if self.jump_direction == RIGHT_FACING:
                self.player_sprite.texture = self.player_sprite_image_r[1]
            else:
                self.player_sprite.texture = self.player_sprite_image_l[1]
                
            if self.player_sprite.center_y > self.jump_start + JUMP_MAX_HEIGHT:
                self.player_jump = False
                self.jump_direction = None
       else:
            self.player_sprite.center_y -= self.player_dy

    def calculate_collision(self):
        self.collide = False

        for block in self.scene["platforms"]:
            player_left = self.player_sprite.center_x - self.player_sprite.width * 0.1
            player_right = self.player_sprite.center_x + self.player_sprite.width * 0.1
            player_top = self.player_sprite.center_y + self.player_sprite.height * 0.1
            player_bottom = self.player_sprite.center_y - self.player_sprite.height * 0.1

            block_left = block.center_x - block.width * 0.5
            block_right = block.center_x + block.width * 0.5
            block_top = block.center_y + block.height * 0.4
            block_bottom = block.center_y - block.height * -0.8

            if (player_right > block_left and player_left < block_right and
                player_top > block_bottom and player_bottom < block_top):
        
                self.collide = True
        
                overlap_x = min(player_right - block_left, block_right - player_left)
                overlap_y = min(player_top - block_bottom, block_top - player_bottom)
        
                if overlap_x < overlap_y:
                    if self.player_sprite.change_x > 0:
                        self.player_sprite.center_x -= overlap_x
                    elif self.player_sprite.change_x < 0:
                        self.player_sprite.center_x += overlap_x
                else:
                    if self.player_sprite.change_y > 0:
                        self.player_sprite.center_y -= overlap_y
                    elif self.player_sprite.change_y < 0:
                        self.player_sprite.center_y += overlap_y
                
                break
            else:
                self.collide = False

        for block in self.scene["fishes"]:
            if (self.player_sprite.center_x + self.player_sprite.width /  20 >= block.center_x - block.width /4 and \
               self.player_sprite.center_x - self.player_sprite.width /6 <= block.center_x + block.width / 6) and \
                (self.player_sprite.center_y + self.player_sprite.height /4 >= block.center_y - block.height / 20 and \
                 self.player_sprite.center_y - self.player_sprite.height / 4 <= block.center_y + block.height / 20):
                    self.scene["fishes"].remove(block)
                    self.fishes  += 1
                    self.total_fishes += 1 

    def reset_timer(self):

        self.total_time = 0.0
        self.total_time_print = "00:00:00"
        self.fishes = 0
        self.level = 1
        self.setup() 

    def on_key_press(self, key, modifiers):

        if key == arcade.key.ESCAPE:
            self.reset_timer() 
            self.setup()

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.collide:
                self.player_jump = True
                self.jump_start = self.player_sprite.center_y
                if self.key_left_pressed:
                    self.jump_direction = LEFT_FACING
                    self.player_sprite.texture = self.player_sprite_image_l[1]
                elif self.key_right_pressed:
                    self.jump_direction = RIGHT_FACING
                    self.player_sprite.texture = self.player_sprite_image_r[1]
                else:
                    self.jump_direction = self.facing_direction
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.key_left_pressed = True
            self.facing_direction = LEFT_FACING
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.key_right_pressed = True
            self.facing_direction = RIGHT_FACING


    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.key_left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.key_right_pressed = False

    def on_update(self, delta_time):
        self.player_sprite.update_animation(delta_time)

        self.center_camera_to_player()
        self.player_movement()

        if self.player_jump:
            self.collide = False
        else:
            self.calculate_collision()


        self.total_time += delta_time

        ms, sec = math.modf(self.total_time)

        minutes = int(sec) // 60
        seconds = int(sec) % 60
        msec = int(ms * 100)

        self.total_time_print = f"{minutes:02d}:{seconds:02d}:{msec:02d}"

        if self.player_sprite.center_x >= self.end_of_map:
            if self.level < NUMBER_OF_LEVELS:
                level_complete_view = LevelCompleteView(self)
                self.window.show_view(level_complete_view)
            else:
                game_over_view = GameOverView(self)
                self.window.show_view(game_over_view)

class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.v_box = arcade.gui.UIBoxLayout(space_between=20)

        start_button = arcade.gui.UIFlatButton(text="Новая игра", width=200)
        exit_button = arcade.gui.UIFlatButton(text="Выход", width=200)

        self.v_box.add(start_button)
        self.v_box.add(exit_button)

        @start_button.event("on_click")
        def on_click_start(event):
            game_view = MainView()
            game_view.setup()
            self.window.show_view(game_view)

        @exit_button.event("on_click")
        def on_click_exit(event):
            arcade.exit()

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=self.v_box,
            anchor_x="center_x",
            anchor_y="center_y",
        )

        self.manager.add(anchor)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()
        
        arcade.draw_text(
            "HLOPUSHEK",
            self.window.width / 2,
            self.window.height - 100,
            arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
        )

class LevelCompleteView(arcade.View):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.manager = arcade.gui.UIManager()

        continue_button = arcade.gui.UIFlatButton(text="Следующий уровень", width=200)
        menu_button = arcade.gui.UIFlatButton(text="В меню", width=200)

        self.v_box = arcade.gui.UIBoxLayout(space_between=20)
        self.v_box.add(continue_button)
        self.v_box.add(menu_button)

        @continue_button.event("on_click")
        def on_click_continue(event):
            self.main_view.level += 1
            self.main_view.setup()
            self.window.show_view(self.main_view)

        @menu_button.event("on_click")
        def on_click_menu(event):
            from views.menu import MainMenuView
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()
        
        arcade.draw_text(
            f"Уровень {self.main_view.level} пройден!",
            self.window.width/2, self.window.height-150,
            arcade.color.WHITE, font_size=50,
            anchor_x="center"
        )
        
        arcade.draw_text(
            f"Рыбок собрано: {self.main_view.fishes}",
            self.window.width/2, self.window.height-250,
            arcade.color.WHITE, font_size=30,
            anchor_x="center"
        )

class GameOverView(arcade.View):

    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.manager = arcade.gui.UIManager()

        menu_button = arcade.gui.UIFlatButton(text="В меню", width=200)
        restart_button = arcade.gui.UIFlatButton(text="Заново", width=200)

        self.v_box = arcade.gui.UIBoxLayout(space_between=20)
        self.v_box.add(restart_button)
        self.v_box.add(menu_button)

        @restart_button.event("on_click")
        def on_click_restart(event):
            game_view = MainView()
            game_view.setup()
            self.window.show_view(game_view)

        @menu_button.event("on_click")
        def on_click_menu(event):
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()
        
        arcade.draw_text(
            "Игра пройдена!",
            self.window.width/2, self.window.height-150,
            arcade.color.GOLD, font_size=50,
            anchor_x="center"
        )
        
        arcade.draw_text(
            f"Общее время: {self.main_view.total_time_print}",
            self.window.width/2, self.window.height-250,
            arcade.color.WHITE, font_size=30,
            anchor_x="center"
        )
        
        arcade.draw_text(
            f"Всего рыбок: {self.main_view.total_fishes}",
            self.window.width/2, self.window.height-300,
            arcade.color.WHITE, font_size=30,
            anchor_x="center"
        )


class MenuView(arcade.View):

    def __init__(self, main_view):
        super().__init__()

        self.manager = arcade.gui.UIManager()

        resume_button = arcade.gui.UIFlatButton(text="продолжить", width=150)
        start_new_game_button = arcade.gui.UIFlatButton(text="новая игра", width=150)

        exit_button = arcade.gui.UIFlatButton(text="выход", width=320)

        self.grid = arcade.gui.UIGridLayout(
            column_count=2, row_count=3, horizontal_spacing=20, vertical_spacing=20
        )

        self.grid.add(resume_button, column=0, row=0)
        self.grid.add(start_new_game_button, column=1, row=0)

        self.grid.add(exit_button, column=0, row=2, column_span=2)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=self.grid,
        )

        self.main_view = main_view

        @resume_button.event("on_click")
        def on_click_resume_button(event):
            self.window.show_view(self.main_view)

        @start_new_game_button.event("on_click")
        def on_click_start_new_game_button(event):
            main_view = MainView()
            main_view.setup()
            self.window.show_view(main_view)

        @exit_button.event("on_click")
        def on_click_exit_button(event):
            arcade.exit()

    def on_hide_view(self):
        self.manager.disable()

    def on_show_view(self):

        arcade.set_background_color([rgb - 50 for rgb in arcade.color.DARK_BLUE_GRAY])
        self.manager.enable()

    def on_draw(self):
        self.clear()
        self.manager.draw()

def main():
      window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
      menu_view = MainMenuView()
      window.show_view(menu_view)
      arcade.run()

if __name__ == "__main__":
    main()
