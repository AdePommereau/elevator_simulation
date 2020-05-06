"""This programs simulates two different lift algorithms: the most basic one (the mechanical lift) and my take on a more efficient algorithm.

The mechanical lift never changes direction until it has reached the bottom or the top.
My lift never changes direction until has finished all the task in the same direction. But he can change direction when not at the top/bottom.
I have implemented a simple GUI system. Charts are then loaded to compare the efficiency of both algorithm.
"""

import os
import random
import sys

import pygame
from pygame.sprite import Sprite


class Building(pygame.sprite.Sprite):
    """ This class manages the structure of the building. It defines the shape of the building,
        the height of the floors, the position of building and the number of floors. """

    def __init__(self, floor=20):

        """Initialisation of the class. The parameters of the building are defined."""

        pygame.sprite.Sprite.__init__(self)
        self.screen = pygame.display.get_surface()

        self.num_of_floors = floor

        self.black = (0, 0, 0)
        self.red = (255, 0, 0)

        self.floor_width = self.screen.get_width() * 0.2
        self.floor_height = (self.screen.get_height() - 20) / self.num_of_floors

        self.hor_margin = self.floor_width * 0.5
        self.ver_margin = self.floor_height * 0.30

        self.leftwall = self.screen.get_width() * 0.375
        self.ground = self.screen.get_height() - 10

        self.load_background()

    def load_background(self):

        """This function calls the draw_function and then the screen_shot function.
            It loads the picture of the building saved."""

        self.screen.fill((255, 255, 255))
        self.draw_building()
        self.screen_shot()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        background = os.path.join(current_dir, "background.bmp")
        try:
            self.image = pygame.image.load(background).convert()
        except pygame.error:
            print("Background can't be loaded")
        return

    def draw_building(self):

        """The function draws the whole building and defines the width of the lines."""

        pygame.draw.line(self.screen, self.black, (int(self.leftwall), 10), (int(self.leftwall), int(self.ground)), 3)
        pygame.draw.line(self.screen, self.black, (int(self.leftwall) + int(self.floor_width), 10),
                         (int(self.leftwall) + int(self.floor_width), int(self.ground)), 3)
        pygame.draw.line(self.screen, self.black, (10, int(self.ground)),
                         (int(self.screen.get_width()) - 10, int(self.ground)), 5)

        for i in range(10, int(self.screen.get_height()), int(self.floor_height)):
            pygame.draw.line(self.screen, self.black, (int(self.leftwall), i),
                             (int(self.leftwall) + int(self.floor_width), i), 3)

        return

    def screen_shot(self):

        """This function saves the building defined in the __init__ function as a picture
            that can then be loaded. """

        pygame.image.save(self.screen, "background.bmp")

        return


class Customer(pygame.sprite.Sprite):
    """This class manages all the information about the customers using the lift:
        ID, direction, their current floor and the floor they want to go to."""

    def __init__(self, floor):

        """Initialisation of the class. The parameters of the customer are defined."""

        pygame.sprite.Sprite.__init__(self)
        self.ID = random.randrange(1, 100, 1)
        self.finished = False
        self.num_of_floors = floor
        self.cur_floor = random.randrange(0, self.num_of_floors, 1)  # for the sake of better showing the
        # effectiveness, I am not putting customers on the last floor.
        self.dst_floor = random.randrange(0, self.num_of_floors, 1)
        self.direction = -1
        self.update()

    def update(self):

        """This function decides the direction of the customers"""

        # finds direction by comparing current floor with destination floor
        if self.dst_floor == self.cur_floor:
            self.finished = True
            self.direction = -1
        elif self.cur_floor < self.dst_floor:
            self.direction = 1
            self.finished = False
        else:
            self.direction = 0
            self.finished = False

        return


