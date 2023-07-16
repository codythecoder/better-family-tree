from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from functools import lru_cache
from typing import Any, ClassVar, Optional, Union
import re


re_fix_enum = re.compile(r'<([\w\.]+): [^>]+>')


def escape_csv(text):
    text = text.replace('"', '""')
    if ',' in text or '\n' in text:
        text = f'"{text}"'
    return text


class Sex(Enum):
    male = 1
    female = 2
    other = 3
    unknown = 4


class Relation(Enum):
    parent = 1
    child = 2
    spouse = 3
    partner = 4
    sibling = 5
    step_sibling = 6
    adopted_child = 7
    adopted_parent = 8
    # TODO ungenderify
    father = 9
    mother = 10
    son = 11
    daughter = 12

    def is_parent(self):
        return self in (
            Relation.parent,
            Relation.adopted_parent,
            Relation.father,
            Relation.mother,
        )

    def is_child(self):
        return self in (
            Relation.child,
            Relation.adopted_child,
            Relation.son,
            Relation.daughter,
        )

    def is_spouse(self):
        return self in (
            Relation.spouse,
            Relation.partner,
        )

@dataclass
class Family:
    """What relation one person has to another"""
    relation: Relation
    person_id: int
    person: Union['Person', None] = None
    notes: str = ''

    def __str__(self) -> str:
        if self.person is None:
            return repr(self)
        return f'Family({self.relation}, {self.person_id}, {repr(self.person.name)})'

    def __repr__(self) -> str:
        return f'Family({self.relation}, {self.person_id})'


@dataclass
class Person:
    """A person as seen inside a family tree"""
    name: str
    sources: list[str] = field(default_factory=list)

    family: list[Family] = field(default_factory=list)

    dob: Optional[str] = None
    dod: Optional[str] = None

    sex: Sex = Sex.unknown

    child_complete: Any = False
    spouse_complete: Any = False
    double_check: bool = False
    ignore: bool = False

    notes: str = ''

    id: Any = None
    # make sure that we don't have any duplicate IDs
    # curr_id: ClassVar[int] = 0
    seen_ids: ClassVar[set[int]] = set()

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = self.name
        assert self.id not in Person.seen_ids

        # if self.id is not None:
        #     Person.curr_id = max(self.id + 1, Person.curr_id)
        # else:
        #     self.id = Person.curr_id
        #     Person.curr_id += 1

        Person.seen_ids.add(self.id)
        assert 0 <= len(self.parents) <= 2

    def rename(self, new_id):
        if new_id is None:
            new_id = self.name

        if new_id == self.id:
            return

        assert new_id not in Person.seen_ids
        Person.seen_ids.remove(self.id)
        self.id = new_id
        Person.seen_ids.add(self.id)


    def __hash__(self) -> int:
        return hash(self.id)

    def save_str(self):
        out = repr(self)
        out = re_fix_enum.sub(r'\1', out)
        out = out.replace('datetime.', '')
        return out

    def save_str2(self):
        assert '"' not in self.name and ',' not in self.name
        print_id = None
        if self.id != self.name:
            print_id = self.id

        family = []
        for fam in self.family:
            if fam.relation.is_parent() or fam.relation.is_spouse():
                if fam.notes:
                    family.append(f'{fam.relation.name}:{fam.person_id}:{escape_csv(fam.notes)}')
                else:
                    family.append(f'{fam.relation.name}:{fam.person_id}')

        if isinstance(self.sources, list):
            sources = ','.join(self.sources)
        else:
            sources = self.sources
        return f'{self.name},{self.dob or ""},{self.dod or ""},{self.sex.name},{escape_csv(",".join(family))},{self.child_complete or ""},{self.spouse_complete or ""},{escape_csv(sources) or ""},{escape_csv(self.notes) or ""},{print_id}'

    def get_relation(self, other: 'Person'):
        for fam in self.family:
            if fam.person_id == other.id:
                return fam.relation
        return None

    def __str__(self) -> str:
        fam = [
            str(f) for f in self.family
        ]
        sep = ',\n        '
        parts = [
            f"name={repr(self.name)}",
            f"id={self.id}",
            f"sources={self.sources}",
            f"family=[\n        {sep.join(str(f) for f in self.family)}\n    ]",
            f"dob={repr(self.dob)}",
            f"dod={repr(self.dod)}",
            f"sex={self.sex}",
            f"child_complete={repr(self.child_complete)}",
            f"spouse_complete={repr(self.spouse_complete)}",
            f"notes={repr(self.notes)}",
        ]
        sep = ',\n    '
        return f"""Person(\n    {sep.join(parts)}\n)"""

    def __repr__(self) -> str:
        fam = [
            repr(f) for f in self.family
        ]
        sep = ',\n        '
        parts = [
            f"name={repr(self.name)}",
            f"id={self.id}",
            f"sources={self.sources}",
            f"family=[\n        {sep.join(str(f) for f in self.family)}\n    ]",
            f"dob={repr(self.dob)}",
            f"dod={repr(self.dod)}",
            f"sex={self.sex}",
            f"child_complete={repr(self.child_complete)}",
            f"spouse_complete={repr(self.spouse_complete)}",
            f"notes={repr(self.notes)}",
        ]
        sep = ',\n    '
        return f"""Person(\n    {sep.join(parts)}\n)"""

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        return self.id == other.id

    @property
    def parent_complete(self):
        return len(self.parents) == 2

    @property
    def complete(self):
        return self.parent_complete and self.child_complete

    @property
    def parents(self):
        return [
            f
            for f in self.family
            if f.relation.is_parent()
        ]

    @property
    def children(self):
        return [
            f
            for f in self.family
            if f.relation.is_child()
        ]

    @property
    def spouses(self):
        return [
            f
            for f in self.family
            if f.relation.is_spouse()
        ]

    @property
    def siblings(self):
        return [
            f
            for f in self.family
            if f.relation == Relation.sibling
        ]


