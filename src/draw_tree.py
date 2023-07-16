from collections import defaultdict
from itertools import zip_longest
import re
from typing import Any, DefaultDict, Iterable, Literal, Sequence, Union
import pygame
from pygame import sprite
from .family_tree import Tree, Person, Relation, Sex, Family
from random import randrange
from numbers import Number
from PIL import Image
import time
from math import ceil
import sys
from functools import cmp_to_key
import tkinter as tk


class Vector:
    def __init__(self, point) -> None:
        self.values = list(point)

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __len__(self):
        return len(self.values)

    def __add__(self, other) -> 'Vector':

        if isinstance(other, Number):
            return Vector(
                [v + other for v in self]
            )

        if isinstance(other, Sequence):
            if len(self) != len(other):
                raise ValueError('Vectors must be same size')

            return Vector(
                [x + y for x, y in zip(self, other)]
            )

        raise NotImplementedError


    def __sub__(self, other) -> 'Vector':

        if isinstance(other, Sequence):
            if len(self) != len(other):
                raise ValueError('Vectors must be same size')

            return Vector(
                [x - y for x, y in zip(self, other)]
            )

        elif isinstance(other, Number):
            return Vector(
                [v - other for v in self]
            )

        raise NotImplementedError

    def __truediv__(self, other: Number) -> 'Vector':
        return Vector(
            [v / other for v in self]
        )

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.values == other.values

    def __str__(self) -> str:
        return f'Vector({self.values})'


class Node(pygame.sprite.Sprite):
    def __init__(self, person: Person, pos, offset, complete=True):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(pygame.font.get_default_font(), 24)
        self.person = person
        self.parents: list['Node'] = []
        self.spouses: list['Node'] = []

        self.clicked = False
        self.color = (200, 200, 200) if complete else (250, 220, 250)
        self.click_offset = 0, 0
        self.click_move = None
        self.pos = Vector(pos)
        self.redraw()

        self.update(offset, None)

    def redraw(self):
        self.text: pygame.Surface = self.font.render(self.person.name, True, (0, 0, 0))
        self.image = pygame.Surface(self.text.get_size())
        self.image.fill((240, 240, 240))

        pygame.draw.rect(
            self.image,
            self.color,
            (5, 5, *self.image.get_size()),
        )
        self.image.blit(self.text, (0, 0))

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

    def update(self, offset, mouse_pos):
        if self.clicked:
            self.pos = Vector((
                mouse_pos[0] - offset[0] + self.click_offset[0],
                mouse_pos[1] - offset[1] + self.click_offset[1]
            ))
            # self.rect.center = mouse_pos
        # else:
        self.rect.center = self.pos[0] + offset[0], self.pos[1] + offset[1]

    def click(self, mouse_pos):
        self.click_move = self.pos
        self.click_offset = (
            self.rect.centerx - mouse_pos[0],
            self.rect.centery - mouse_pos[1]
        )
        if self.rect.collidepoint(mouse_pos):
            self.clicked = True

    def unclick(self):
        if self.clicked:
            if self.click_move == self.pos:
                global pressed
                pressed = self.person
        self.clicked = False

    def move_spouse(self, people: Sequence[Person]):
        for spouse in self.person.spouses:
            if spouse.person not in people:
                continue
            if self.person.sex == Sex.male:
                self.pos[0] += (spouse.person.sprite.rect.left - self.rect.right)/2-10
            else:
                self.pos[0] += (spouse.person.sprite.rect.right - self.rect.left)/2+10

    def move_children(self, people: Sequence[Person]):
        positions = []
        for child in self.person.children:
            if child.person in people:
                positions.append(child.person.sprite.rect.centerx)
        if positions:
            self.pos[0] += sum(positions)/len(positions) - self.rect.centerx

    def set_pos(self, pos):
        self.pos = Vector(pos)