class Elevator(pygame.sprite.DirtySprite):

    def __init__(self, floor_num, position, c):

        """Initialisation of the class. Defines the settings of the lift image: position, size, scale..
        I am not using a picture for the elevator so that it can be rescaled depending on the number of floors."""

        pygame.sprite.DirtySprite.__init__(self)
        self.screen = pygame.display.get_surface()

        self.num_of_floors = floor_num
        # floor to start from
        self.cur_floor = 0
        # direction to start from -> start from groundfloor so can only go up (1 is up, 0 is down, -1 is stay)
        self.direction = 1
        # to keep track of the number of floors stop at
        self.floor_count = 0
        # to keep tracked of the number of floors passed
        self.passed_floor = [0]
        self.cost = 0

        # width and height of lift
        self.floor_width = self.screen.get_width() * position  # 0.1 for mecha_lift and 0.35 for my_lift
        self.floor_height = (self.screen.get_height() - 22) / self.num_of_floors

        self.hor_margin = self.floor_width * 0.4
        self.ver_margin = self.floor_height * 0.09

        self.lift_width = int(self.floor_width)
        self.lift_height = int(self.floor_height)
        self.moving = False
        self.overload = False
        self.going_up = True
        self.load = 10

        self.leftwall = self.screen.get_width() * 0.375
        self.ground = self.screen.get_height() - 17

        self.allcustomer = pygame.sprite.Group()  # basically a list of customers objects ( class customer is sprite
        # so better in sprite group)
        self.elevator_customer = pygame.sprite.Group()
        self.removed_customer = []
        self.finished_customer = 0

        self.add_customer(pygame.sprite.Group(c))  # add lists of customers to a more global list

        self.cur_pixel = int((self.num_of_floors - self.cur_floor - 1) * self.floor_height + 10 + (self.ver_margin / 2))
        self.next_floor = int()  # returns floor to go next

        self.load_lift_image()

        self.rect = self.image.get_rect().move(int(self.leftwall + self.hor_margin), self.cur_pixel)

    def add_customer(self, customer_list):

        """Adds customers created above to the allcustomer"""

        for customer in customer_list:
            self.allcustomer.add(customer)
        self.floor_initialize()

    def floor_initialize(self):

        """This function keeps track of the floors the elevator has to go to depending on the customers.
            It basically checks when new customer is added. It creates a list of floors to go to """

        self.floor_list = []
        for floor_num in range(0, self.num_of_floors):

            floor_customer = []

            for i in self.allcustomer:
                if i.cur_floor == floor_num and i.finished == False and (i not in self.elevator_customer):
                    floor_customer += (i,)
            floor = pygame.sprite.Group(floor_customer)  # groups customers by floor
            self.floor_list += (floor,)  # add groups to a more general list --> list of list

        return

    def load_lift_image(self, image_name):

        """As the building, this function loads the image of the lift defined at the start of the class.
        It also resizes the image depending on the number of floors."""

        current_dir = os.path.dirname(os.path.abspath("__file__"))
        lift_image = os.path.join(current_dir, image_name)

        self.image = pygame.image.load(lift_image)
        rect = self.image.get_rect()
        ratio = rect[3] / self.lift_height
        rect = [i / ratio for i in rect]
        self.image = pygame.transform.scale(self.image, (int(rect[2]), int(rect[3])))

    def cancel_customer(self, customer_list):

        """This function removes customers of the list when they have reached their desired floor."""

        for customer in customer_list:
            if self.cur_floor == customer.dst_floor:  # removes customer from the list if it arrives at destination
                customer.finished = True
                customer.in_elevator = False
                customer.cur_floor = self.cur_floor
                customer.update()
                customer_list.remove(customer)
                self.finished_customer += len(self.removed_customer)
        return

    def next_stop(self):

        """This function decides the next stops that the lift will stop at.
            It is basically the algorithm for my lift."""

        up = []
        down = []
        same = []  # to handle duplicates

        """iterate through the lift of all floors and by comparing the lift current floor to the customer current floor 
            decide in which list to put the customer"""
        for i in range(len(self.floor_list)):  # iterates through the list of all floors
            if len(self.floor_list[i]):  # if there is something
                for customer in self.floor_list[i]:
                    if type(self) is My_Elevator:
                        if self.cur_floor == customer.cur_floor:  # if the customer is on the same floor as the lift
                            # check the direction of the customer either up or down
                            same.append(i)
                        elif self.cur_floor < customer.cur_floor:
                            up.append(i)
                        else:
                            down.append(i)
                    else:
                        if self.cur_floor < customer.cur_floor:
                            up.append(i)
                        elif self.cur_floor > customer.cur_floor:
                            down.append(i)
            # when the lift has served everyone but their is still people inside - only runned at the end
            elif self.next_floor is None and len(self.elevator_customer):
                for customer in self.elevator_customer:  # if the list of customers is empty but the lift is not
                    # empty, go to the destination floor of the customers in the lift
                    if type(self) is My_Elevator:
                        if self.cur_floor == customer.dst_floor:
                            same.append(customer.dst_floor)
                            self.elevator_customer.remove(customer)
                        elif self.cur_floor < customer.dst_floor:
                            up.append(customer.dst_floor)
                            self.elevator_customer.remove(customer)
                        else:
                            down.append(customer.dst_floor)
                            self.elevator_customer.remove(customer)
                    else:
                        if self.cur_floor < customer.dst_floor:
                            up.append(customer.dst_floor)
                            self.elevator_customer.remove(customer)
                        else:
                            down.append(customer.dst_floor)
                            self.elevator_customer.remove(customer)

            # only when the lifts have finished
            if self.next_floor is None and len(self.elevator_customer) == 0:
                if type(self) is Mecha_Elevator:
                    print("mecha done")
                if type(self) is My_Elevator:
                    print("my done")

        # make sure that the mechanical lift goes to the endpoints
        if type(self) is Mecha_Elevator:
            if self.direction == 1 and len(up) == 0 and len(down):
                up.append(self.num_of_floors - 1)
            if self.direction == 0 and len(down) == 0 and len(up):
                up.append(0)
            if self.cur_floor == self.num_of_floors - 1:
                self.direction = 0
            elif self.cur_floor == 0:
                self.direction = 1

        # if direction is up
        if self.direction == 1:
            if not self.overload:
                if len(up):
                    return min(up)  # return smallest floor to go up to

        elif self.direction == 0:
            if not self.overload:
                if len(down):
                    return max(down)

        # handles the change of direction from the non mechanical lift
        if len(same):
            if self.direction == 0:
                self.direction = 1
            elif self.direction == 1:
                self.direction = 0
            elif self.direction == -1:
                self.direction = 1
            return self.next_stop()

        else:
            self.direction = -1

    def move_one_step(self, dst_floor):

        """The function manages the change in directions. Updward or downward. It also handles "the graphical" maths
            to check if the lift is at the right place. Decices when the current floor = destination floor"""
        count = 1

        if self.direction == 1:  # moves elevator depending of the direction
            count = - abs(count)
        elif self.direction == 0:
            count = abs(count)
        else:
            return

        tmp = self.num_of_floors - dst_floor - 1
        dst_floor_pixel = int((self.floor_height * tmp) + 10 + (self.ver_margin / 2))

        # if the current pixel is equal to the destination pixel calculated above
        if self.cur_pixel == dst_floor_pixel:
            # means that the current floor is equal to the destination floor --> do the required
            self.cur_floor = dst_floor
            # remove the customer from the list of customers and from the elevator
            self.cancel_customer(self.floor_list[self.cur_floor])
            self.cancel_customer(self.elevator_customer)
            # add customer to the list of all removed customers
            self.removed_customer.append(self.elevator_customer)  # add customer to a list of all finished customers

            # increase the floor count by one
            self.floor_count += 1
            # add the floor to the list of floors stopped at to calculate the cost
            self.passed_floor.append(self.cur_floor)
            self.cost += abs(
                self.passed_floor[len(self.passed_floor) - 1] - self.passed_floor[len(self.passed_floor) - 2])

            # register the customer in elevator
            if self.floor_list[self.cur_floor]:
                self.register_customer(self.floor_list[self.cur_floor])
            self.moving = False
            pygame.time.delay(500)
            return

        self.rect = self.rect.move(0, count)
        self.cur_pixel += count
        self.moving = True

    def register_customer(self, customer_list):

        '''Adds customer to the elevator_customer list --> list of customers in the elevator.
        Customers are added into that list from the big customer_list containing all the customers.'''

        load = len(self.elevator_customer)

        for customer in customer_list:
            # check if lift is not full
            if load > self.load:
                self.overload = True
                return
            elif customer.finished is False and self.cur_floor == customer.cur_floor and self.direction == customer.direction:
                self.elevator_customer.add(customer)
                customer_list.remove(customer)
            load += 1

    def update(self):

        """update function"""

        self.next_floor = self.next_stop()

        if not self.moving:
            self.register_customer(self.floor_list[self.cur_floor])

            if self.direction != -1:

                if self.cur_floor < self.next_floor:
                    self.direction = 1
                elif self.cur_floor > self.next_floor:
                    self.direction = 0

            if self.direction == -1:
                """
                for customer in self.allcustomer:
                    print (customer.ID, customer.cur_floor, customer.dst_floor, customer.finished, " direction=> ", customer.direction)
                """

            else:
                self.move_one_step(self.next_floor)
        else:
            self.move_one_step(self.next_floor)
        self.dirty = 1
        return


