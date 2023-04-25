import random
import arcade
from pyglet.math import Vec2
import CONSTANTS
import math

"""
Controls: 
A = left
D = Right
Space = Jump

Purpose of the game:
Spawn in with a gun. The player can pick up ammo. Zombies spawn randomly and pathfind to the player. 3 hits from a 
zombie and game over. 2 bullets to kill a zombie.
As the game progress the zombie spawning will increase and it will take more bullets to kill them and they will 
walk faster.

Right now, my biggest issue is with getting the zombie to pathfind and move. I'm also 
trying to figure out how to loop the map. I want it so that you can just walk from one end to 
the other and it will continue. I'm thinking about doing a player_sprite_center conditional statement and if it meets 
the requirements then it will update the center of the player to the other side of the map but I don't want it to jump.
I want it to appear as though the player hasn't moved and he's just continuing to walk forward. 
I then need to get the zombie coded in

Largest obstacle for me during this whole process is that the examples I'm pulling from all use different styles. One 
will have their zombie in the MyGame class and the other one will have it in it's own separate class so I'm having 
trouble figuring out how to implement and specific example into the code I've already reference/written


Current issue: 
(1)The zombie spawns at 0,0 below the map. If I set his spawn point using zombie.center_x or center_y,
then no pathfind line is drawn and it  only "pathfinds" when I am on top of the zombie. It only pathfinds for about a 
64 by 64 pixel radius around the zombie.
The pathfind line is also only ever vertical and is draw at 0,0 upwards ina straight line no matter where I am. In order
to see the line you have to walk left towards the edge of the map while jumping because the line only shows when the 
player is jumping

(2) The zombie also wont move even though I called the function (Zombie) to move the zombie. Biggest thing right now is
that I'm trying to code things that I don't really know how they work

(3) It only pathfinds when I jump
"""


def load_texture_pair(filename):
    return [arcade.load_texture(filename), arcade.load_texture(filename, flipped_horizontally=True)]


class Entity(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.facing_direction = CONSTANTS.RIGHT_FACING
        self.cur_texture = 0
        self.scale = CONSTANTS.PLAYER_SCALE
        main_path = f"character_maleAdventurer"
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)
        self.texture = self.idle_texture_pair[0]
        self.set_hit_box(self.texture.hit_box_points)


class Zombie(arcade.Sprite):
    def __init__(self, image, scale, position_list):
        super().__init__(image, scale)
        self.position_list = position_list
        self.cur_position = 0
        self.speed = CONSTANTS.ZOMBIE_SPEED

    def update(self):

        #  self.center_x = 2300
        #  I tried setting the spawn point in the actual function and that doesn't work either.
        #  self.center_y = 2400
        # Where are we
        start_x = self.center_x
        start_y = self.center_y

        # Where are we going
        dest_x = self.position_list[0]
        dest_y = self.position_list[1]
        # X and Y diff between the two
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y

        # Calculate angle to get there
        angle = math.atan2(y_diff, x_diff)

        # How far are we?
        distance = math.sqrt((self.center_x - dest_x) ** 2 + (self.center_y - dest_y) ** 2)

        # How fast should we go? If we are close to our destination,
        # lower our speed, so we don't overshoot.
        speed = min(self.speed, distance)

        # Calculate vector to travel
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed

        # Update our location
        self.center_x += self.change_x
        self.center_y += self.change_y

        # How far are we?
        distance = math.sqrt((self.center_x - dest_x) ** 2 + (self.center_y - dest_y) ** 2)

        # If we are there, head to the next point.
        if distance <= self.speed:
            self.cur_position += 1

            # Reached the end of the list, start over.
            if self.cur_position >= len(self.position_list):
                self.cur_position = 0