def sort_people(tree: Tree, head: Person, p1: Person, p2: Person):
    path1 = tree.path(head, p1)
    path2 = tree.path(head, p2)
    # print(p1.id, p2.id)
    generation = tree.generation(head, p1)
    assert generation == tree.generation(head, p2)
    # print(f'{generation=}')
    # print(f'{p1.name=}')
    # print(f'{p2.name=}')
    # print([p.name for p in path1])
    # print([p.name for p in path2])

    if generation > 0:
        ### THIS WORKS DON'T MESS WITH IT
        last_s1 = last_s2 = None
        for s1, s2 in zip_longest(path1, path2):
            s1: Person
            s2: Person
            if not s1 or not s2:
                break
            if s1 != s2:
                # father should be left of mother
                if last_s1.get_relation(s1) == Relation.father:
                    return -1
                else:
                    return 1
            last_s1 = s1
            # last_s2 = s2

        if len(path1) > len(path2):
            if p2.sex == Sex.male:
                return -1
            return 1
        elif len(path1) < len(path2):
            if p1.sex == Sex.male:
                return 1
            return -1
        else:
            raise Exception("shouldn't be here looking for ancestor")
    elif generation < 0:
        # if (p1.id == '12' and p2.id == '34') or (p2.id == '12' and p1.id == '34'):
        #     print(len(path1) > len(path2))
        #     print(len(path1) < len(path2))
        for s1, s2 in zip_longest(path1, path2):
            s1: Person
            s2: Person
            if not s1 or not s2:
                break
            if s1 != s2:
                if s1.dob is not None and s2.dob is not None:
                    if s1.dob < s2.dob:
                        return -1
                    elif s1.dob > s2.dob:
                        return 1
                else:
                    if s1.name < s2.name:
                        return -1
                    elif s1.name > s2.name:
                        return 1
                    else:
                        print('bbbbbbbbbbbbbbbbbbb')
                        print(s1.name, s2.name)
        last_relation = path1[-1].get_relation(path2[-1])
        if last_relation and last_relation.is_spouse():
            if path1[-1].sex == Sex.male:
                return -1
            else:
                return 1
        else:
            # should be sibling
            if path1[-1].dob is not None and path2[-1].dob is not None:
                if path1[-1].dob < path2[-1].dob:
                    return -1
                elif path2[-1].dob > path1[-1].dob:
                    return 1
            else:
                if path1[-1].name < path2[-1].name:
                    return -1
                elif path1[-1].name > path2[-1].name:
                    return 1
                else:
                    print('eeeeeeeeeeeeeeeeeee')
                    print(path1[-1].name, path2[-1].name)
        return randrange(-1, 2)
    else:
        # print('fffffffffffffffff')
        # return int(input(f'{p1.name} vs {p2.name}'))
        return randrange(-1, 2)

    # raise NotImplementedError


def _draw(screen, offset: tuple[int, int], nodes: dict[Any, Node], nodeGroup, generations):
    screen.fill((255, 255, 255))
    # screen.blit(people[0].image, (0, 0))

    for i in generations:
        pygame.draw.rect(
            screen,
            (240, 240, 240),
            (0, i*300+offset[1]+40, screen.get_width(), 40)
        )

    people = [node.person for node in nodeGroup]

    for node in nodes.values():
        person = node.person
        # draw a line to parents
        #   if there's 1 parent in the tree draw to them
        #   if there's 2 draw a line between them
        if len(node.parents) == 1:
            parent = node.parents[0]
            pygame.draw.line(screen, (0, 0, 0), node.rect.center, parent.rect.center)
        elif len(node.parents) == 2:
            parent0 = node.parents[0]
            parent1 = node.parents[1]
            new_pos = (Vector(parent0.rect.center) +
                        Vector(parent1.rect.center))/2
            pygame.draw.line(screen, (0, 0, 0), node.rect.center, new_pos)

        # draw a red line between spouses
        for spouse in node.spouses:
            pygame.draw.line(screen, (255, 0, 0), node.rect.center, spouse.rect.center, 3)

    nodeGroup.draw(screen)

    pygame.display.update()