class Mecha_Elevator(Elevator):
    """class of the mechanical lift. handles position, picture, labels.."""

    def __init__(self, floor_num, position, c):
        super().__init__(floor_num, position, c)

    def load_lift_image(self):
        image_name = 'mecha_lift.png'
        super().load_lift_image(image_name)

    def draw(self, surface):
        """manages all the labels of the lifts. Gives information on the lift. I am not using them since pygame is really slow with handling these and really slows down my program"""
        # elevator_name = Label("Mechanical Elevator", 30, (0, 0, 255), (26, 50), "topleft", surface)
        # current = Label("Current floor: " + str(self.cur_floor), 20, (0, 0, 0), (50, 150), "topleft", surface)
        # inside = Label("People in elevator: " + str(len(self.elevator_customer)), 20, (0, 0, 0), (50, 170),"topleft", surface)
        # delivered = Label("Delivered at floor: " + str(len(self.removed_customer)), 20, (0, 0, 0), (50, 190),"topleft", surface)
        # cost = Label("Total stops: " + str(self.floor_count), 20, (0, 0, 0), (50, 300), "topleft", surface)
        floor_cost = Label("Total cost: " + str(self.cost), 20, (0, 0, 0), (50, 320), "topleft", surface)
        # total = Label("Total finished customers: " + str(self.finished_customer), 20, (0, 0, 0), (50, 340), "topleft", surface)


