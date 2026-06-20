/* lr_dump.c — minimal headless libretro frontend.
 * 載入 genesis_plus_gx core,跑 ROM N 幀後 dump VRAM(16KB)+ CRAM(128B)。
 * 全 headless:不開視窗、不出聲;video/audio callback 收下即丟。
 * 用法: lr_dump <core.so> <rom.sms> <frames> <out_prefix>
 *   輸出 <out_prefix>.vram (0x10000 byte) 與 <out_prefix>.cram (0x80 byte)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <dlfcn.h>
#include "libretro.h"

static void *core;
#define SYM(n) dlsym(core, #n)

/* libretro callbacks — 全部最小實作 */
static void cb_video(const void *d, unsigned w, unsigned h, size_t p){ (void)d;(void)w;(void)h;(void)p; }
static void cb_audio_sample(int16_t l, int16_t r){ (void)l;(void)r; }
static size_t cb_audio_batch(const int16_t *d, size_t f){ (void)d; return f; }
/* g_btn = 這一幀要按住的 RETRO_DEVICE_ID_JOYPAD_* id(-1 表示全放開)。
 * 由主迴圈的輸入腳本逐幀設定。*/
static int g_btn = -1;
static void cb_input_poll(void){}
static int16_t cb_input_state(unsigned port, unsigned dev, unsigned idx, unsigned id){
    (void)idx;
    if(port!=0 || dev!=RETRO_DEVICE_JOYPAD) return 0;
    return ((int)id == g_btn) ? 1 : 0;
}
static bool cb_environ(unsigned cmd, void *data){
    switch(cmd){
        case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
            *(const char**)data = "/tmp"; return true;
        case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            return true; /* 接受任何像素格式 */
        case RETRO_ENVIRONMENT_GET_CAN_DUPE:
            *(bool*)data = true; return true;
        case RETRO_ENVIRONMENT_GET_VARIABLE:
            return false;
        case RETRO_ENVIRONMENT_SET_VARIABLES:
        case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
            return false;
        default:
            return false;
    }
}

