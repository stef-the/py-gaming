"""
Origin from pyarcade examples, scroll around screen
"""

import random
import arcade
import math
import time
from pyglet.math import Vec2
from pynput import keyboard
import engine_sound_sim.engine_factory
from engine_sound_sim.audio_device import AudioDevice
from multiprocessing import Process
import threading

SPRITE_SCALING = 0.5

DEFAULT_SCREEN_WIDTH = 1600
DEFAULT_SCREEN_HEIGHT = 1000
SCREEN_TITLE = "Sprite Move with Scrolling Screen Example"

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
VIEWPORT_MARGIN = 300

# How fast the camera pans to the player. 1.0 is instant.
CAMERA_SPEED = 0.3

# How fast the car moves
BASE_RPM = 750
STEERING_COEF = 550
BRAKE_SPEED = 0.2
POWER_MAX = 40
    # POWER_MAX = 40 Top speed is 35 (with 0.9993 resistance) -> 315km/h
RUNNING = True

# 1 block is 64*64 pixels
blocks = [
    (0,0),
    (64,64)
]
class _BlockingInputThread(threading.Thread):
    '''
    The `inputs` library's IO is blocking, which means a new thread is needed to wait for
    events to avoid blocking the program when no inputs are received.
    '''
    def __init__(self, lock):
        super(_BlockingInputThread, self).__init__(daemon=True)
        self.lock = lock
        self.space_held = False
    def on_press(self, key):
        self.space_held = True
    def on_release(self, key):
        self.space_held = False
    def run(self):
        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        listener.start()

