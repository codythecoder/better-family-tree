import src.draw_tree as draw_tree
from src.family_tree import Person, Sex, Relation, Family, Tree
import csv

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
assert family.head is not None
print(family.head)


draw_tree.drawTree(family)