int main(int argc, char **argv){
    if(argc < 5){ fprintf(stderr,"usage: %s core rom frames out_prefix\n",argv[0]); return 2; }
    const char *corepath=argv[1], *rompath=argv[2], *prefix=argv[4];
    long frames = atol(argv[3]);

    core = dlopen(corepath, RTLD_NOW);
    if(!core){ fprintf(stderr,"dlopen: %s\n", dlerror()); return 1; }

    void (*retro_init)(void) = SYM(retro_init);
    void (*retro_set_environment)(retro_environment_t) = SYM(retro_set_environment);
    void (*retro_set_video_refresh)(retro_video_refresh_t) = SYM(retro_set_video_refresh);
    void (*retro_set_audio_sample)(retro_audio_sample_t) = SYM(retro_set_audio_sample);
    void (*retro_set_audio_sample_batch)(retro_audio_sample_batch_t) = SYM(retro_set_audio_sample_batch);
    void (*retro_set_input_poll)(retro_input_poll_t) = SYM(retro_set_input_poll);
    void (*retro_set_input_state)(retro_input_state_t) = SYM(retro_set_input_state);
    bool (*retro_load_game)(const struct retro_game_info*) = SYM(retro_load_game);
    void (*retro_run)(void) = SYM(retro_run);
    void *(*retro_u4_get_vram)(void) = SYM(retro_u4_get_vram);
    void *(*retro_u4_get_cram)(void) = SYM(retro_u4_get_cram);
    size_t (*retro_serialize_size)(void) = SYM(retro_serialize_size);
    bool (*retro_serialize)(void*,size_t) = SYM(retro_serialize);
    bool (*retro_unserialize)(const void*,size_t) = SYM(retro_unserialize);

    if(!retro_init||!retro_load_game||!retro_run||!retro_u4_get_vram){
        fprintf(stderr,"missing core symbols\n"); return 1;
    }

    retro_set_environment(cb_environ);
    retro_set_video_refresh(cb_video);
    retro_set_audio_sample(cb_audio_sample);
    retro_set_audio_sample_batch(cb_audio_batch);
    retro_set_input_poll(cb_input_poll);
    retro_set_input_state(cb_input_state);
    retro_init();

    /* 讀 ROM 進記憶體 */
    FILE *f = fopen(rompath,"rb");
    if(!f){ perror("rom"); return 1; }
    fseek(f,0,SEEK_END); long sz=ftell(f); fseek(f,0,SEEK_SET);
    void *rom = malloc(sz);
    if(fread(rom,1,sz,f)!=(size_t)sz){ fprintf(stderr,"rom read short\n"); return 1; }
    fclose(f);

    struct retro_game_info gi; memset(&gi,0,sizeof(gi));
    gi.path = rompath; gi.data = rom; gi.size = sz;
    if(!retro_load_game(&gi)){ fprintf(stderr,"load_game failed\n"); return 1; }

    /* U4_LOADSTATE=<file>:載入先前存的 savestate,從該點續跑(分段導航)。 */
    const char *lsf = getenv("U4_LOADSTATE");
    if(lsf && retro_unserialize){
        FILE *sf=fopen(lsf,"rb");
        if(sf){ fseek(sf,0,SEEK_END); long ss=ftell(sf); fseek(sf,0,SEEK_SET);
            void *sd=malloc(ss); if(fread(sd,1,ss,sf)==(size_t)ss){
                if(retro_unserialize(sd,ss)) fprintf(stderr,"loaded state %s (%ld B)\n",lsf,ss);
                else fprintf(stderr,"unserialize failed\n"); }
            free(sd); fclose(sf); }
    }

    /* 輸入腳本:可由 env U4_BTN 指定固定要脈衝的 button id(預設 START=3)。
     * 每 40 幀按 8 幀放 32 幀(產生 edge);前 60 幀放開過 logo。
     * 每 600 幀 dump 快照,事後挑含地形 tile 的畫面。
     * RETRO JOYPAD id: B=0 Y=1 SELECT=2 START=3 UP=4 DOWN=5 LEFT=6 RIGHT=7 A=8 X=9 L=10 R=11 */
    const char *be = getenv("U4_BTN");
    int btn = be ? atoi(be) : RETRO_DEVICE_ID_JOYPAD_START;
    /* U4_SEQ=1:離散按鍵(每 120 幀按 4 幀),適合 menu 需要單次 edge 的情況。*/
    int seq = getenv("U4_SEQ") ? 1 : 0;
    /* U4_BTN2:在 U4_SW 幀之後改按這個 button(階段切換,例:先 START 進完整 title,再 A 進遊戲)。*/
    int btn2 = getenv("U4_BTN2") ? atoi(getenv("U4_BTN2")) : -999;
    long swf = getenv("U4_SW") ? atol(getenv("U4_SW")) : 1<<30;
    /* U4_SCRIPT="f0:b0,f1:b1,...":到 fN 幀起改按 bN(離散 edge:每 60 幀按 6 放 54)。
     * 比 2-phase 更彈性,可逐段導航 menu(命名→END→性別→問答→世界)。b=-1 放開。 */
    long scf[64]; int scb[64], scn=0;
    const char *sc = getenv("U4_SCRIPT");
    if(sc){ char buf[1024]; strncpy(buf,sc,sizeof(buf)-1); buf[sizeof(buf)-1]=0;
        char *p=strtok(buf,","); while(p && scn<64){ long f; int b;
            if(sscanf(p,"%ld:%d",&f,&b)==2){ scf[scn]=f; scb[scn]=b; scn++; } p=strtok(NULL,","); } }
    for(long i=0;i<frames;i++){
        long period = seq ? 120 : 40;
        long ph = i % period;
        int curbtn = (i >= swf && btn2 != -999) ? btn2 : btn;
        if(scn){ int cb=-1; for(int k=0;k<scn;k++) if(i>=scf[k]) cb=scb[k];
            long sph=i%60; g_btn=(cb!=-1 && sph<6)?cb:-1; }
        else g_btn = (i > 60 && ph < 4) ? curbtn : -1;
        retro_run();
        if(i>0 && i%600==0){
            unsigned char *v=retro_u4_get_vram(), *c=retro_u4_get_cram();
            char pp[512]; FILE *q;
            snprintf(pp,sizeof(pp),"%s_f%ld.vram",prefix,i); q=fopen(pp,"wb"); fwrite(v,1,0x10000,q); fclose(q);
            snprintf(pp,sizeof(pp),"%s_f%ld.cram",prefix,i); q=fopen(pp,"wb"); fwrite(c,1,0x80,q); fclose(q);
            fprintf(stderr,"snapshot f%ld\n",i);
        }
    }
    g_btn = -1;

    /* U4_SAVESTATE=<file>:跑完後存 savestate,供下一段 U4_LOADSTATE 續跑。 */
    const char *ssf = getenv("U4_SAVESTATE");
    if(ssf && retro_serialize && retro_serialize_size){
        size_t ss=retro_serialize_size(); void *sd=malloc(ss);
        if(retro_serialize(sd,ss)){ FILE *sf=fopen(ssf,"wb"); fwrite(sd,1,ss,sf); fclose(sf);
            fprintf(stderr,"saved state %s (%zu B)\n",ssf,ss); }
        else fprintf(stderr,"serialize failed\n");
        free(sd);
    }

    /* dump VRAM + CRAM */
    unsigned char *vram = retro_u4_get_vram();
    unsigned char *cram = retro_u4_get_cram();
    char path[512];

    snprintf(path,sizeof(path),"%s.vram",prefix);
    FILE *fv=fopen(path,"wb"); fwrite(vram,1,0x10000,fv); fclose(fv);
    snprintf(path,sizeof(path),"%s.cram",prefix);
    FILE *fc=fopen(path,"wb"); fwrite(cram,1,0x80,fc); fclose(fc);

    fprintf(stderr,"dumped %ld frames: %s.vram(64K) %s.cram(128B)\n",frames,prefix,prefix);
    return 0;
}
