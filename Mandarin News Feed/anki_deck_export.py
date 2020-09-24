import random
import genanki
import csv
import traceback
import os

from kivymd.toast import toast

def export_deck(fpath, txt_file_name):
    try:
        # to import file name
        data_filename = txt_file_name

        # title
        anki_deck_title = "Mandarin News Feed"

        anki_model_name = "mandarin-news-feed"

        # exported deck name
        r2 = str(random.randrange(1 << 15, 1 << 16))
        deck_filename = anki_deck_title + "_export_" + r2 + ".apkg"
        deck_filename = os.path.join(fpath, deck_filename)
        model_id = random.randrange(1 << 30, 1 << 31)

        # front side
        front = """
<div class="text-color1">{{Pinyin}}</div>
<div class="text-color3">{{Meaning}}</div>
"""
        # card style
        style = """
.card {
    --pinyin-color: #27b46e;
    --simplified-color: #6495ed;
    --traditional-color: #fba910;
    --meaning-color: #29b6f6;

    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}

.card.night_mode{}

.text-color1 {
    font-size: 16px;
    color: var(--pinyin-color);
}

.text-color2 {
    color: var(--traditional-color);
}

.text-color3 {
    color: var(--meaning-color);
}

.text-color4 {
    font-size: 30px;
    font-weight: bold;
    color: var(--simplified-color);
}
"""

        # back side
        back = """
<div class="text-color4 ">{{Simplified}}</div>
<div class="text-color2">{{Traditional}}</div>
<div class="text-color1">{{Pinyin}}</div>
<div class="text-color3">{{Meaning}}</div>
"""
        # print(self.fields)
        anki_model = genanki.Model(
          model_id,
          anki_model_name,
          fields=[{"name": "Simplified"}, {"name": "Traditional"}, {"name": "Pinyin"}, {"name": "Meaning"}],
          templates=[
              {
                  "name": "Card 1",
                  "qfmt": front,
                  "afmt": back,
              },
          ],
          css=style,
        )

        anki_notes = []

        with open(data_filename, "r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter="\t")
            for row in csv_reader:
                flds = []
                for i in range(len(row)):
                    flds.append(row[i])

                anki_note = genanki.Note(
                    model=anki_model,
                    fields=flds,
                )
                anki_notes.append(anki_note)

        # random.shuffle(anki_notes)

        anki_deck = genanki.Deck(model_id, anki_deck_title)
        anki_package = genanki.Package(anki_deck)

        for anki_note in anki_notes:
            anki_deck.add_note(anki_note)

        anki_package.write_to_file(deck_filename)

        toast("Deck generated with {} flashcards. View Mandarin News Feed folder".format(
          len(anki_deck.notes)))

    except FileNotFoundError:
        toast("Add some words to {} then export deck".format(txt_file_name))

    except Exception:
        traceback.print_exc()