class MyGame(arcade.Window):
    """Main application class."""

    def __init__(self, width, height, title):
        """
        Initializer
        """
        super().__init__(width, height, title, resizable=True)

        # Sprite lists
        self.player_list = None
        self.wall_list = None

        # Set up the player
        self.player_sprite = None

        # Physics engine so we don't run into walls.
        self.physics_engine = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.shift_up_pressed = False
        self.shift_down_pressed = False

        self.timers = [time.time() for x in range(2)]

        # Create the cameras. One for the GUI, one for the sprites.
        # We scroll the 'sprite world' but not the GUI.
        self.camera_sprites = arcade.Camera(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)

        # Create sound management variables
        self.engine = None
        self.lock = None
        self.blockingInputThread = None

    def setup(self):
        """Set up the game and initialize the variables."""

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = arcade.Sprite("./img/red_car/straight.png", scale=0.4)
        self.player_sprite.center_x = 0
        self.player_sprite.center_y = 0

        # T1 (interacting with the player)
        self.player_sprite.throttle = 0
        self.player_sprite.brake = 0
        self.player_sprite.steering = 0
        self.player_sprite.gear = 0

        # T2 variables (engine)
        self.player_sprite.power = 0
        self.player_sprite.torque = 0

        # T3 variables (connecting engine to physics and sound)
        self.player_sprite.rpm = 750

        # T4 variables (interacting with the physics engine)
        self.player_sprite.angle = 0
        self.player_sprite.speed = 0

        self.player_list.append(self.player_sprite)

        # -- Set up several columns of walls
        for x in range(200, 5000, 210):
            for y in range(0, 5000, 64):
                # Randomly skip a box so the player can find a way through
                if random.randrange(5) > 0:
                    wall = arcade.Sprite(
                        ":resources:images/tiles/grassCenter.png", SPRITE_SCALING
                    )
                    wall.center_x = x
                    wall.center_y = y
                    self.wall_list.append(wall)
        
        for i in blocks:
            wall = arcade.Sprite(
                ":resources:images/tiles/grassCenter.png", SPRITE_SCALING
            )
            wall.center_x = i[0]
            wall.center_y = i[1]
            self.wall_list.append(wall)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.wall_list
        )

        # Set the background color
        arcade.set_background_color(arcade.color.AMAZON)

        # Create engine sound engine
        self.engine = engine_sound_sim.engine_factory.formula_one()
        # self.engine = engine_sound_sim.engine_factory.v_four_90_deg()
        # self.engine = engine_sound_sim.engine_factory.w_16()
        # self.engine = engine_sound_sim.engine_factory.v_8_LS()
        # self.engine = engine_sound_sim.engine_factory.inline_5_crossplane()
        # self.engine = engine_sound_sim.engine_factory.inline_6()
        # self.engine = engine_sound_sim.engine_factory.boxer_4_crossplane_custom([1, 1, 0, 0])  # (rando := random.randrange(360)))
        # self.engine = engine_sound_sim.engine_factory.inline_4_1_spark_plug_disconnected()
        # self.engine = engine_sound_sim.engine_factory.inline_4()
        # self.engine = engine_sound_sim.engine_factory.boxer_4_half()
        # self.engine = engine_sound_sim.engine_factory.random()
        # self.engine = engine_sound_sim.engine_factory.fake_rotary_2rotor()
        # self.engine = engine_sound_sim.engine_factory.V_12()

        self.lock = threading.Lock()
        self.blockingInputThread = _BlockingInputThread(self.lock)
        self.blockingInputThread.start()

        # Connect engine to audio device
        self.audio_device = AudioDevice()
        self.stream = self.audio_device.play_stream(self.engine.gen_audio)

    def on_draw(self):
        """Render the screen."""

        # This command has to happen before we start drawing
        self.clear()

        # Select the camera we'll use to draw all our sprites
        self.camera_sprites.use()

        # Draw all the sprites.
        self.wall_list.draw()
        self.player_list.draw()

        # Select the (unscrolled) camera for our GUI
        self.camera_gui.use()

        # Draw the GUI
        arcade.draw_rectangle_filled(
            self.width // 2, 20, self.width, 40, arcade.color.GRAY
        )
        text = (
            f"Coords: ({self.camera_sprites.position[0]:5.1f}, {self.camera_sprites.position[1]:5.1f}) | "
            f"Speed: {self.player_sprite.speed*9:5.1f}km/h | "
            f"Gear: {self.player_sprite.gear if self.player_sprite.gear > 0 else 'N' if self.player_sprite.gear == 0 else f'R{abs(self.player_sprite.gear)}'} | "
            #f"Throttle: {self.player_sprite.throttle} | "
            #f"Brake: {self.player_sprite.brake} | "
            #f"Angle: {self.player_sprite.angle:5.1f} | "
            #f"Steering: {self.player_sprite.steering} | "
            f"RPM: {abs(self.player_sprite.rpm):0.0f}"
        )

        arcade.draw_text(text, 10, 10, arcade.color.BLACK, 20)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.Q:
            self.shift_down_pressed = True
            self.player_sprite.gear -= 1 if self.player_sprite.gear > 0 or self.player_sprite.speed < 0.5 and self.player_sprite.gear > -1 else 0
        elif key == arcade.key.E:
            self.shift_up_pressed = True
            self.player_sprite.gear += 1 if self.player_sprite.gear < 0 or self.player_sprite.speed > -0.5 and self.player_sprite.gear < 7 else 0

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.Q:
            self.shift_up_pressed = False
        elif key == arcade.key.E:
            self.shift_up_pressed = False

    def on_update(self, delta_time):
        """Movement and game logic"""

        # Throttle input
        self.player_sprite.throttle = 1 if self.up_pressed else 0

        # Brake input
        self.player_sprite.brake = 1 if self.down_pressed else 0

        # Steering input
        if self.left_pressed and not self.right_pressed:
            self.player_sprite.steering = 1
        elif self.right_pressed and not self.left_pressed:
            self.player_sprite.steering = -1
        else:
            self.player_sprite.steering = 0

        # Update steering
        self.player_sprite.angle += (
            (
                self.player_sprite.steering
                / (
                    abs(self.player_sprite.speed) / 3 * 40 / STEERING_COEF
                )
            )
            if abs(self.player_sprite.steering * self.player_sprite.speed * 0.8) > 5
            else self.player_sprite.steering * self.player_sprite.speed * 0.8
        )

        # Update sound based on throttle & gear
        self.engine.specific_rpm(self.player_sprite.rpm)

        # Update T2 and T3 variables
        self.player_sprite.torque = POWER_MAX * (1 - (self.player_sprite.gear if self.player_sprite.gear != 0 else 1) / 8)
        self.player_sprite.power = POWER_MAX * ((self.player_sprite.gear if self.player_sprite.gear != 0 else 1) / 8)
        if self.player_sprite.gear:
            self.player_sprite.rpm = self.player_sprite.speed / (self.player_sprite.power+0.000001) * 12500 if abs(self.player_sprite.speed) > 0 else 750
        else:
            if self.player_sprite.throttle and self.player_sprite.rpm < 12500:
                self.player_sprite.rpm += 800 if self.player_sprite.rpm < 12000 else 300 if self.player_sprite.rpm < 13000 else 0
            if self.player_sprite.rpm >= 750:
                self.player_sprite.rpm -= 150
            else:
                self.player_sprite.rpm = 750

        # Update speed based on torque, power and throttle:
        if self.player_sprite.throttle and self.player_sprite.gear:
            self.player_sprite.speed += self.player_sprite.torque * 0.005
        
        # Update speed based on power limiter
        if self.player_sprite.speed > self.player_sprite.power and self.player_sprite.gear:
            self.player_sprite.speed -= (self.player_sprite.speed - self.player_sprite.power) / (3 - self.player_sprite.throttle)

        # Update speed based on resistance
        self.player_sprite.speed *= 0.998

        # Update speed based on braking
        if self.player_sprite.brake:
            BRAKE_COEF = BRAKE_SPEED if abs(self.player_sprite.speed) > BRAKE_SPEED * 1.1 else abs(self.player_sprite.speed)
            if self.player_sprite.speed > 0:
                self.player_sprite.speed -= BRAKE_COEF
            elif self.player_sprite.speed < 0:
                self.player_sprite.speed += BRAKE_COEF

        # Update player position based on speed and angle
        self.player_sprite.change_x = (
            self.player_sprite.speed
        ) * math.cos(math.radians(self.player_sprite.angle))
        self.player_sprite.change_y = (
            self.player_sprite.speed
        ) * math.sin(math.radians(self.player_sprite.angle))
        self.position = arcade.rotate_point(
            self.player_sprite.center_x,
            self.player_sprite.center_y,
            self.player_sprite.center_x,
            self.player_sprite.center_y,
            self.player_sprite.angle,
        )

        # Update angle to keep within bounds (0-360deg)
        self.player_sprite.angle += (
            -360
            if self.player_sprite.angle > 360
            else +360
            if self.player_sprite.angle < 0
            else 0
        )

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.physics_engine.update()

        # Scroll the screen to the player
        self.scroll_to_player()

    def scroll_to_player(self):
        """
        Scroll the window to the player.
        if CAMERA_SPEED is 1, the camera will immediately move to the desired position.
        Anything between 0 and 1 will have the camera move to the location with a smoother
        pan.
        """
        position = Vec2(
            self.player_sprite.center_x - self.width / 2,
            self.player_sprite.center_y - self.height / 2,
        )
        self.camera_sprites.move_to(position, CAMERA_SPEED)

    def on_resize(self, width, height):
        """
        Resize window
        Handle the user grabbing the edge and resizing the window.
        """

        self.camera_sprites.resize(int(width), int(height))
        self.camera_gui.resize(int(width), int(height))


def game_engine_processor():
    window = MyGame(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()

def main():
    """Main function"""
    p1 = Process(target=game_engine_processor) 
    p1.start()
    # Might incorporate multithreading later
    # For now it's leftover from implementing engine sounds

if __name__ == "__main__":
    main()