def drawTree(tree: Tree, head: Person=None):
    global pressed
    pygame.init()

    # print('start...')

    # print(sort_people(tree, tree.head, tree.get('1'), tree.get('18')))
    # print(sort_people(tree, tree.head, tree.get('3'), tree.get('14')))

    if head is None:
        head = tree.head

    offset: Vector = Vector(screen_size) / 2
    drag_screen = None


    generation_rows: DefaultDict[int, list[Node]] = defaultdict(list)
    nodes: dict[Any, Node] = {}

    # create nodes
    people = tree.explore(levels=lookback)
    # print(people)
    for person in people:
        nodes[person.id] = Node(person, (0, 0), offset)
        gen = tree.generation(head, person)
        generation_rows[gen].append(nodes[person.id])

    generations = tuple(generation_rows.keys())

    # filter by generation
    for generation in generation_rows:
        generation_rows[generation].sort(key=cmp_to_key(lambda x, y: sort_people(tree, head, x.person, y.person)))
        count = len(generation_rows[generation])
        for i, node in enumerate(generation_rows[generation]):
            node.set_pos((
                (i - count/2) * 500,
                (max(generation_rows)-generation) * 300
            ))

    # connect nodes
    for node in nodes.values():
        for parent in node.person.parents:
            if parent.person_id not in nodes:
                continue
            node.parents.append(nodes[parent.person_id])
        for spouse in node.person.spouses:
            if spouse.person_id not in nodes:
                continue
            node.spouses.append(nodes[spouse.person_id])

    print('total =', len(nodes))
    print('---done---')
    screen: pygame.Surface = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
    nodeGroup = pygame.sprite.Group(nodes.values())

    while True:
        mouse = Vector(pygame.mouse.get_pos())
        if drag_screen is not None:
            diff = mouse - drag_screen
            view_offset = offset + diff
        else:
            view_offset = offset

        nodeGroup.update(view_offset, mouse)
        if pressed:
            press(tree, pressed)
            if not pygame.get_init():
                return
            for node in nodes.values():
                node.redraw()
        pressed = None

        _draw(screen, view_offset, nodes, nodeGroup, generations)

        for e in pygame.event.get():
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == pygame.BUTTON_RIGHT:
                    drag_screen = mouse
                elif e.button == pygame.BUTTON_LEFT:
                    for n in nodeGroup:
                        n.click(mouse)

            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == pygame.BUTTON_RIGHT and drag_screen is not None:
                    drag_screen = None
                    offset = view_offset
                elif e.button == pygame.BUTTON_LEFT:
                    for n in nodeGroup:
                        n.unclick()

            elif e.type == pygame.QUIT:
                pygame.quit()
                return
            # elif e.type == pygame.KEYDOWN and e.key == pygame.K_h:
            #     for person in tuple(people):
            #         if person.sprite.rect.collidepoint(mouse):
            #             nodeGroup.remove(person.sprite)
            #             people.remove(person)
            #             for generation in generations:
            #                 generation_rows[generation].sort(key=lambda x:x.sprite.pos[0])
            #                 if person in generation_rows[generation]:
            #                     generation_rows[generation].remove(person)
            # elif e.type == pygame.KEYDOWN and e.key == pygame.K_g:
            #     for person in tuple(people):
            #         if person.sprite.rect.collidepoint(mouse):
            #             any_children = False
            #             for sib in person.siblings:
            #                 if sib.person.name.endswith(' children'):
            #                     sib.person.name = str(int(sib.person.name.split()[0]) + 1) + ' children'
            #                     any_children = True
            #                     sib.person.sprite.redraw()
            #             if not any_children:
            #                 person.name = '1 children'
            #                 person.sprite.redraw()
            #                 break
            #             nodeGroup.remove(person.sprite)
            #             people.remove(person)
            #             for generation in generations:
            #                 generation_rows[generation].sort(key=lambda x:x.sprite.pos[0])
            #                 if person in generation_rows[generation]:
            #                     generation_rows[generation].remove(person)
            # elif e.type == pygame.KEYDOWN and e.key == pygame.K_r:
            #     for generation in generations:
            #         # sort all rows based on their new positions
            #         generation_rows[generation].sort(key=lambda x:x.sprite.pos[0])
            #         if pygame.key.get_mods() & pygame.KMOD_CTRL:
            #             for i, person in enumerate(generation_rows[generation]):
            #                 old = person.sprite.pos[0]
            #                 new = (i - len(generation_rows[generation]) / 2) * 300
            #                 person.sprite.pos[0] = new
            #                 person.sprite.rect.centerx += new - old
            #         for i, person in enumerate(generation_rows[generation]):
            #             person.sprite.pos[1] = generation * 300 + 60
            #             if person.sprite.pos[0] > 0:
            #                 if i > 0:
            #                     diff = person.sprite.rect.left - generation_rows[generation][i-1].sprite.rect.right - 40
            #                     if diff < 0 or pygame.key.get_mods() & pygame.KMOD_CTRL:
            #                         person.sprite.pos[0] -= diff
            #                         person.sprite.rect.x -= diff
            #         for i, person in reversed(tuple(enumerate(generation_rows[generation]))):
            #             person.sprite.pos[1] = generation * 300 + 60
            #             if person.sprite.pos[0] < 0:
            #                 if i < len(generation_rows[generation])-1:
            #                     diff = generation_rows[generation][i+1].sprite.rect.left - person.sprite.rect.right - 40
            #                     if diff < 0 or pygame.key.get_mods() & pygame.KMOD_CTRL:
            #                         person.sprite.pos[0] += diff
            #                         person.sprite.rect.x += diff
            # elif e.type == pygame.KEYDOWN and e.key == pygame.K_s:
            #     rect = pygame.Rect(tree.head.sprite.rect)
            #     for node in nodeGroup:
            #         rect.union_ip(node.rect)
            #     sub = screen.subsurface(screen.get_rect())
            #     offset -= rect.topleft

            #     from PIL import Image
            #     im = Image.new(mode='RGB', size=rect.size)

            #     for y in range(ceil(rect.height / screen.get_height())):
            #         for x in range(ceil(rect.width / screen.get_width())):
            #             view_offset = offset - (x * screen.get_width(), y * screen.get_height())
            #             # view_offset = offset - (x * 3, y * 3)
            #             nodeGroup.update(view_offset, mouse)
            #             # print(offset)
            #             _draw(screen, view_offset, people, nodeGroup)
            #             screenshot = pygame.image.tostring(sub, 'RGB')
            #             im.paste(Image.frombytes('RGB', screen.get_size(), screenshot), (x * screen.get_width(), y * screen.get_height()))
            #             # q = True
            #             time.sleep(0.1)
            #             pygame.event.get()

            #     im.save('screenshot.png')
            #     im.close()