class Player(Entity):
    def __init__(self):
        super().__init__()
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_x < 0 and self.facing_direction == CONSTANTS.RIGHT_FACING:
            self.facing_direction = CONSTANTS.LEFT_FACING
        elif self.change_x > 0 and self.facing_direction == CONSTANTS.LEFT_FACING:
            self.facing_direction = CONSTANTS.RIGHT_FACING
        if self.is_on_ladder:
            self.climbing = True
        if not self.is_on_ladder and self.climbing:
            self.climbing = False
        if self.climbing and abs(self.change_y) > 1:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
        if self.climbing:
            self.texture = self.climbing_textures[self.cur_texture // 4]
            return
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.facing_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.fall_texture_pair[self.facing_direction]
            return
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.facing_direction]
            return
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][self.facing_direction]


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, resizable=True)
        #  Player related
        self.player_list = True
        self.player_sprite = None
        self.player_hit_list = None
        #  Zombie related
        self.zombie_sprite = None
        self.zombie_list = None
        self.position_list = None
        self.barrier_list = None
        self.path = None
        #  Bullet/ammo related
        self.direction = True
        self.bullet_list = None  # A list of the visible projectiles
        self.ammo_hit_list = None
        self.ammo_full = True
        self.gun_shot = arcade.load_sound("gun_shot.mp3")
        self.ammo_pickup_sound = arcade.load_sound("confirmation_004.ogg")
        self.ammo_list = None  # A list of the floating ammo images that are used for reloading
        self.ammo = None
        self.mag_amount = 0
        #  Wall/map related
        self.wall_hit_list = None
        self.wall_list = None
        self.background = None
        self.title_map = None
        self.view_bottom = 0
        self.view_left = 0
        self.grid_size = None

        self.physics_engine = None
        self.score = 0

        # Keyboard related
        # Space/jump
        self.space_bar_pressed = False
        # left
        self.a_pressed = False
        # down
        self.s_pressed = False
        # right
        self.d_pressed = False
        self.e_pressed = False
        self.left_click_pressed = False
        #  Camera related
        self.camera_sprites = arcade.Camera(CONSTANTS.DEFAULT_SCREEN_WIDTH, CONSTANTS.DEFAULT_SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(CONSTANTS.DEFAULT_SCREEN_WIDTH, CONSTANTS.DEFAULT_SCREEN_HEIGHT)

    def setup(self):
        self.score = 0
        self.mag_amount = 15

        self.player_list = arcade.SpriteList()
        self.player_sprite = Player()
        self.player_sprite.center_x = CONSTANTS.SPRITE_SIZE * 20
        self.player_sprite.center_y = CONSTANTS.SPRITE_SIZE * 34
        self.player_list.append(self.player_sprite)

        self.background = arcade.load_texture("background.jpg")
        self.grid_size = CONSTANTS.SPRITE_SIZE
        self.wall_list = arcade.SpriteList(use_spatial_hash=True, spatial_hash_cell_size=128)
        map_name = "Map_final_game.tmj"
        self.title_map = arcade.load_tilemap(map_name, CONSTANTS.TILE_SCALING)
        self.wall_list = self.title_map.sprite_lists["Walls_and_blocks"]

        self.zombie_list = arcade.SpriteList()
        self.path = [self.player_sprite.center_x, self.player_sprite.center_y]
        self.position_list = self.path
        self.zombie_sprite = Zombie("character_zombie_idle.png", CONSTANTS.SPRITE_SCALING, self.position_list)
        self.zombie_sprite.center_x = 2200
        self.zombie_sprite.center_y = 1450
        self.zombie_list.append(self.zombie_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.wall_list,
                                                             gravity_constant=CONSTANTS.GRAVITY)
        self.ammo_full = True
        self.bullet_list = arcade.SpriteList()
        self.ammo_list = arcade.SpriteList()
        for i in range(CONSTANTS.AMMO_COUNT):
            ammo = arcade.Sprite("bro.png", CONSTANTS.AMMO_SCALE)
            ammo_placed_successfully = False
            ammo.center_x = random.randrange(CONSTANTS.START_X, CONSTANTS.END_X)
            ammo.center_y = 1450
            while not ammo_placed_successfully:
                self.ammo_hit_list = arcade.check_for_collision_with_list(ammo, self.ammo_list)
                self.wall_hit_list = arcade.check_for_collision_with_list(ammo, self.wall_list)
                self.player_hit_list = arcade.check_for_collision_with_list(ammo, self.player_list)
                if len(self.ammo_hit_list) != 0:
                    ammo.center_x += 64
                if len(self.wall_hit_list) != 0:
                    ammo.center_y += 64
                if len(self.ammo_hit_list) == 0 and len(self.wall_hit_list) == 0:
                    ammo_placed_successfully = True
            self.ammo_list.append(ammo)

    def on_update(self, delta_time):
        self.player_sprite.change_x = 0
        if self.a_pressed and not self.d_pressed:
            self.player_sprite.change_x = -CONSTANTS.PLAYER_SPEED
        elif self.d_pressed and not self.a_pressed:
            self.player_sprite.change_x = CONSTANTS.PLAYER_SPEED

        self.player_list.update()
        self.player_list.update_animation()
        self.ammo_list.update()
        self.bullet_list.update()
        self.physics_engine.update()

        playing_field_left_boundary = -CONSTANTS.SPRITE_SIZE * 2
        playing_field_right_boundary = CONSTANTS.SPRITE_SIZE * 35
        playing_field_top_boundary = CONSTANTS.SPRITE_SIZE * 17
        playing_field_bottom_boundary = -CONSTANTS.SPRITE_SIZE * 2

        self.barrier_list = arcade.AStarBarrierList(self.zombie_sprite,
                                                    self.wall_list,
                                                    self.grid_size,
                                                    playing_field_left_boundary,
                                                    playing_field_right_boundary,
                                                    playing_field_bottom_boundary,
                                                    playing_field_top_boundary)

        for bullet in self.bullet_list:
            hit_list = arcade.check_for_collision_with_list(bullet, self.zombie_list)
            hit_list2 = arcade.check_for_collision_with_list(bullet, self.wall_list)
            if len(hit_list) > 0 or len(hit_list2) > 0:
                bullet.remove_from_sprite_lists()
            if bullet.right > self.player_sprite.center_x + 750 or \
                    bullet.left < self.player_sprite.center_x - 750:
                bullet.remove_from_sprite_lists()

        for ammo in self.ammo_list:
            ammo_player_hit_list = arcade.check_for_collision_with_list(ammo, self.player_list)
            if len(ammo_player_hit_list) != 0 and self.e_pressed:
                ammo.remove_from_sprite_lists()
                arcade.play_sound(self.ammo_pickup_sound)
                self.mag_amount = 15
                self.ammo_full = True
                #  arcade.play_sound(self.reload_sound)

        zombie = self.zombie_list[0]
        self.path = arcade.astar_calculate_path(zombie.position,
                                                self.player_sprite.position,
                                                self.barrier_list,
                                                diagonal_movement=False)
        self.zombie_list.update()
        self.scroll_to_player()

    def on_draw(self):

        self.clear()

        arcade.draw_lrwh_rectangle_textured(0, 0, CONSTANTS.DEFAULT_SCREEN_WIDTH,
                                            CONSTANTS.DEFAULT_SCREEN_HEIGHT, self.background)
        self.camera_sprites.use()
        self.wall_list.draw()
        self.ammo_list.draw()
        self.bullet_list.draw()

        self.zombie_list.draw()
        self.player_list.draw()

        self.camera_gui.use()

        score = f"Score: {self.score}"
        arcade.draw_text(score, 10, 20, arcade.color.WHITE, 14)

        arcade.draw_rectangle_filled(self.width // 2,
                                     20,
                                     self.width,
                                     40,
                                     arcade.color.ALMOND)
        text = f"Scroll value: ({self.camera_sprites.position[0]:5.1f}, " \
               f"{self.camera_sprites.position[1]:5.1f})"
        arcade.draw_text(text, 10, 10, arcade.color.BLACK_BEAN, 20)

        ammo_display = f"Bullets: {self.mag_amount}/15"
        reload = f"YOU NEED TO RELOAD"
        if self.mag_amount < 1:
            self.ammo_full = False
            arcade.draw_text(reload, CONSTANTS.DEFAULT_SCREEN_WIDTH // 3.5, CONSTANTS.DEFAULT_SCREEN_HEIGHT // 2,
                             CONSTANTS.RELOAD_COLOR, 24)
        arcade.draw_text(ammo_display, 0, CONSTANTS.DEFAULT_SCREEN_HEIGHT // 2, CONSTANTS.AMMO_COUNT_COLOR, 24)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.A:
            self.a_pressed = True
            self.direction = False
        elif key == arcade.key.D:
            self.d_pressed = True
            self.direction = True
        elif key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = CONSTANTS.JUMP_SPEED
        elif key == arcade.key.E:
            self.e_pressed = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.A:
            self.a_pressed = False
        elif key == arcade.key.D:
            self.d_pressed = False
        elif key == arcade.key.SPACE:
            self.space_bar_pressed = False
        elif key == arcade.key.E:
            self.e_pressed = False

    def scroll_to_player(self):
        camera_position = Vec2(self.player_sprite.center_x - self.width / 2,
                               self.player_sprite.center_y - self.height / 3)
        self.camera_sprites.move_to(camera_position, CONSTANTS.CAMERA_SPEED)

    def on_resize(self, width, height):
        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))
        CONSTANTS.DEFAULT_SCREEN_WIDTH = width
        CONSTANTS.DEFAULT_SCREEN_HEIGHT = height

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.ammo_full:
            arcade.play_sound(self.gun_shot)
            bullet = arcade.Sprite("Bullet.png", .04)
            bullet.angle = 90
            self.mag_amount -= 1
            if self.direction:
                bullet.center_x = self.player_sprite.center_x - 8
                bullet.center_y = self.player_sprite.center_y - 12
                bullet.change_x = CONSTANTS.BULLET_SPEED
                bullet.angle = 270
            else:
                bullet.center_x = self.player_sprite.center_x - 8
                bullet.center_y = self.player_sprite.center_y - 12
                bullet.change_x = -CONSTANTS.BULLET_SPEED

            self.bullet_list.append(bullet)


def main():
    window = MyGame(CONSTANTS.DEFAULT_SCREEN_WIDTH, CONSTANTS.DEFAULT_SCREEN_HEIGHT, CONSTANTS.SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
