module [
    about: {{
        Ultima IV with FM Towns (1990, Japan) tileset + CD music.
        繁中化專案:FM Towns 美術主題 + CD-DA 音樂(本機,版權資產不入 repo)。
    }}
    author: "u4-cht"
    version: "1.0"
    rules: "Ultima-IV/1.4"
]

include %graphics.b

; FM Towns CD-DA 2 軌對映 9 個 music ID(world/dungeon/combat=main;town/castle/shrine=town)
music: [
    path %music
    %fmt_main.ogg   ; 1 world
    %fmt_town.ogg   ; 2 town
    %fmt_town.ogg   ; 3 shrine
    %fmt_town.ogg   ; 4 merchant
    %fmt_main.ogg   ; 5 rule britannia
    %fmt_main.ogg   ; 6 fanfare
    %fmt_main.ogg   ; 7 dungeon
    %fmt_main.ogg   ; 8 combat
    %fmt_town.ogg   ; 9 castle
]