def press(tree: Tree, person: Person):
    main = tk.Tk()
    def task():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                main.destroy()
                pygame.quit()
                return
        main.after(1000, task)  # reschedule event in 1 seconds

    def edit():
        def save_and_close():
            person.name = entry_name.get()
            person.dob = entry_dob.get()
            person.dod = entry_dod.get()
            newWindow.destroy()

        newWindow = tk.Toplevel(main)

        tk.Label(newWindow, text='name').pack(anchor='w')
        entry_name = tk.Entry(newWindow, width=100)
        entry_name.pack(anchor='w', fill='x')
        if person.name: entry_name.insert(tk.END, person.name)

        tk.Label(newWindow, text='dob').pack(anchor='w')
        entry_dob = tk.Entry(newWindow)
        entry_dob.pack(anchor='w', fill='x')
        if person.dob: entry_dob.insert(tk.END, person.dob)

        tk.Label(newWindow, text='dod').pack(anchor='w')
        entry_dod = tk.Entry(newWindow)
        entry_dod.pack(anchor='w', fill='x')
        if person.dod: entry_dod.insert(tk.END, person.dod)

        tk.Button(newWindow, text='save & close', command=save_and_close).pack()


    main.after(1000, task)
    # for line in str(person).split('\n'):
    #     tk.Label(main, text=line.strip()).pack()
    tk.Label(main, text=person.name).pack()
    if person.dob and person.dod:
        tk.Label(main, text=f'{person.dob} - {person.dod}').pack()
    elif person.dob:
        tk.Label(main, text=f'b: {person.dob}').pack()
    elif person.dod:
        tk.Label(main, text=f'd: {person.dod}').pack()

    tk.Button(main, text='edit', command=edit).pack(side='left')
    tk.Button(main, text='close', command=main.destroy).pack(side='right')
    main.mainloop()

if __name__ == '__main__':
    """sort_people tdd"""
    import csv


    lookback = int(sys.argv[1]) if len(sys.argv) > 2 else None
    # lookback = 3
    screen_size = (1500, 900)

    pressed = None

    person_list: list[Person] = []
    with open('data/example1.csv') as f:
        rdr = csv.DictReader(f)
        for line in rdr:
            fam = []
            if line['family']:
                for person in line['family'].split(','):
                    p_rel, p_id, *notes = person.split(':')
                    if notes:
                        notes = notes[0]
                    fam.append(Family(Relation[p_rel], p_id, notes=notes))

            sex = Sex[line['sex']] if line['sex'] else None
            p = Person(
                # name
                # sources
                # family
                # dob
                # dod
                # sex
                # child_complete
                # spouse_complete
                # notes
                # id
                name=line['name'],
                dob=line['dob'],
                dod=line['dod'],
                sex=sex,
                family=fam,
                child_complete=line['child complete'],
                spouse_complete=line['spouse complete'],
                sources=line['sources'],
                notes=line['notes'],
                id=line['id'] or None,
            )
            person_list.append(p)

    family = Tree(person_list)
    family.set_head('Joshua Thomas Andrews')

