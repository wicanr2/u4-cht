; U4-SMS 主題 graphics 覆寫(草稿 / 受阻)
;
; 現況:SMS ROM(materals/_extracted/genesis/u4.sms)圖形為 VDP 8×8 4bpp planar,
; 但 0x40000–0x44000 是「已組好的全螢幕場景/標題 bitmap」,非 xu4 期望的 256-tile bank。
; raw ROM 順序切不出 256-tile 邏輯序(SMS 走 name-table + pattern bank,需 VRAM dump 才能對映)。
; 故此檔暫無法提供 fmt_tileset.png 等價物;待 emulator VRAM dump 後再補。
;
; 一旦取得對齊好的 16×4096 PNG(命名 sms_tileset.png),覆寫格式同 fmtowns/module/graphics.b:
;
; graphics: [
;     image (name: tiles filename: "sms_tileset.png" tiles: 256 fixup: blackTransparencyHack) [
;         at 0,0 size 16,16
;         ; ... 256-tile 標準序(同 fmtowns graphics.b)...
;     ]
; ]
