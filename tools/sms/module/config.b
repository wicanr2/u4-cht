module [
    about: {{
        Ultima IV — Sega Master System (1990, Europe) tileset 主題(草稿 / 受阻)。
        SMS VDP 8×8 4bpp planar 圖形;graphics.b 僅覆寫 tiles。
        現況:tileset 尚未對齊(見 graphics.b 註解),待 VRAM dump 後補。
    }}
    author: "u4-cht"
    version: "0.1-wip"
    rules: "Ultima-IV/1.4"
]

include %graphics.b

; SMS 版音樂為 PSG(SN76489),非 CD-DA;若日後抽出可在此補 music 對映。