class Tree:
    """A family tree"""
    def __init__(self, tree=None):
        self.tree: set[Person] = set() if tree is None else set(tree)
        self._head = None
        self.connect()
        self.fix()

    def __iter__(self):
        return iter(self.tree)

    @property
    def head(self) -> Person:
        if self._head is None and self.tree:
            self._head = next(iter(self.tree))
        return self._head

    def set_head(self, head_id: Any):
        head = self.get(head_id)
        assert head is not None
        self._head = head

    def fix(self):
        for node in self.tree:
            for fam in node.family:
                if fam.person is None:
                    fam.person = self.get(fam.person_id)
                if fam.relation == Relation.parent:
                    if fam.person.sex == Sex.male:
                        fam.relation = Relation.father
                    elif fam.person.sex == Sex.female:
                        fam.relation = Relation.mother

    def connect(self):
        for node in self.tree:
            for family in node.family:
                rel = self.get(family.person_id)
                # print(f'{node.id=}')
                # print(f'{family.person_id=}')
                print(node.id, family.person_id)
                assert rel is not None
                # make sure spouse is bidirectional:
                if family.relation.is_spouse():
                    if not any(f.person_id == node.id and f.relation.is_spouse() for f in rel.family):
                        rel.family.append(
                            Family(family.relation, node.id)
                        )
                # make sure parents and children are bidirectional
                if family.relation.is_parent():
                    if not any(f.person_id == node.id for f in rel.family):
                        rel.family.append(
                            Family(Relation.child, node.id)
                        )
                if family.relation == Relation.child:
                    if not any(f.person_id == node.id for f in rel.family):
                        rel.family.append(
                            Family(Relation.parent, node.id)
                        )
                if family.relation == Relation.adopted_parent:
                    if not any(f.person_id == node.id for f in rel.family):
                        rel.family.append(
                            Family(Relation.adopted_child, node.id)
                        )
                if family.relation == Relation.adopted_child:
                    if not any(f.person_id == node.id for f in rel.family):
                        rel.family.append(
                            Family(Relation.adopted_parent, node.id)
                        )
                # make sure spouses are bidirectional
                if family.relation.is_spouse():
                    if not any(f.person_id == node.id for f in rel.family):
                        rel.family.append(
                            Family(Relation.spouse, node.id)
                        )
            # add sibling connector
            for node2 in self.tree:
                if node.id == node2.id:
                    continue
                node_parents = [f.person_id for f in node.family if f.relation.is_parent()]
                node2_parents = [f.person_id for f in node2.family if f.relation.is_parent()]

                same = len([x for x in node_parents if x in node2_parents])
                if same == 2:
                    node.family.append(
                        Family(Relation.sibling, node2.id)
                    )
                elif same == 1:
                    node.family.append(
                        Family(Relation.step_sibling, node2.id)
                    )

    def search_names(self, name: str) -> set[Person]:
        """Get a list of people who have a partial match to a name"""
        nodes: set[Person] = set()

        for node in self.tree:
            if name in node.name:
                nodes.add(node)

        return nodes

    def explore(self, head: Optional[Person]=None, levels=None) -> set[Person]:
        head = head or self.head
        nodes: set[Person] = {head}

        for node in self.explore_up(head, levels):
            nodes.add(node)
        for node in self.explore_down(head, levels):
            nodes.add(node)

        return nodes

    def re_id(self, name: str):
        match_person: list[Person] = []
        for p in self.tree:
            if p.name == name:
                match_person.append(p)
        if len(match_person) == 1:
            p_id = match_person[0].id
            p_name = match_person[0].name
            match_person[0].id = p_name
            for p in self.tree:
                for fam in match_person[0].family:
                    if fam.person_id == p_id:
                        fam.person_id = p_name

    def explore_up(self, head: Optional[Person]=None, levels=None) -> set[Person]:
        """get the family tree upwards from the head"""
        if levels == 0:
            return set()

        head = head or self.head
        nodes: set[Person] = {head}

        next_level = levels - 1 if levels else levels

        for p1 in head.family:
            if p1.relation.is_parent():
                nodes.add(p1.person)
                for p2 in p1.person.family:
                    if p2.relation.is_child():
                        nodes.add(p2.person)
                nodes.update(self.explore_up(p1.person, next_level))

        return nodes

    def explore_down(self, head: Optional[Person]=None, levels=None) -> set[Person]:
        """get the family tree downwards from the head"""
        if levels == 0:
            return set()


        head = head or self.head
        nodes: set[Person] = {head}

        # print('exploring down from', head.name, f'({levels} levels)')
        next_level = levels - 1 if levels else levels

        for p1 in head.family:
            if p1.relation.is_child():
                nodes.add(p1.person)
                for p2 in p1.person.family:
                    if p2.relation.is_parent():
                        nodes.add(p2.person)
                nodes.update(self.explore_down(p1.person, next_level))

        return nodes


    def get_incomplete_nodes(self, levels=None) -> set[Person]:
        nodes: set[Person] = set()

        for node in self.explore(levels=levels):
            # if not (node.parent_complete and node.child_complete and node.spouse_complete):
            if not (node.parent_complete and node.child_complete):
                # print(node.id, node.parent_complete, node.child_complete)
                nodes.add(node)

        return nodes

    def generation(self, p1: Person, p2: 'Person') -> int:
        level: set[tuple['Person', int]] = {(p1, 0)}
        next_level: set[tuple['Person', int]] = set()

        while True:
            for item in level:
                if p2 == item[0]:
                    return item[1]
            for person in level:
                for fam in person[0].parents:
                    next_level.add((fam.person, person[1]+1))
                for fam in person[0].children:
                    next_level.add((fam.person, person[1]-1))
            level = next_level
            next_level = set()

    def update(self, other: 'Tree', this_id: Any, other_id: Any):
        people_list = [(self.get(this_id), other.get(other_id))]

        a_seen = [this_id]
        b_seen = [other_id]
        same = [(this_id, other_id)]

        while people_list:
            a, b = people_list.pop()
            for r_a in a.family:
                if r_a.person_id in a_seen:
                    continue
                for r_b in b.family:
                    if r_b.person_id in b_seen:
                        continue
                    if r_a.person.name.split(' ', 1)[0] == r_b.person.name.split(' ', 1)[0]:
                        print('\n'*4)
                        print(r_a.person)
                        print(r_b.person)
                        if input('same: ') == 'y':

                            people_list.append((r_a.person, r_b.person))
                            a_seen.append(r_a.person_id)
                            b_seen.append(r_b.person_id)
                            same.append((r_a.person_id, r_b.person_id))
                            break

        print(same)

    def __dfs(self, search: Person, levels: int, head: Person=None):
        next_level = levels - 1
        head = head or self.head
        if head == search:
            return [head]
        if next_level == 0:
            return None

        for p1 in head.family:
            if p1.relation.is_child() or p1.relation.is_parent():
                path = self.__dfs(search, next_level, p1.person)
                if path:
                    return [head] + path
        return None

    @lru_cache
    def path(self, p1: Person, p2: Person):
        for i in range(1, len(self.tree)):
            path = self.__dfs(p2, i, head=p1)
            if path and path[-1] == p2:
                return path


    def add(self, node: Person) -> None:
        self.tree.add(node)
        self.connect()
        self.fix()

    def get(self, id: Any) -> Person:
        for node in self.tree:
            if node.id == id:
                return node

    def rename(self, old: Any, new: Any):
        for person in self.tree:
            for fam in person.family:
                assert(fam.person.id == fam.person_id)

        person = self.get(old)
        person.rename(new)
        for node in self.tree:
            for fam in node.family:
                if fam.person_id == old:
                    fam.person_id = person.id

        for person in self.tree:
            for fam in person.family:
                assert(fam.person.id == fam.person_id)
        self.connect()
        self.fix()

    def __str__(self) -> str:
        return str(self.tree)

    def __len__(self):
        return len(self.tree)

    def __contains__(self, other: Person) -> bool:
        return other in self.tree

    # def match(self, other: 'Tree', start: int, end: int) -> list[tuple[int, int]]:
    #     pass

    # def combine(self, other: 'Tree', start: int, end: int):
    #     new1 = Tree(self.tree)
    #     new2 = Tree(other.tree)

    #     return new1