class My_Elevator(Elevator):
    """class of the non mechanical lift. handles position, picture, labels.."""

    def __init__(self, floor_num, position, c):
        super().__init__(floor_num, position, c)
        self.floor_count = 0

    def load_lift_image(self):
        image_name = 'my_lift.png'
        super().load_lift_image(image_name)

    def draw(self, surface):
        """manages all the labels of the lifts. Gives information on the lift. I am not using them since pygame is really slow with handling these and really slows down my program"""
        # elevator_name = Label("My Elevator", 30, (255, 0, 0), (555, 50), "topright", surface)
        # current = Label("Current floor: " + str(self.cur_floor), 20, (0, 0, 0), (430, 150), "topleft", surface)
        # inside = Label("People in elevator: " + str(len(self.elevator_customer)), 20, (0, 0, 0), (430, 170),"topleft", surface)
        # delivered = Label("Delivered at floor: " + str(len(self.removed_customer)), 20, (0, 0, 0), (430, 190),"topleft", surface)
        # cost = Label("Total stops: " + str(self.floor_count), 20, (0, 0, 0), (430, 300), "topleft", surface)
        floor_cost = Label("Total cost: " + str(self.cost), 20, (0, 0, 0), (430, 320), "topleft", surface)
        # total = Label("Total finished customers: " + str(self.finished_customer), 20, (0, 0, 0), (430, 340), "topleft", surface)


class Label(Sprite):
    """handles all the labels of the simulation."""

    def __init__(self, text, size, color, position, anchor, surface):
        Sprite.__init__(self)
        self._font = pygame.font.Font(None, size)
        self._text = text
        self._color = color
        self._anchor = anchor
        self._position = position
        self._surface = surface
        self._render()
        self.draw(self._surface)

    def _render(self):
        self.image = self._font.render(self._text, 1, self._color)
        self.rect = self.image.get_rect(**{self._anchor: self._position})

    def clip(self, rect):
        self.image = self.image.subsurface(rect)
        self.rect = self.image.get_rect(**{self._anchor: self._position})

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def set_text(self, text):
        self._text = text
        self._render()

    def set_font(self, font):
        self._font = font
        self._render()

    def set_color(self, color):
        self._color = color
        self._render()

    def set_position(self, position, anchor=None):
        self._position = position
        if anchor:
            self._anchor = anchor

        self.rect = self.image.get_rect(**{self._anchor: self._position})


def main():
    pygame.init()
    current_dir = os.path.dirname(os.path.abspath("__file__"))

    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Elevators simulation")

    # change the value to change the number of floors. (preferably between 5 and 100 but can go higher)
    total_floors = 20

    building = Building(total_floors)

    c = []

    for i in range(0, 10):  # create list of Customers
        c.append(Customer(total_floors), )

    mecha_elevator = Mecha_Elevator(total_floors, 0.1, c)
    mecha_lift = pygame.sprite.LayeredDirty(mecha_elevator)

    myelevator = My_Elevator(total_floors, 0.35, c)
    lift = pygame.sprite.LayeredDirty(myelevator)

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(building.image, (0, 0))

        mecha_elevator.draw(screen)
        mecha_lift.update()
        mecha_lift.draw(screen)

        myelevator.draw(screen)
        lift.update()
        lift.draw(screen)

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
